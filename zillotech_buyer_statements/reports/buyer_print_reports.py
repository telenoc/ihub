from odoo import models, api, fields


class BuyerStatementReport(models.AbstractModel):
    _name = 'report.zillotech_buyer_statements.report_buyer_statements'
    _description = "Buyer Statement Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        if not docids:
            active_id = self.env.context.get('active_id')
            partner = self.env['res.partner'].browse(active_id)
        else:
            active_id = docids[0]
            partner = self.env['res.partner'].browse(active_id)
        content_dict = {}
        total_credit_amount = total_balance_amount = total_amount_signed = 0.0
        for line in [x for x in partner.buyer_balance_ids.sorted(lambda x: x.name)]:
            total_balance_amount += line.balance_due_amount
            total_credit_amount += line.credit_payment
            total_amount_signed += line.amount_total_signed
        content_dict['total_balance_amount'] = round(total_balance_amount, 2)
        content_dict['total_credit_amount'] = round(total_credit_amount, 2)
        content_dict['total_amount_signed'] = round(total_amount_signed, 2)
        content_dict['field_datas'] = [x for x in partner.buyer_balance_ids.sorted(lambda x: x.name)]
        data['content_dict'] = content_dict
        return {
            'doc_ids': docids,
            'data': data,
            'partner': partner,
            'content_dict': data['content_dict']
        }


class BuyerFilterStatementReport(models.AbstractModel):
    _name = 'report.zillotech_buyer_statements.report_buyer_fil_statements'
    _description = "Buyer Filter Statement Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        if not docids:
            active_id = self.env.context.get('active_id')
            partner = self.env['res.partner'].browse(active_id)
        else:
            active_id = docids[0]
            partner = self.env['res.partner'].browse(active_id)
        content_dict = {}
        total_credit_amount = total_balance_amount = total_amount_signed = 0.0
        for line in [x for x in partner.buyer_filter_line_ids.sorted(lambda x: x.reference)]:
            total_balance_amount += line.balance_due_amount
            total_credit_amount += line.credit_payment
            total_amount_signed += line.amount_total_signed
        content_dict['total_balance_amount'] = round(total_balance_amount, 2)
        content_dict['total_credit_amount'] = round(total_credit_amount, 2)
        content_dict['total_amount_signed'] = round(total_amount_signed, 2)
        content_dict['field_datas'] = [x for x in partner.buyer_filter_line_ids.sorted(lambda x: x.reference)]
        data['content_dict'] = content_dict
        return {
            'doc_ids': docids,
            'data': data,
            'partner': partner,
            'content_dict': data['content_dict']
        }


class BuyerOverdueStatementReport(models.AbstractModel):
    _name = 'report.zillotech_buyer_statements.report_buyer_o_statements'
    _description = "Buyer Overdue Statement Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        if not docids:
            active_id = self.env.context.get('active_id')
            partner = self.env['res.partner'].browse(active_id)
        else:
            active_id = docids[0]
            partner = self.env['res.partner'].browse(active_id)
        content_dict = {}
        date_today = fields.Date.today()
        total_credit_amount = total_balance_amount = total_amount_signed = 0.0
        for line in [x for x in partner.buyer_balance_ids if x.invoice_date_due]:
            if line and line.invoice_date_due < date_today:
                if line.payment_state != 'paid':
                    total_balance_amount += line.balance_due_amount
                    total_credit_amount += line.credit_payment
                    total_amount_signed += line.amount_total_signed
        content_dict['total_balance_amount'] = round(total_balance_amount, 2)
        content_dict['total_paid_amount'] = round(total_credit_amount, 2)
        content_dict['total_amount_due'] = round(total_amount_signed, 2)
        content_dict['field_datas'] = [y for y in [x for x in partner.buyer_balance_ids if
                                                   x.payment_state != 'paid' and x.invoice_date_due] if
                                       y.invoice_date_due < date_today]
        data['content_dict'] = content_dict
        return {
            'doc_ids': docids,
            'data': data,
            'partner': partner,
            'content_dict': data['content_dict']
        }


