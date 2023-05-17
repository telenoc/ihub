import time
from odoo import api, models, _


class OutstandingReportPDFValues(models.AbstractModel):
    _name = 'report.zillotech_buyer_statements.report_print_pdf_o_report'
    _description = "Outstanding Invoices Report"

    def _get_report_values(self, doc_ids, data=None):
        return {
            'doc_ids': self.ids,
            'docs': self,
            'data': data,
            'time': time,
            'get_customer': self._get_customer,
        }

    def _get_customer(self, partner):
        return self.env['res.partner'].browse(int(partner)).name
