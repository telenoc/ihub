# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

import base64

from odoo import api, fields, models


class Invoice(models.Model):
    _inherit = 'account.move'

    invoice_date = fields.Date('Invoice Date')
    l10n_ar_qr_data = fields.Char(string="FATOORA E-Invoicing QR Data", compute="_compute_qr_data")

    def get_total_discount(self):
        total_disc = 0
        for rec in self:
            for line in rec.invoice_line_ids:
                total_disc += (((line.discount * line.price_unit) * line.quantity) / 100)
        return total_disc

    def get_address(self, partner, company=False):
        partner_address = []
        if partner.street:
            partner_address.append(partner.street)
        if partner.street2:
            partner_address.append(partner.street2)
        if not company and partner.city:
            partner_address.append(partner.city)
        if not company and partner.country_id:
            partner_address.append(partner.country_id.name)
        if not company and partner.zip:
            partner_address.append(partner.zip)
        partner_add = ','.join(str(e) for e in partner_address)
        return partner_add

    @api.depends('amount_total', 'state', 'amount_tax', 'invoice_date')
    def _compute_qr_data(self):
        def to_byte_array(tvl):
            '''Translate all keys and values into an array of bytes.'''
            values = bytes()
            for k, v in tvl.items():
                val = v.encode('utf-8')
                values += int(k).to_bytes(1, byteorder='big')
                values += len(val).to_bytes(1, byteorder='big')
                values += val  # binascii.hexlify(v.encode('utf-8'))#
            return values

        for invoice in self:
            if not invoice.company_id.vat:
                invoice.l10n_ar_qr_data = False
                continue
            if not invoice.invoice_date:
                invoice.l10n_ar_qr_data = False
                continue
            tlv_dict = dict()
            tlv_dict[0x01] = invoice.company_id.name
            tlv_dict[0x02] = invoice.company_id.vat
            tlv_dict[0x03] = invoice.invoice_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            tlv_dict[0x04] = '{:.2f}'.format(invoice.amount_total_signed)
            tlv_dict[0x05] = '{:.2f}'.format(invoice.amount_tax_signed)
            byte_array = to_byte_array(tlv_dict)
            invoice.l10n_ar_qr_data = base64.b64encode(byte_array).decode('utf-8')