class SupplierCommonReport(models.AbstractModel):
    _name = 'report.zillotech_buyer_statements.report_sup_fil_statements'
    _description = "Supplier Common Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        partner = self.env['res.partner'].browse(data['context']['active_id'])
        if data['supplier_statement']:
            content_dict = {}
            total_credit_amount = total_balance_amount = total_amount_signed = 0.0
            for line in [x for x in partner.supplier_balance_ids.sorted(lambda x: x.name)]:
                total_balance_amount += line.balance_due_amount
                total_credit_amount += line.credit_payment
                total_amount_signed += line.amount_total_signed
            content_dict['total_balance_amount'] = round(total_balance_amount, 2)
            content_dict['total_credit_amount'] = round(total_credit_amount, 2)
            content_dict['total_amount_signed'] = round(total_amount_signed, 2)
            content_dict['field_datas'] = [x for x in partner.supplier_balance_ids.sorted(lambda x: x.name)]
            data['content_dict'] = content_dict
            return {
                'doc_ids': docids,
                'data': data,
                'partner': partner,
                'content_dict': data['content_dict']
            }

        if data['filter_supplier_statement']:
            content_dict = {}
            total_credit_amount = total_balance_amount = total_amount_signed = 0.0
            for line in [x for x in partner.supplier_filter_line_ids.sorted(lambda x: x.reference)]:
                total_balance_amount += line.balance_due_amount
                total_credit_amount += line.credit_payment
                total_amount_signed += line.amount_total_signed
            content_dict['total_balance_amount'] = round(total_balance_amount, 2)
            content_dict['total_credit_amount'] = round(total_credit_amount, 2)
            content_dict['total_amount_signed'] = round(total_amount_signed, 2)
            content_dict['field_datas'] = [x for x in partner.supplier_filter_line_ids.sorted(lambda x: x.reference)]
            data['content_dict'] = content_dict
            return {
                'doc_ids': docids,
                'data': data,
                'partner': partner,
                'content_dict': data['content_dict']
            }


class BuyerMonthlyReport(models.AbstractModel):
    _name = 'report.zillotech_buyer_statements.report_buyer_m_statements'
    _description = "Buyer Monthly Report"

    @api.model
    def _get_report_values(self, doc_ids, data=None):
        if not doc_ids:
            active_id = self.env.context.get('active_id')
            partner = self.env['res.partner'].browse(active_id)
        else:
            active_id = doc_ids[0]
            partner = self.env['res.partner'].browse(active_id)
        content_dict = {}
        total_credit_amount = total_balance_amount = total_amount_signed = 0.0
        for line in [x for x in partner.buyer_monthly_statement_ids.sorted(lambda x: x.m_reference)]:
            total_balance_amount += line.m_balance_due_amount
            total_credit_amount += line.m_credit_payment
            total_amount_signed += line.m_amount_total_signed
        content_dict['total_balance_amount'] = round(total_balance_amount, 2)
        content_dict['total_credit_amount'] = round(total_credit_amount, 2)
        content_dict['total_amount_signed'] = round(total_amount_signed, 2)
        content_dict['field_datas'] = [x for x in partner.buyer_monthly_statement_ids.sorted(lambda x: x.m_reference)]
        return {
            'doc_ids': doc_ids,
            'partner': partner,
            'content_dict': content_dict
        }


class BuyerWeeklyReport(models.AbstractModel):
    _name = 'report.zillotech_buyer_statements.report_buyer_w_statements'
    _description = "Buyer Weekly Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        if not docids:
            active_id = self.env.context.get('active_id')
            partner = self.env['res.partner'].browse(active_id)
        else:
            active_id = docids[0]
            partner = self.env['res.partner'].browse(active_id)
        content_dict = {}
        total_credit_amount = total_balance_amount = total_amount_signed = 0.0
        for line in [x for x in partner.buyer_weekly_statement_ids.sorted(lambda x: x.w_reference)]:
            total_balance_amount += line.w_balance_due_amount
            total_credit_amount += line.w_credit_payment
            total_amount_signed += line.w_amount_total_signed
        content_dict['total_balance_amount'] = round(total_balance_amount, 2)
        content_dict['total_credit_amount'] = round(total_credit_amount, 2)
        content_dict['total_amount_signed'] = round(total_amount_signed, 2)
        content_dict['field_datas'] = [x for x in partner.buyer_weekly_statement_ids.sorted(lambda x: x.w_reference)]
        return {
            'doc_ids': docids,
            'partner': partner,
            'content_dict': content_dict
        }


class BuyerCustomReport(models.AbstractModel):
    _name = 'report.zillotech_buyer_statements.report_buyer_c_statements'
    _description = "Buyer Custom Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        if not docids:
            active_id = self.env.context.get('active_id')
            partner = self.env['res.partner'].browse(active_id)
        else:
            active_id = docids[0]
            partner = self.env['res.partner'].browse(active_id)
        content_dict = {}
        total_credit_amount = total_balance_amount = total_amount_signed = total_grand_total = 0.0
        for line in [x for x in partner.custom_statement_line_ids.sorted(lambda x: x.c_reference)]:
            total_balance_amount += line.c_balance_due_amount
            total_credit_amount += line.c_credit_payment
            total_amount_signed += line.c_amount_total_signed
            total_grand_total += line.c_amount_total_signed - line.c_credit_payment
        content_dict['total_balance_amount'] = round(total_balance_amount, 2)
        content_dict['total_credit_amount'] = round(total_credit_amount, 2)
        content_dict['total_amount_signed'] = round(total_amount_signed, 2)
        content_dict['total_grand_total'] = round(total_grand_total, 2)
        content_dict['field_datas'] = [x for x in partner.custom_statement_line_ids.sorted(lambda x: x.c_reference)]
        return {
            'doc_ids': docids,
            'partner': partner,
            'content_dict': content_dict
        }
