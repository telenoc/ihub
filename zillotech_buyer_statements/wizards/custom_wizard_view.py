from dateutil.relativedelta import relativedelta
from odoo import fields, models, api


class CustomStatementWizard(models.TransientModel):
    _name = 'buyer.custom.statement.wizard'
    _description = 'Send Customer Statement'

    custom_duration = fields.Selection([
        ('30', 'Thirty Days '),
        ('60', 'Sixty Days'),
        ('90', 'Ninety Days'),
        ('3m', 'Quarter'),
        ('custom', 'Custom Date Range'),
    ], string="Duration", required=True, default="30")
    custom_date_from = fields.Date(string='From Date')
    custom_date_to = fields.Date(string='To Date')

    def custom_statement_buyer_statements(self):
        if self._context.get('default_partner_ids'):
            active_partners = self.env['res.partner'].browse(self._context.get('default_partner_ids', []))
        else:
            active_partners = self.env['res.partner'].browse(self._context.get('active_ids', []))
        for partner in active_partners:
            partner.custom_duration = self.custom_duration
            if self.custom_duration:
                if self.custom_duration == 'custom':
                    partner.custom_date_from = fields.Date.today() - relativedelta(months=3)
                    partner.custom_date_to = fields.Date.today()
                elif self.custom_duration == '3m':
                    partner.custom_date_from = fields.Date.today() - relativedelta(months=int(3))
                    partner.custom_date_to = fields.Date.today()
                elif self.custom_duration == '30' or '60' or '90':
                    partner.custom_date_from = fields.Date.today() - relativedelta(days=int(self.custom_duration))
                    partner.custom_date_to = fields.Date.today()

                else:
                    partner.custom_date_from = False
                    partner.custom_date_to = False
            partner._sent_custom_statement_email()
