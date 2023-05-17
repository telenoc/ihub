from odoo import models, fields, api, _


class PartnerData(models.TransientModel):
    _name = "partner.email.wizard"
    _description = "Email Partners"

    customer_id = fields.Many2one('res.partner', readonly=True)
    email = fields.Char('Email', readonly=False)
    customer_bool = fields.Boolean("Send", default=False)
    overdue_bool = fields.Boolean("Overdue", default=False)
    filter_bool = fields.Boolean("Filtered", default=False)

    def action_sent_buyer_mail_from_wizard(self):
        if self.email:
            template = self.env.ref('zillotech_buyer_statements.buyer_statement_email_template')
            data = self.customer_id.action_print_buyer_statement()
            template.report_template = \
                self.customer_id.env['ir.actions.report'].search([('report_name', '=', data['report_name'])])[0]
            for buyer in self.customer_id:
                buyer_to_send = [x for x in buyer.child_ids if x.email and x.type == 'invoice']
                if buyer.email and not buyer_to_send:
                    buyer_to_send = [buyer]
                if buyer_to_send:
                    for buyer_rec in buyer_to_send:
                        template.send_mail(buyer_rec.id, force_send=True, email_values={'email_to': self.email})
                        message_line = _("Customer's Statement sent to %s - %s" % (buyer_rec.name, self.email))
                        buyer_rec.message_post(body=message_line)
        else:
            raise Warning('Email address is not a valid !')
        return True

    def action_sent_buyer_overdue_mail_from_wizard(self):
        if self.email:
            template = self.env.ref('zillotech_buyer_statements.buyer_overdue_statement_email_template')
            data = self.customer_id.action_print_buyer_overdue_statement()
            template.report_template = \
                self.env['ir.actions.report'].search([('report_name', '=', data['report_name'])])[0]
            for buyer in self.customer_id:
                buyer_to_send = [x for x in buyer.child_ids if x.email and x.type == 'invoice']
                if buyer.email and not buyer_to_send:
                    buyer_to_send = [buyer]
                if buyer_to_send:
                    for buyer_rec in buyer_to_send:
                        template.send_mail(buyer_rec.id, force_send=True, email_values={'email_to': self.email})
                        message_line = _("Customer's Overdue Statement sent to %s - %s" % (buyer_rec.name, self.email))
                        buyer_rec.message_post(body=message_line)
        else:
            raise Warning('Email address is not a valid !')
        return True

    def action_sent_filtered_buyer_statement_from_wizard(self):
        if self.email:
            template = self.env.ref('zillotech_buyer_statements.buyer_filtered_statement_email_template')
            data = self.customer_id.action_print_filtered_buyer_statement()
            template.report_template = \
                self.env['ir.actions.report'].search([('report_name', '=', data['report_name'])])[0]
            for buyer in self.customer_id:
                buyer_to_send = [x for x in buyer.child_ids if x.email and x.type == 'invoice']
                if buyer.email and not buyer_to_send:
                    buyer_to_send = [buyer]
                if buyer_to_send:
                    for buyer_rec in buyer_to_send:
                        template.send_mail(buyer_rec.id, force_send=True, email_values={'email_to': self.email})
                        message_line = _(
                            "Customer's Filtered Statement sent to %s - %s" % (buyer_rec.name, self.email))
                        buyer_rec.message_post(body=message_line)
        else:
            raise Warning('Email address is not a valid !')
        return True
