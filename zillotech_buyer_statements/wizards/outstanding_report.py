from odoo import http
import os
import xlsxwriter
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
import collections
import base64
from odoo.http import request, content_disposition

try:
    import xlwt
except ImportError:
    xlwt = None


class OutstandingReportExcelPDF(models.TransientModel):
    _name = 'buyer.outstanding.report.wizard'
    _description = "Buyer Outstanding Report Wizard"

    @api.onchange('last_date')
    def _onchange_last_date(self):
        if self.first_date and self.last_date and self.first_date > self.last_date:
            raise UserError(_('Invalid Action!', 'Start date cannot be greater than last date.'))

    journal_id = fields.Many2one('account.journal', domain=[('type', '=', 'sale')])
    first_date = fields.Date(string='Start Date', required=True)
    last_date = fields.Date(string='End Date', required=True)
    excel_file = fields.Binary('Excel Report for outstanding invoice', readonly=True)
    file_name = fields.Char('Excel File', size=64)
    excel_file_bool = fields.Boolean('Excel File Bool', default=False)

    attachment_id = fields.Many2one('ir.attachment', string='Attachment')

    def action_outstanding_report_print_excel_pdf(self):
        if self.journal_id:
            all_journal_list = [dict(id=journal.id, name=journal.name) for journal in self.journal_id]
        else:
            all_journal_list = [dict(id=journal.id, name=journal.name) for journal in
                                self.env['account.journal'].search(
                                    [('type', 'in', ['sale'])])]
        due_month_list = []
        last_group_data = {}
        l_dict_list = []
        d_month_dict = {}
        l_custom_month_data = []
        l_month_list = []

        for journal_id in all_journal_list:
            self._cr.execute(
                'select distinct partner_id from account_move where (journal_id=%s) and invoice_date_due between (%s) and (%s)',
                (journal_id['id'], self.first_date, self.last_date))
            all_partner_records = self._cr.dictfetchall()
            d_data_final = {}
            for partner in all_partner_records:
                self._cr.execute(
                    "select * from account_move where (journal_id=%s) and "
                    "partner_id = (%s) and invoice_date_due between (%s) and (%s) and  state != 'paid' order by "
                    "invoice_date_due ASC",
                    (journal_id['id'], partner['partner_id'], self.first_date, self.last_date,))
                all_invoice_records = self._cr.dictfetchall()
                for invoice in all_invoice_records:
                    l_month_list.append(invoice['invoice_date_due'])
                    inv_due_month = str(
                        datetime.strptime(str(invoice['invoice_date_due']), '%Y-%m-%d').strftime("%B")) + str(
                        datetime.strptime(str(invoice['invoice_date_due']), '%Y-%m-%d').year)
                    due_month_list.append(inv_due_month)
                    d_month_dict.update(
                        {inv_due_month: datetime.strptime(str(invoice['invoice_date_due']), '%Y-%m-%d').month})
                    if invoice['amount_residual'] == 0.0:
                        price_total = ''
                    else:
                        price_total = invoice['amount_residual']
                    dict_data = dict(invoice_number=invoice['name'], invoice_date_due=invoice['invoice_date_due'],
                                     total=price_total, journal_id=invoice['journal_id'],
                                     invoice_date=invoice['invoice_date'])
                    dict_data[inv_due_month] = price_total
                    l_dict_list.append(dict_data)
                sorted_dict = sorted(l_dict_list, key=lambda k: k['invoice_date_due'])
                if sorted_dict:
                    d_data_final.update({partner['partner_id']: sorted_dict})
                l_dict_list = []
                if d_data_final:
                    last_group_data.update({journal_id['id']: d_data_final})

        if l_month_list:
            for rec in (sorted(d_month_dict.items(), key=lambda kv: (kv[1], kv[0]))):
                l_custom_month_data.append(rec[0])
            due_month_list = l_custom_month_data
            last_group_data = collections.OrderedDict(sorted(last_group_data.items()))
            list_months_total_dict = []
            all_data = collections.OrderedDict(sorted(d_month_dict.items()))
            for key1, data1 in last_group_data.items():
                dict_of_month_total = {}
                for key, value in all_data.items():
                    self._cr.execute(
                        "select sum(amount_residual),invoice_date_due  from account_move where Extract(month from "
                        "invoice_date_due)=(%s) and journal_id=(%s) group by invoice_date_due",
                        (value, key1))
                    record = self._cr.dictfetchall()
                    total = 0
                    for rec in record:
                        total += rec.get('sum')
                    dict_of_month_total.update({key: total})
                list_months_total_dict.append({key1: dict_of_month_total})
        else:
            list_months_total_dict = None
            last_group_data = None
            l_custom_month_data = None
        if self._context.get('type') == 'pdf':
            report = self._outstanding_pdf_report(list_months_total_dict, last_group_data, l_custom_month_data)
            return report
        else:
            attachment_id = self._outstanding_excel_report(due_month_list, last_group_data, list_months_total_dict)
            self.attachment_id = attachment_id
            return {'type': 'ir.actions.act_url',
                    'url': '/web/binary/outstanding_report?rec_id=%s' % self.id,
                    'target': 'self',
                    'res_id': self.id,
                    }

    def _outstanding_pdf_report(self, list_months_total_dict, dict_all_data, list_l_custom_month_data):
        data = {'list_months_total_dict': list_months_total_dict,
                'dict_all_data': dict_all_data,
                'due_month_list': list_l_custom_month_data,
                'journal_name': self.journal_id.name}
        datas = {
            'ids': self._ids,
            'model': 'account.move',
            'form': data,
        }
        return self.env.ref('zillotech_buyer_statements.action_print_pdf_outstanding_report').report_action(self,
                                                                                                      data=datas)

    def _outstanding_excel_report(self, due_month_list, dict_all_data, list_months_total_dict):
        destination_folder = os.path.dirname(__file__) + "/odoo_xlsx"
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)
        file_name = 'Outstanding Report of Invoices.xlsx'
        file_content_name = os.path.join(destination_folder, file_name)
        workbook = xlsxwriter.Workbook(file_content_name)
        txt = workbook.add_format({'font_size': '10px', 'border': 1})
        sub_heading_sub = workbook.add_format({'align': 'center', 'bold': True,
                                               'border': 1
                                               }
                                              )

        row = 0
        worksheet = workbook.add_worksheet('Sheet 1')
        for index in range(5):
            worksheet.set_column(0, index, 20)
        worksheet.write(row, 1, 'Invoice Date', sub_heading_sub)
        col = 2
        for months_cols in due_month_list:
            worksheet.write(row, col, months_cols, sub_heading_sub)
            col += 1
        worksheet.write(row, col, 'Total', sub_heading_sub)
        worksheet.write(row, col + 1, 'Due Date', sub_heading_sub)
        if dict_all_data:
            for journal_id, values in dict_all_data.items():
                worksheet.write(row, 0, self.env['account.journal'].browse(journal_id).name, sub_heading_sub)
                for partner_id, vals in values.items():
                    if vals:
                        worksheet.write(row + 1, 0, self.env['res.partner'].browse(partner_id).name)
                        row = row + 1
                    for val in vals:
                        row = row + 1
                        worksheet.write(row, 0, val['invoice_number'], txt)
                        worksheet.write(row, 1, str(val['invoice_date']), txt)
                        col = 2
                        for month in due_month_list:
                            if val.get(month) is not None:
                                worksheet.write(row, col, val[month], txt)
                            else:
                                worksheet.write(row, col, '')
                            col = col + 1
                        worksheet.write(row, col, val['total'], txt)
                        worksheet.write(row, col + 1, 'DUE DATE - ' + str(val['invoice_date_due']), txt)
                        row = row + 0
                row = row + 1
                col = 2
                for values in list_months_total_dict:
                    for key, value in values.items():
                        if key == journal_id:
                            for months in due_month_list:
                                if value.get(months) is not None:
                                    if value.get(months) != '':
                                        worksheet.write(row, col, value.get(months), sub_heading_sub)
                                        col = col + 1
        workbook.close()
        files = base64.b64encode(open(file_content_name, 'rb').read())
        attachment_id = self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',
            'datas': files,
        })
        os.remove(file_content_name)
        return attachment_id


class BinaryZipReport(http.Controller):
    @http.route('/web/binary/outstanding_report', type='http', auth="public")
    def download_function_outstanding_report(self, **kwargs):
        rec_id = int(kwargs.get('rec_id'))
        data = request.env['buyer.outstanding.report.wizard'].browse(rec_id)
        if data.attachment_id:
            file_content = base64.b64decode(data.attachment_id.datas)
            file_name = data.attachment_id.name if data.attachment_id.name else 'outstanding_report.xlsx'
            unlink_attachments = [(2, line.id) for line in data.attachment_id]
            data.write({'attachment_id': unlink_attachments})
            if not file_content:
                return request.not_found()
            else:
                if file_name:
                    return request.make_response(file_content,
                                                 [('Content-Type', 'application/octet-stream'),
                                                  ('Content-Disposition', content_disposition(file_name))])
