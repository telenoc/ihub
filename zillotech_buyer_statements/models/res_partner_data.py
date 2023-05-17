from datetime import date, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError

try:
    import qrcode
except ImportError:
    qrcode = None
try:
    import base64
except ImportError:
    base64 = None
from io import BytesIO


class ResBuyerSellerData(models.Model):
    _inherit = 'res.partner'

    def _compute_buyer_balance_and_overdue_amount(self):
        current_date = fields.Date.today()
        for customer in self:
            customer.action_print_buyer_statement_monthly()
            customer.action_print_buyer_statement_weekly()
            customer._compute_monthly_weekly_statement()
            balance_due = balance_overdue = 0.0

            # Buyer Total
            for move in [line for line in customer.buyer_balance_ids if line.company_id == customer.env.company]:
                date_maturity = move.invoice_date_due or move.date
                balance_due += move.balance_due_amount
                if date_maturity and date_maturity <= current_date:
                    balance_overdue += move.balance_due_amount
            customer.buyer_amount_due_payment = balance_due
            customer.buyer_amount_overdue_payment = balance_overdue

    def _compute_supplier_balance_and_overdue_amount(self):
        current_date = fields.Date.today()
        for customer in self:
            balance_due = balance_overdue = filtered_balance_due = filtered_balance_overdue = 0.0

            # Supplier Total
            for move in [line for line in customer.supplier_balance_ids if line.company_id == customer.env.company]:
                date_maturity = move.invoice_date_due or move.date
                balance_due += move.balance_due_amount
                if date_maturity and date_maturity <= current_date:
                    balance_overdue += move.balance_due_amount
            customer.supplier_amount_due_payment = balance_due
            customer.supplier_amount_overdue_payment = balance_overdue

            # Supplier filtered Total
            if customer.supplier_filter_line_ids:
                for move in [x for x in customer.supplier_filter_line_ids if x.due_invoice_date]:
                    date_maturity = move.due_invoice_date
                    filtered_balance_due += move.balance_due_amount
                    if date_maturity and date_maturity <= current_date:
                        filtered_balance_overdue += move.balance_due_amount
                customer.supplier_amount_due_payment_filtered = filtered_balance_due
                customer.supplier_amount_overdue_payment_filtered = filtered_balance_overdue

    def action_get_buyer_filtered_statements(self):
        for partner_record in self:
            # initial balance
            if partner_record.buyer_statement_date_from:
                buyer_initial_balance = 0.0
                for move in [x for x in self.env['account.move'].search([('partner_id', '=', partner_record.id),
                                                                         ('move_type', 'in',
                                                                          ['out_invoice', 'out_refund']),
                                                                         ('state', 'in', ['posted']),
                                                                         ('payment_state', 'not in', ['paid']),
                                                                         ('invoice_date', '<',
                                                                          partner_record.buyer_statement_date_from), (
                                                                                 'date', '<',
                                                                                 partner_record.buyer_statement_date_from)])]:
                    buyer_initial_balance += move.amount_residual

                for payment in [y for y in self.env['account.payment'].search([('partner_id', '=', partner_record.id), \
                                                                               (
                                                                                       'state', 'in',
                                                                                       ['posted', 'reconciled']),
                                                                               ('date', '<',
                                                                                partner_record.buyer_statement_date_from), \
                                                                               ('partner_type', '=', 'customer')])]:
                    buyer_initial_balance -= payment.amount
                if buyer_initial_balance:
                    partner_record.write({'buyer_initial_balance': buyer_initial_balance})
            history_lines = self.env['filter.data.line'].search([('partner_id', '=', partner_record.id)])
            if history_lines:
                history_lines.unlink()
            partner_record._invoice_data(partner_record, buyer=True, vendor=False)
            # partner_record._entry_data(partner_record, buyer=True, vendor=False)
        view = self.env.ref('zillotech_buyer_statements.view_filter_buyer_statements')
        return {
            'name': _('Customer Filter Statement View'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'res.partner',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
        }

    def action_get_supplier_filtered_statements(self):
        for partner_record in self:
            if partner_record.supplier_statement_date_from:
                supplier_initial_balance = 0.0
                for move in [x for x in self.env['account.move'].search([('partner_id', '=', partner_record.id), \
                                                                         ('move_type', 'in',
                                                                          ['in_invoice', 'in_refund']),
                                                                         ('state', 'in', ['posted']), \
                                                                         ('invoice_date', '<',
                                                                          partner_record.supplier_statement_date_from),
                                                                         (
                                                                                 'date', '<',
                                                                                 partner_record.supplier_statement_date_from),
                                                                         ('payment_state', 'not in', ['paid'])])]:
                    supplier_initial_balance += move.amount_residual

                for payment in [y for y in self.env['account.payment'].search([('partner_id', '=', partner_record.id), \
                                                                               (
                                                                                       'state', 'in',
                                                                                       ['posted', 'reconciled']),
                                                                               ('date', '<',
                                                                                partner_record.supplier_statement_date_from), \
                                                                               ('partner_type', '=', 'supplier')])]:
                    supplier_initial_balance -= payment.amount
                if supplier_initial_balance:
                    partner_record.write({'supplier_initial_balance': -supplier_initial_balance})
            history_lines = self.env['filter.supplier.data.line'].search([('partner_id', '=', partner_record.id)])
            if history_lines:
                history_lines.unlink()
            partner_record._invoice_data(partner_record, buyer=False, vendor=True)
            # partner_record._entry_data(partner_record, buyer=False, vendor=True)
        view = self.env.ref('zillotech_buyer_statements.view_filter_supplier_statements')
        return {
            'name': _('Supplier Filter Statement View'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'res.partner',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
        }

    def _invoice_data(self, partner_record, buyer=False, vendor=False):
        if buyer:
            domain = [('move_type', 'in', ['out_invoice', 'out_refund']), ('state', 'in', ['posted']),
                      ('partner_id', '=', partner_record.id),
                      ('payment_state', 'not in', ['paid']),
                      ('invoice_date', '>=',
                       partner_record.buyer_statement_date_from) if partner_record.buyer_statement_date_from else None,
                      ('invoice_date', '<=',
                       partner_record.buyer_statement_date_to) if partner_record.buyer_statement_date_to else None]
        elif vendor:
            domain = [('move_type', 'in', ['in_invoice', 'in_refund']), ('state', 'in', ['posted']),
                      ('payment_state', 'not in', ['paid']),
                      ('partner_id', '=', partner_record.id), ('invoice_date', '>=',
                                                               partner_record.supplier_statement_date_from) if partner_record.supplier_statement_date_from else None,
                      ('invoice_date', '<=',
                       partner_record.supplier_statement_date_to) if partner_record.supplier_statement_date_to else None]
        else:
            domain = None
        invoices = self.env['account.move'].search(domain)
        if invoices:
            invoice_list = [dict(partner_id=invoice.partner_id.id or False, invoice_date=invoice.invoice_date or None,
                                 due_invoice_date=invoice.invoice_date_due or None,
                                 state=invoice.state or False,
                                 payment_state=invoice.payment_state or False,
                                 reference=invoice.name or '',
                                 credit_payment=invoice.credit_payment or 0.0,
                                 balance_due_amount=invoice.balance_due_amount or 0.0,
                                 amount_total=invoice.amount_total or 0.0,
                                 transaction_ids=invoice.transaction_ids.ids or [],
                                 move_type=invoice.move_type or False,
                                 invoice_id=invoice.id) for
                            invoice in
                            invoices.sorted(key=lambda x: x.name) if invoice.balance_due_amount > 0]
            if buyer:
                for list_data in invoice_list:
                    self.env['filter.data.line'].create(list_data)
            if vendor:
                for list_data in invoice_list:
                    self.env['filter.supplier.data.line'].create(list_data)

    # def _entry_data(self, partner_record, buyer=False, vendor=False):
    #     if buyer:
    #         domain_entry = [('move_type', 'in', ['entry']), ('state', 'in', ['posted']),
    #                         ('partner_id', '=', partner_record.id), ('date', '>=',
    #                                                                  partner_record.buyer_statement_date_from) if partner_record.buyer_statement_date_from else None,
    #                         ('date', '<=',
    #                          partner_record.buyer_statement_date_to) if partner_record.buyer_statement_date_to else None]
    #     elif vendor:
    #         domain_entry = [('move_type', 'in', ['entry']), ('state', 'in', ['posted']),
    #                         ('partner_id', '=', partner_record.id), ('date', '>=',
    #                                                                  partner_record.supplier_statement_date_from) if partner_record.supplier_statement_date_from else None,
    #                         ('date', '<=',
    #                          partner_record.supplier_statement_date_to) if partner_record.supplier_statement_date_to else None]
    #
    #     else:
    #         domain_entry = None
    #
    #     invoices = self.env['account.move'].search(domain_entry)
    #     if invoices:
    #         invoice_list = [dict(partner_id=invoice.partner_id.id or False, invoice_date=invoice.invoice_date or None,
    #                              due_invoice_date=invoice.invoice_date_due or None,
    #                              reference=invoice.name or '',
    #                              credit_payment=invoice.credit_payment or 0.0,
    #                              balance_due_amount=invoice.balance_due_amount or 0.0,
    #                              amount_total=invoice.amount_total or 0.0,
    #                              transaction_ids=invoice.transaction_ids.ids or [],
    #                              payment_state=invoice.payment_state or False,
    #                              move_type=invoice.move_type or False,
    #                              invoice_id=invoice.id) for
    #                         invoice in
    #                         invoices.sorted(key=lambda x: x.name) if invoice.balance_due_amount > 0]
    #         if buyer:
    #             for list_data in invoice_list:
    #                 self.env['filter.data.line'].create(list_data)
    #         if vendor:
    #             for list_data in invoice_list:
    #                 self.env['filter.supplier.data.line'].create(list_data)

    def action_print_buyer_statement(self):
        self.ensure_one()
        report = self.env.ref('zillotech_buyer_statements.action_report_buyer_statements').report_action(self, data={
            'partner_id': self})
        print("report------------------",report)
        if report.get('report_name'):
            base_url = self.get_base_url()
            self.update(
                {'qr_code_url': base_url + '/report/statements/page/%i' % self.id + '/' + '%s' % report.get('report_name')})
            self.report_name = report.get('report_name')
        else:
            raise UserError(_('Please set Document Layout First! Go to the General Settings.'))
        return report

    def action_show_monthly_statements(self):
        self.ensure_one()
        report = self.env.ref('zillotech_buyer_statements.action_report_buyer_monthly_statements').report_action(self, data={
            'partner_id': self})
        if report.get('report_name'):
            base_url = self.get_base_url()
            self.update(
                {'qr_code_url': base_url + '/report/statements/page/%i' % self.id + '/' + '%s' % report.get('report_name')})
            self.report_name = report.get('report_name')
        else:
            raise UserError(_('Please set Document Layout First! Go to the General Settings.'))
        return report

    def action_show_weekly_statements(self):
        self.ensure_one()
        report = self.env.ref('zillotech_buyer_statements.action_report_buyer_weekly_statements').report_action(self, data={
            'partner_id': self})
        if report.get('report_name'):
            base_url = self.get_base_url()
            self.update(
                {'qr_code_url': base_url + '/report/statements/page/%i' % self.id + '/' + '%s' % report.get('report_name')})
            self.report_name = report.get('report_name')
        else:
            raise UserError(_('Please set Document Layout First! Go to the General Settings.'))
        return report

    def action_print_filtered_buyer_statement(self):
        self.ensure_one()
        report = self.env.ref('zillotech_buyer_statements.action_report_buyer_filtered_statements').report_action(self, data={
            'partner_id': self})
        if report.get('report_name'):
            base_url = self.get_base_url()
            self.update(
                {'qr_code_url': base_url + '/report/statements/page/%i' % self.id + '/' + '%s' % report.get('report_name')})
            self.report_name = report.get('report_name')
        else:
            raise UserError(_('Please set Document Layout First! Go to the General Settings.'))
        return report

    def action_print_buyer_overdue_statement(self):
        self.ensure_one()
        report = self.env.ref('zillotech_buyer_statements.action_report_buyer_overdue_statements').report_action(self, data={
            'partner_id': self})
        if report.get('report_name'):
            base_url = self.get_base_url()
            self.update(
                {'qr_code_url': base_url + '/report/statements/page/%i' % self.id + '/' + '%s' % report.get('report_name')})
            self.report_name = report.get('report_name')
        else:
            raise UserError(_('Please set Document Layout First! Go to the General Settings.'))
        return report

    def action_print_supplier_statement(self):
        self.ensure_one()
        data = {'partner_id': self, 'supplier_statement': True, 'filter_supplier_statement': False}
        return self.env.ref('zillotech_buyer_statements.action_report_supplier_filtered_statements').report_action(self,
                                                                                                             data=data)

    def action_print_filtered_supplier_statement(self):
        self.ensure_one()
        data = {'partner_id': self, 'supplier_statement': False, 'filter_supplier_statement': True}
        return self.env.ref('zillotech_buyer_statements.action_report_supplier_filtered_statements').report_action(self,
                                                                                                             data=data)

    def action_sent_buyer_mail(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window',
                'name': _('Customer Email Wizard'),
                'res_model': 'partner.email.wizard',
                'target': 'new',
                'view_id': self.env.ref('zillotech_buyer_statements.partner_email_wizard_wizard_form').id,
                'view_mode': 'form',
                'context': {'default_customer_id': self.id,
                            'default_customer_bool': True,
                            'default_email': self.email}
                }

    def action_sent_buyer_overdue_mail(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window',
                'name': _('Customer Email Wizard'),
                'res_model': 'partner.email.wizard',
                'target': 'new',
                'view_id': self.env.ref('zillotech_buyer_statements.partner_email_wizard_wizard_form').id,
                'view_mode': 'form',
                'context': {'default_customer_id': self.id,
                            'default_overdue_bool': True,
                            'default_email': self.email}
                }

    def action_sent_filtered_buyer_statement(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window',
                'name': _('Customer Email Wizard'),
                'res_model': 'partner.email.wizard',
                'target': 'new',
                'view_id': self.env.ref('zillotech_buyer_statements.partner_email_wizard_wizard_form').id,
                'view_mode': 'form',
                'context': {'default_customer_id': self.id,
                            'default_filter_bool': True,
                            'default_email': self.email}
                }

    def action_connect_filter_statement_form(self):
        self.ensure_one()
        view = self.env.ref('zillotech_buyer_statements.view_filter_buyer_statements')
        return {
            'name': _('Customer Filter Statement View'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'res.partner',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
        }

    def action_connect_supplier_filter_statement_form(self):
        self.ensure_one()
        view = self.env.ref('zillotech_buyer_statements.view_filter_supplier_statements')
        return {
            'name': _('Supplier Filter Statement View'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'res.partner',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
        }

    @api.depends('supplier_filter_line_ids')
    def _compute_supplier_filter_balance_and_overdue_amount(self):
        current_date = fields.Date.today()
        for customer in self:
            filtered_balance_due = filtered_balance_overdue = 0.0
            # Supplier filtered Total
            for move in [x for x in customer.supplier_filter_line_ids if x.due_invoice_date]:
                date_maturity = move.due_invoice_date
                filtered_balance_due += move.balance_due_amount
                if date_maturity and date_maturity <= current_date:
                    filtered_balance_overdue += move.balance_due_amount
            customer.supplier_amount_due_payment_filtered = filtered_balance_due
            customer.supplier_amount_overdue_payment_filtered = filtered_balance_overdue

    @api.depends('buyer_filter_line_ids')
    def _compute_buyer_filter_balance_and_overdue_amount(self):
        current_date = fields.Date.today()
        for customer in self:
            filtered_balance_due = filtered_balance_overdue = 0.0
            # Supplier filtered Total
            for move in [x for x in customer.buyer_filter_line_ids if x.due_invoice_date]:
                date_maturity = move.due_invoice_date
                filtered_balance_due += move.balance_due_amount
                if date_maturity and date_maturity <= current_date:
                    filtered_balance_overdue += move.balance_due_amount
            customer.buyer_amount_due_payment_filtered = filtered_balance_due
            customer.buyer_amount_overdue_payment_filtered = filtered_balance_overdue

    # monthly / weekly functions

    def action_print_buyer_statement_monthly(self):
        self.ensure_one()
        self.monthly_statement_flag = True
        if self.monthly_statement_flag:
            end_date = date.today().replace(day=1) - timedelta(days=1)
            start_date = end_date.replace(day=1)
            self._common_calender_statement(start_date, end_date)

    def action_print_buyer_statement_weekly(self):
        self.ensure_one()
        self.weekly_statement_flag = True
        if self.weekly_statement_flag:
            today = date.today()
            start_date = today + timedelta(-today.weekday(), weeks=-1)
            end_date = today + timedelta(-today.weekday() - 1)
            self._common_calender_statement(start_date, end_date)

    def _common_calender_statement(self, start_date=None, end_date=None):
        monthly_move = self.env['buyer.monthly.statement']
        weekly_move = self.env['buyer.weekly.statement']

        for partner_record in self:
            domain_entry = [('move_type', 'in', ['out_invoice', 'out_refund']), ('state', 'in', ['posted']),
                            ('partner_id', '=', partner_record.id), ('invoice_date', '>=',
                                                                     str(start_date)),
                            ('payment_state', 'not in', ['paid']),
                            ('invoice_date', '<=',
                             str(end_date))]

            invoices = self.env['account.move'].search(domain_entry)
            if invoices:
                if self.monthly_statement_flag:
                    m_invoice_list = [
                        dict(m_partner_id=invoice.partner_id.id or False, m_invoice_date=invoice.invoice_date or None,
                             m_due_invoice_date=invoice.invoice_date_due or None,
                             m_reference=invoice.name or '',
                             m_credit_payment=invoice.credit_payment or 0.0,
                             m_balance_due_amount=invoice.balance_due_amount or 0.0,
                             m_amount_total=invoice.amount_total or 0.0,
                             payment_state=invoice.payment_state or False,
                             transaction_ids=invoice.transaction_ids.ids or [],
                             move_type=invoice.move_type or False,
                             m_invoice_id=invoice.id) for
                        invoice in
                        invoices.sorted(key=lambda x: x.name)]
                    history_lines = monthly_move.search(
                        [('m_partner_id', '=', partner_record.id)])
                    if history_lines:
                        history_lines.unlink()
                    for list_data in m_invoice_list:
                        if list_data:
                            monthly_move.create(list_data)
                    self.monthly_statement_flag = False
                    self.weekly_statement_flag = False

                if self.weekly_statement_flag:
                    w_invoice_list = [
                        dict(w_partner_id=invoice.partner_id.id or False, w_invoice_date=invoice.invoice_date or None,
                             w_due_invoice_date=invoice.invoice_date_due or None,
                             w_reference=invoice.name or '',
                             w_credit_payment=invoice.credit_payment or 0.0,
                             w_balance_due_amount=invoice.balance_due_amount or 0.0,
                             w_amount_total=invoice.amount_total or 0.0,
                             transaction_ids=invoice.transaction_ids.ids or [],
                             payment_state=invoice.payment_state or False,
                             move_type=invoice.move_type or False,
                             w_invoice_id=invoice.id) for
                        invoice in
                        invoices.sorted(key=lambda x: x.name)]
                    history_lines = weekly_move.search(
                        [('w_partner_id', '=', partner_record.id)])
                    if history_lines:
                        history_lines.unlink()
                    for list_data in w_invoice_list:
                        if list_data:
                            weekly_move.create(list_data)
                    self.monthly_statement_flag = False
                    self.weekly_statement_flag = False
            else:
                self.monthly_statement_flag = False
                self.weekly_statement_flag = False

    @api.depends('buyer_monthly_statement_ids', 'buyer_weekly_statement_ids')
    def _compute_monthly_weekly_statement(self):
        current_date = fields.Date.today()
        for customer in self:
            monthly_balance_due = monthly_balance_overdue = weekly_balance_due = weekly_balance_overdue = 0.0
            # Supplier monthly Total
            for move in [x for x in customer.buyer_monthly_statement_ids if x.m_due_invoice_date]:
                date_maturity = move.m_due_invoice_date
                monthly_balance_due += move.m_balance_due_amount
                if date_maturity and date_maturity <= current_date:
                    monthly_balance_overdue += move.m_balance_due_amount
            customer.buyer_amount_due_payment_monthly = monthly_balance_due
            customer.buyer_amount_overdue_payment_monthly = monthly_balance_overdue
            # Supplier weekly Total
            for move in [x for x in customer.buyer_weekly_statement_ids if x.w_due_invoice_date]:
                date_maturity = move.w_due_invoice_date
                weekly_balance_due += move.w_balance_due_amount
                if date_maturity and date_maturity <= current_date:
                    weekly_balance_overdue += move.w_balance_due_amount
            customer.buyer_amount_due_payment_weekly = weekly_balance_due
            customer.buyer_amount_overdue_payment_weekly = weekly_balance_overdue

    def action_show_custom_wizard(self):
        return {'type': 'ir.actions.act_window',
                'name': _('Customize Statement'),
                'res_model': 'buyer.custom.statement.wizard',
                'target': 'new',
                'view_id': self.env.ref('zillotech_buyer_statements.wizard_form_custom_statement_conf').id,
                'view_mode': 'form',
                'context': {'default_partner_ids': self.ids}
                }

    def _sent_custom_statement_email(self):
        custom_move = self.env['buyer.custom.statement']
        for partner_record in self:
            domain_entry = [('move_type', 'in', ['out_invoice', 'out_refund']), ('state', 'in', ['posted']),
                            ('payment_state', 'not in', ['paid']),
                            ('partner_id', '=', partner_record.id), ('invoice_date', '>=',
                                                                     str(partner_record.custom_date_from) if partner_record.custom_date_from else None),
                            ('invoice_date', '<=',
                             str(partner_record.custom_date_to) if partner_record.custom_date_to else None)]
            invoices = self.env['account.move'].search(domain_entry)
            if invoices:
                c_invoice_list = [
                    dict(c_partner_id=invoice.partner_id.id or False, c_invoice_date=invoice.invoice_date or None,
                         c_due_invoice_date=invoice.invoice_date_due or None,
                         c_reference=invoice.name or '',
                         c_credit_payment=invoice.credit_payment or 0.0,
                         c_balance_due_amount=invoice.balance_due_amount or 0.0,
                         c_amount_total=invoice.amount_total or 0.0,
                         c_invoice_id=invoice.id)
                    for
                    invoice in
                    invoices.sorted(key=lambda x: x.name)]
                history_lines = custom_move.search(
                    [('c_partner_id', '=', partner_record.id)])
                if history_lines:
                    history_lines.unlink()
                for list_data in c_invoice_list:
                    if list_data:
                        custom_move.create(list_data)
            if partner_record.email:
                template = self.env.ref('zillotech_buyer_statements.custom_buyer_statement_email_template')
                data = self.env.ref('zillotech_buyer_statements.action_report_buyer_custom_statements').report_action(self,
                                                                                                                data={
                                                                                                                    'partner_id': partner_record})
                if data['report_name']:
                    base_url = partner_record.get_base_url()
                    partner_record.update(
                        {'qr_code_url': base_url + '/report/statements/page/%i' % partner_record.id + '/' + '%s' % data[
                            'report_name']})
                    partner_record.report_name = data['report_name']

                template.report_template = \
                    self.env['ir.actions.report'].search([('report_name', '=', data['report_name'])])[0]
                buyer_to_send = [x for x in partner_record.child_ids if x.email and x.type == 'invoice']
                if partner_record.email and not buyer_to_send:
                    buyer_to_send = [partner_record]
                if buyer_to_send:
                    for buyer_rec in buyer_to_send:
                        template.send_mail(buyer_rec.id, force_send=True)
                        message_line = _(
                            " Customer's Custom Statement sent to %s - %s" % (buyer_rec.name, buyer_rec.email))
                        buyer_rec.message_post(body=message_line)

    # Cron job to send custom statement email weekly and monthly

    def _cron_send_buyer_monthly_statements(self):
        company_id = self.env.user.company_id
        partner_records = self.env['res.partner'].search([])
        if company_id.auto_statement_monthly and company_id.customer_statement_bool:
            partner_records.sent_monthly_cron_buyer_statements(company_id)

    def _cron_send_buyer_weekly_statements(self):
        company_id = self.env.user.company_id
        partner_records = self.env['res.partner'].search([])
        if company_id.auto_statement_weekly and company_id.weekly_statement_selected and company_id.customer_statement_bool:
            partner_records.sent_weekly_cron_buyer_statements(company_id)

    def _cron_send_buyer_overdue_statements(self):
        partner_records = self.env['res.partner'].search([])
        for partner_record in partner_records:
            partner_record.sent_overdue_cron_buyer_statements()

    def sent_overdue_cron_buyer_statements(self):
        self.ensure_one()
        self.buyer_amount_overdue_payment = None
        self._compute_buyer_balance_and_overdue_amount()
        if self.buyer_amount_overdue_payment != 0.00 and self.email:
            overdue_email_template_id = self.env.user.company_id.overdue_email_template_id
            template = overdue_email_template_id if overdue_email_template_id else self.env.ref(
                'zillotech_buyer_statements.buyer_overdue_statement_email_template')
            data = self.action_print_buyer_overdue_statement()
            template.report_template = \
                self.env['ir.actions.report'].search([('report_name', '=', data['report_name'])])[0]
            buyer_to_send = [x for x in self.child_ids if x.email and x.type == 'invoice']
            if self.email and not buyer_to_send:
                buyer_to_send = [self]
            if buyer_to_send:
                for buyer_rec in buyer_to_send:
                    template.send_mail(buyer_rec.id, force_send=True)
                    message_line = _(
                        "Monthly Customer's Statement sent to %s - %s" % (buyer_rec.name, buyer_rec.email))
                    buyer_rec.message_post(body=message_line)

    def sent_monthly_cron_buyer_statements(self, company_id):
        for buyer in self:
            if not buyer.exclude_statements:
                if buyer.email and buyer.buyer_amount_due_payment_monthly != 0.00:
                    template = company_id.monthly_template_report_id
                    if not template:
                        template = self.env.ref('zillotech_buyer_statements.monthly_buyer_statement_email_template')
                    data = self.env.ref('zillotech_buyer_statements.action_report_buyer_monthly_statements')
                    if data['report_name']:
                        base_url = buyer.get_base_url()
                        buyer.update(
                            {'qr_code_url': base_url + '/report/statements/page/%i' % buyer.id + '/' + '%s' % data[
                                'report_name']})
                        buyer.report_name = data['report_name']
                    template.report_template = \
                        self.env['ir.actions.report'].search([('report_name', '=', data['report_name'])])[0]
                    buyer_to_send = [x for x in buyer.child_ids if x.email and x.type == 'invoice']
                    if buyer.email and not buyer_to_send:
                        buyer_to_send = [buyer]
                    if buyer_to_send:
                        for buyer_rec in buyer_to_send:
                            template.send_mail(buyer_rec.id, force_send=True)
                            message_line = _(
                                "Monthly Customer's Statement sent to %s - %s" % (buyer_rec.name, buyer_rec.email))
                            buyer_rec.message_post(body=message_line)

    def sent_weekly_cron_buyer_statements(self, company_id):
        for buyer in self:
            if not buyer.exclude_statements and not buyer.exclude_weekly_statements:
                if buyer.email and buyer.buyer_amount_due_payment_weekly != 0.00:
                    template = company_id.weekly_template_report_id
                    data = self.env.ref('zillotech_buyer_statements.action_report_buyer_weekly_statements')
                    if data['report_name']:
                        base_url = buyer.get_base_url()
                        buyer.update(
                            {'qr_code_url': base_url + '/report/statements/page/%i' % buyer.id + '/' + '%s' % data[
                                'report_name']})
                        buyer.report_name = data['report_name']

                    template.report_template = \
                        self.env['ir.actions.report'].search([('report_name', '=', data['report_name'])])[0]
                    buyer_to_send = [x for x in buyer.child_ids if x.email and x.type == 'invoice']
                    if buyer.email and not buyer_to_send:
                        buyer_to_send = [buyer]
                    if buyer_to_send:
                        for buyer_rec in buyer_to_send:
                            template.send_mail(buyer_rec.id, force_send=True)
                            message_line = _(
                                "Weekly Customer's Statement sent to %s - %s" % (buyer_rec.name, buyer_rec.email))
                            buyer_rec.message_post(body=message_line)

    # Aged Analysis Section
    def _compute_aged_analysis(self):
        """Compute the Aged Analysis"""
        for buyer in self:
            buyer.aged_analysis_f_thirty = buyer.aged_analysis_t_sixty = \
                buyer.aged_analysis_s_ninety = buyer.aged_analysis_ninety_plus = 0
            buyer.aged_analysis_total = 0
            domain = [('partner_id', '=', buyer.id), ('state', 'in', ['posted'])]
            for mov in [vals for data in self.env['account.move'].search(domain) for vals in data.line_ids if
                        vals.account_id.account_type == 'asset_receivable']:
                if mov.date_maturity:
                    date_difference = buyer.current_date - mov.date_maturity
                else:
                    date_difference = buyer.current_date
                if 0 <= date_difference.days <= 30:
                    buyer.aged_analysis_f_thirty = buyer.aged_analysis_f_thirty + mov.amount_residual
                elif 30 < date_difference.days <= 60:
                    buyer.aged_analysis_t_sixty = buyer.aged_analysis_t_sixty + mov.amount_residual
                elif 60 < date_difference.days <= 90:
                    buyer.aged_analysis_s_ninety = buyer.aged_analysis_s_ninety + mov.amount_residual
                else:
                    if date_difference.days > 90:
                        buyer.aged_analysis_ninety_plus = buyer.aged_analysis_ninety_plus + mov.amount_residual
                if buyer.aged_analysis_f_thirty and buyer.aged_analysis_t_sixty and buyer.aged_analysis_s_ninety and \
                        buyer.aged_analysis_ninety_plus:
                    buyer.aged_analysis_total = buyer.aged_analysis_f_thirty + buyer.aged_analysis_t_sixty + \
                                                buyer.aged_analysis_s_ninety + buyer.aged_analysis_ninety_plus
            return

    def _compute_custom_aged_analysis(self):
        """Compute the Custom Aged Analysis"""
        for buyer in self:
            buyer.custom_aged_analysis_f_thirty = buyer.custom_aged_analysis_t_sixty = \
                buyer.custom_aged_analysis_s_ninety = buyer.custom_aged_analysis_ninety_plus = 0
            buyer.custom_aged_analysis_total = 0
            domain = [('partner_id', '=', buyer.id), ('state', 'in', ['posted'])]
            for mov in self.env['account.move'].search(domain).mapped('line_ids'):
                if mov.date_maturity and buyer.custom_date_from <= mov.date_maturity <= buyer.custom_date_to:
                    if mov.date_maturity:
                        date_difference = buyer.current_date - mov.date_maturity
                    else:
                        date_difference = buyer.current_date
                    if 0 <= date_difference.days <= 30:
                        buyer.custom_aged_analysis_f_thirty = buyer.custom_aged_analysis_f_thirty + mov.amount_residual
                    elif 30 < date_difference.days <= 60:
                        buyer.custom_aged_analysis_t_sixty = buyer.custom_aged_analysis_t_sixty + mov.amount_residual
                    elif 60 < date_difference.days <= 90:
                        buyer.custom_aged_analysis_s_ninety = buyer.custom_aged_analysis_s_ninety + mov.amount_residual
                    else:
                        if date_difference.days > 90:
                            buyer.custom_aged_analysis_ninety_plus = buyer.custom_aged_analysis_ninety_plus + mov.amount_residual
                    if buyer.custom_aged_analysis_f_thirty and buyer.custom_aged_analysis_t_sixty and buyer.custom_aged_analysis_s_ninety and \
                            buyer.custom_aged_analysis_ninety_plus:
                        buyer.custom_aged_analysis_total = buyer.custom_aged_analysis_f_thirty + buyer.custom_aged_analysis_t_sixty + \
                                                           buyer.custom_aged_analysis_s_ninety + buyer.custom_aged_analysis_ninety_plus
            return

    # QR Code Section
    @api.depends('qr_code_url')
    def _generate_qr_code(self):
        """Method to generate QR code"""
        for rec in self:
            if rec.qr_code_url:
                if qrcode and base64:
                    qr = qrcode.QRCode(
                        version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=3,
                        border=4,
                    )
                    qr.add_data("Link : ")
                    qr.add_data(str(rec.qr_code_url))
                    qr.make(fit=True)
                    img = qr.make_image()
                    temp = BytesIO()
                    img.save(temp, format="PNG")
                    qr_image = base64.b64encode(temp.getvalue())
                    rec.update({'qr_code': qr_image})
                else:
                    raise UserError(_('Necessary Requirements To Run This Operation Is Not Satisfied'))
            else:
                rec.update({'qr_code': False})

    @api.depends('company_id.global_note')
    def _compute_global_note(self):
        """Method to compute global note"""
        for rec in self:
            rec.global_note = rec.env.company.global_note

    monthly_statement_flag = fields.Boolean(string="Monthly Statement Flag", default=False)
    weekly_statement_flag = fields.Boolean(string="Monthly Statement Flag", default=False)
    buyer_monthly_statement_ids = fields.One2many('buyer.monthly.statement', 'm_partner_id',
                                                  'Buyer Monthly Statement')
    buyer_amount_due_payment_monthly = fields.Float(string="Monthly Statement Amount",
                                                    compute="_compute_monthly_weekly_statement")
    buyer_amount_overdue_payment_monthly = fields.Float(string="Monthly Overdue Statement Amount",
                                                        compute="_compute_monthly_weekly_statement")
    buyer_weekly_statement_ids = fields.One2many('buyer.weekly.statement', 'w_partner_id',
                                                 'Buyer Weekly Statement')
    buyer_amount_due_payment_weekly = fields.Float(string="Weekly Statement Amount",

                                                   compute="_compute_monthly_weekly_statement")

    buyer_amount_overdue_payment_weekly = fields.Float(string="Weekly Overdue Statement Amount",
                                                       compute="_compute_monthly_weekly_statement")
    # Buyer Form Section
    buyer_balance_ids = fields.One2many('account.move', 'partner_id', 'Buyer Balance Lines',
                                        domain=[('state', 'in', ['posted']), ('payment_state', 'not in', ['paid']),
                                                ('move_type', 'in', ['out_refund', 'out_invoice', ])])

    buyer_amount_overdue_payment = fields.Float(compute='_compute_buyer_balance_and_overdue_amount',
                                                string="Total Overdue Amount", store=True)
    buyer_amount_due_payment = fields.Float(compute='_compute_buyer_balance_and_overdue_amount',
                                            string="Balance Due Amount")
    # Buyer Filter Form Section
    buyer_statement_date_from = fields.Date('From Date')
    buyer_statement_date_to = fields.Date('To Date')
    buyer_initial_balance = fields.Float('Initial Balance')
    buyer_filter_line_ids = fields.One2many('filter.data.line', 'partner_id', 'Filter Data Lines')
    buyer_amount_due_payment_filtered = fields.Float(compute='_compute_buyer_filter_balance_and_overdue_amount',
                                                     string="Filtered Balance Due Amount")
    buyer_amount_overdue_payment_filtered = fields.Float(compute='_compute_buyer_filter_balance_and_overdue_amount',
                                                         string="Filtered Total Overdue Amount", store=True)
    current_date = fields.Date(default=fields.Date.today())
    # Supplier Form Section
    supplier_balance_ids = fields.One2many('account.move', 'partner_id', 'Buyer Balance Lines',
                                           domain=[('move_type', 'in', ['in_invoice', 'in_refund']),
                                                   ('state', 'in', ['posted'])])
    supplier_amount_overdue_payment = fields.Float(compute='_compute_supplier_balance_and_overdue_amount',
                                                   string="Total Overdue Amount", store=True)
    supplier_amount_due_payment = fields.Float(compute='_compute_supplier_balance_and_overdue_amount',
                                               string="Balance Due Amount")
    # Supplier Filter Form Section
    supplier_statement_date_from = fields.Date('From Date')
    supplier_statement_date_to = fields.Date('To Date')
    supplier_initial_balance = fields.Float('Supplier Initial Balance')
    supplier_filter_line_ids = fields.One2many('filter.supplier.data.line', 'partner_id', 'Filter Supplier Data Lines')
    supplier_amount_due_payment_filtered = fields.Float(compute='_compute_supplier_filter_balance_and_overdue_amount',
                                                        string="Filtered Balance Due Amount")
    supplier_amount_overdue_payment_filtered = fields.Float(
        compute='_compute_supplier_filter_balance_and_overdue_amount',
        string="Filtered Total Overdue Amount", store=True)
    # Supplier Custom Section
    custom_statement_line_ids = fields.One2many('buyer.custom.statement', 'c_partner_id', 'Buyer Custom Statements')
    custom_duration = fields.Selection([
        ('30', 'Thirty Days '),
        ('60', 'Sixty Days'),
        ('90', 'Ninety Days'),
        ('3m', 'Quarter'),
        ('custom', 'Custom Date Range'),
    ], string="Duration", required=True, default="30")
    custom_date_from = fields.Date('From Date')
    custom_date_to = fields.Date('To Date')
    # Aged Analysis
    aged_analysis_f_thirty = fields.Float(string="0-30", compute="_compute_aged_analysis")
    aged_analysis_t_sixty = fields.Float(string="30-60", compute="_compute_aged_analysis")
    aged_analysis_s_ninety = fields.Float(string="60-90", compute="_compute_aged_analysis")
    aged_analysis_ninety_plus = fields.Float(string="90+", compute="_compute_aged_analysis")
    aged_analysis_total = fields.Float(string="Total", compute="_compute_aged_analysis")
    # Aged Analysis ( Custom )
    custom_aged_analysis_f_thirty = fields.Float(string="0-30 Custom", compute="_compute_custom_aged_analysis")
    custom_aged_analysis_t_sixty = fields.Float(string="30-60 Custom", compute="_compute_custom_aged_analysis")
    custom_aged_analysis_s_ninety = fields.Float(string="60-90 Custom", compute="_compute_custom_aged_analysis")
    custom_aged_analysis_ninety_plus = fields.Float(string="90+ Custom", compute="_compute_custom_aged_analysis")
    custom_aged_analysis_total = fields.Float(string="Total", compute="_compute_custom_aged_analysis")
    # Exclude Customer
    exclude_statements = fields.Boolean(string="Exclude Statements", default=False)
    exclude_monthly_statements = fields.Boolean(string="Monthly Statements", default=False)
    exclude_weekly_statements = fields.Boolean(string="Weekly Statements", default=False)
    # Internal Notes
    nck_internal_notes = fields.Text(string="Internal Notes")
    disable_global_notes = fields.Boolean(string="Disable Global Notes", default=False)
    global_note = fields.Text(" ", compute="_compute_global_note")
    # QR Code
    qr_code = fields.Binary('QR Code', compute="_generate_qr_code", store=True)
    qr_code_url = fields.Char(string="QR Code URL")
    report_name = fields.Char(string="Report Name")
    # Website Checkbox
    inv_null = fields.Boolean(string="Inv Null", default=False)
    inv_reference = fields.Char(string="Inv Reference")
    multi_inv_total = fields.Float(string="Multi Inv Total", default=0.0)
    multi_inv_ids = fields.Many2many('account.move', string="Multi Invoices")
