import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.exceptions import ValidationError

Field_Week_Data = [('0', 'Monday'), ('1', 'Tuesday'), ('2', 'Wednesday'), ('3', 'Thursday'), ('4', 'Friday'),
                   ('5', 'Saturday'), ('6', 'Sunday'), ]
Res_Partner = 'res.partner'
Mail_Template = 'mail.template'


class ResCompanyData(models.Model):
    _inherit = 'res.company'

    int_overdue_day_num = fields.Integer("Overdue Statement Send Date")
    send_overdue_statement = fields.Boolean("Send Overdue customer Statement")
    customer_statement_bool = fields.Boolean("Send customer's Statement")
    overdue_email_template_id = fields.Many2one(Mail_Template, 'Template for Overdue Statements',
                                                domain=[('model', '=', Res_Partner)])
    auto_statement_monthly = fields.Boolean("Auto Monthly Statement")
    auto_statement_weekly = fields.Boolean("Auto Weekly Statement")
    weekly_statement_selected = fields.Selection(Field_Week_Data, string="Weekly Send Day")
    int_monthly_statement_num = fields.Integer("Monthly Send Day")
    weekly_template_report_id = fields.Many2one(Mail_Template, 'Weekly Statement Email Template',
                                                domain=[('model', '=', Res_Partner)])
    monthly_template_report_id = fields.Many2one(Mail_Template, 'Monthly Statement Email Template',
                                                 domain=[('model', '=', Res_Partner)])
    global_note_bool = fields.Boolean("Enable Global Note")
    global_note = fields.Text("Global Note")

    def _scheduled_time_selector(self, total_days):
        date_time_expected = datetime(now.year, now.month, total_days, now.hour, now.minute, now.second)
        present_day = datetime.now()
        scheduled_datetime = date_time_expected
        if present_day.day > total_days:
            scheduled_datetime = date_time_expected + relativedelta(months=+1)
            return scheduled_datetime
        return scheduled_datetime

    @api.onchange('customer_statement_bool', 'send_overdue_statement')
    def _onchange_res_company_settings(self):
        if self.send_overdue_statement:
            scheduled_data_reference = self.env.ref('zillotech_buyer_statements.cron_send_buyer_overdue_statements')
            scheduled_data_reference.active = self.send_overdue_statement
            scheduled_datetime = self._scheduled_time_selector(self.send_overdue_statement)
            scheduled_data_reference.nextcall = str(scheduled_datetime)

        if self.customer_statement_bool and self.auto_statement_monthly:
            scheduled_data_reference = self.env.ref('zillotech_buyer_statements.cron_send_buyer_monthly_statement')
            scheduled_data_reference.active = self.auto_statement_monthly
            scheduled_datetime = self._scheduled_time_selector(self.int_monthly_statement_num)
            scheduled_data_reference.nextcall = str(scheduled_datetime)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    int_overdue_day_num = fields.Integer("Overdue Statement Send Date", related='company_id.int_overdue_day_num',
                                         readonly=False)
    send_overdue_statement = fields.Boolean("Send Overdue Customer Statement",
                                            related='company_id.send_overdue_statement',
                                            readonly=False)
    overdue_email_template_id = fields.Many2one(Mail_Template, 'Template for Overdue Statements',
                                                domain=[('model', '=', Res_Partner)],
                                                related='company_id.overdue_email_template_id',
                                                readonly=False)
    customer_statement_bool = fields.Boolean("Send Customer's Statement", related='company_id.customer_statement_bool',
                                             readonly=False)
    auto_statement_monthly = fields.Boolean("Auto Monthly Statement", related='company_id.auto_statement_monthly',
                                            readonly=False)
    auto_statement_weekly = fields.Boolean("Auto Weekly Statement", related='company_id.auto_statement_weekly',
                                           readonly=False)
    weekly_statement_selected = fields.Selection(string="Weekly Send Day",
                                                 related='company_id.weekly_statement_selected',
                                                 readonly=False)
    int_monthly_statement_num = fields.Integer("Monthly Send Day", related='company_id.int_monthly_statement_num',
                                               readonly=False)
    weekly_template_report_id = fields.Many2one(Mail_Template, 'Weekly Statement Email Template',
                                                domain=[('model', '=', Res_Partner)],
                                                related='company_id.weekly_template_report_id',
                                                readonly=False)
    monthly_template_report_id = fields.Many2one(Mail_Template, 'Monthly Statement Email Template',
                                                 domain=[('model', '=', Res_Partner)],
                                                 related='company_id.monthly_template_report_id',
                                                 readonly=False)
    global_note_bool = fields.Boolean("Enable Global Note", related='company_id.global_note_bool',
                                      readonly=False)
    global_note = fields.Text("Global Note", related='company_id.global_note',
                              readonly=False)

    @api.constrains('int_overdue_day_num', 'monthly_statement_flag')
    def _check_monthly_statement_flag(self):
        if self.int_monthly_statement_num and self.int_monthly_statement_num > 31 or self.int_monthly_statement_num <= 0:
            raise ValidationError(_('Enter Valid Date Range for taking Statements'))
        if self.send_overdue_statement and self.int_overdue_day_num > 31 or self.int_overdue_day_num <= 0:
            raise ValidationError(_('Enter Valid Date Range for taking Overdue Statements'))
