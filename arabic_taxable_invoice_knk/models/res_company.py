# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    knk_footer = fields.Char('Footer')
    company_registry = fields.Char('Company Registry')
    knk_header1 = fields.Char('Header 1st Line')
    knk_header2 = fields.Char('Header 2nd Line')
    knk_header3 = fields.Char('Header 3rd Line')
    knk_header4 = fields.Char('Header 4th Line')
