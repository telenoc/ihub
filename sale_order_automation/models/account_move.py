from odoo import api, fields, models, exceptions


class SaleOrderLine(models.Model):
    _inherit = "account.move.line"

    uom_note = fields.Char(string="UoM Note")
