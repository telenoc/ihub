# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Sitaram Solutions (<https://sitaramsolutions.in/>).
#
#    For Module Support : info@sitaramsolutions.in  or Skype : contact.hiren1188
#
##############################################################################

import json
from odoo import fields, api, models, _
from odoo.exceptions import UserError


class srAccountMoveLine(models.Model):
    _inherit = "account.move.line"

    partial_matching_number = fields.Char(
        string="Partial Matching #",
        help="Partial Matching number for this line, 'PM' if it is only partially reconcile, or the name of the full reconcile if it exists.",
    )