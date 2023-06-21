# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Sitaram Solutions (<https://sitaramsolutions.in/>).
#
#    For Module Support : info@sitaramsolutions.in  or Skype : contact.hiren1188
#
##############################################################################

from odoo import fields, api, models, _


class srPartialMultiPaymentWizard(models.TransientModel):
    _name = "partial.multi.payment.wizard"
    _description = "Partial Multi Payment Wizard"

    partner_type = fields.Selection(
        [("customer", "Customer"), ("supplier", "Vendor")],
        string="Partner Type",
        default="customer",
    )
    partner_id = fields.Many2one(comodel_name="res.partner", string="Partner")
    move_type = fields.Selection(
        [("in_invoice", "Vendor Bill"), ("out_invoice", "Customer Invoice")],
        string="Move Type",
    )
    payment_type = fields.Selection(
        [("payin", "Customer Payment"), ("payout", "Vendor Payment")],
        string="Payment Type",
        default="payin",
    )
    company_currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Company Currency",
        default=lambda self: self.env.user.company_id.currency_id.id,
    )
    move_line_id = fields.Many2one(
        comodel_name="account.move.line",
        string="Customer/Vendor Payment Line",
        domain=lambda self: [("payment_id.partner_type", "=", self.partner_type)],
    )
    name = fields.Char(related="move_line_id.payment_id.name", string="Payment Name")
    move_id = fields.Many2one(comodel_name="account.move", string="Account Move")
    currency_id = fields.Many2one(comodel_name="res.currency", string="Currency")
    amount_residual = fields.Monetary(string="Residual Amount")
    remain_amount = fields.Monetary(
        compute="compute_remaining_amount", store=True, string="Remain Amount"
    )
    amount_residual_currency = fields.Monetary(string="Currency Residual Amount")
    remain_amount_currency = fields.Monetary(
        compute="compute_remaining_amount", string="Currency Remain Amount", store=True
    )
    move_line_ids = fields.One2many(
        comodel_name="multi.move.line",
        inverse_name="multi_partial_payment_id",
        string="Move Lines",
    )

    @api.depends("move_line_ids.curr_amount_to_pay")
    def compute_remaining_amount(self):
        self.remain_amount = self.amount_residual - sum(
            self.move_line_ids.mapped("curr_amount_to_pay")
        )
        self.remain_amount_currency = self.amount_residual_currency - sum(
            self.move_line_ids.mapped("curr_amount_to_pay")
        )

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        payments = self.env["account.payment"].search(
            [("partner_id", "=", self.partner_id.id)]
        )
        lines = payments.mapped("move_id").mapped("line_ids")
        return {
            "domain": {
                "move_line_id": [
                    (
                        "id",
                        "in",
                        lines.filtered(
                            lambda l: (
                                l.payment_id.partner_type == "customer"
                                and l.credit
                                and not l.partial_matching_number
                            )
                            or (
                                l.payment_id.partner_type == "supplier"
                                and l.debit
                                and not l.partial_matching_number
                            )
                        ).ids,
                    ),
                    ("payment_id.partner_type", "=", self.partner_type),
                    ("reconciled", "!=", True),
                ]
            }
        }

    @api.onchange("move_line_id")
    def onchange_move_line_id(self):
        if self.move_line_id:
            self.move_id = self.move_line_id.move_id.id
            self.currency_id = self.move_line_id.currency_id.id
            self.amount_residual = abs(self.move_line_id.amount_residual)
            self.amount_residual_currency = abs(self.move_line_id.amount_currency)
            self.remain_amount = abs(self.move_line_id.amount_residual)
            self.remain_amount_currency = abs(self.move_line_id.amount_currency)

    def sr_register_payment(self):
        line_id = self.move_line_id
        if line_id.payment_id.partner_type == "customer":
            for line in self.move_line_ids:
                if line.curr_amount_to_pay > 0.0:
                    vals_list = []
                    amount_to_pay = self.currency_id.compute(
                        line.amount_to_pay, line.payment_currency_id
                    )
                    vals_list.append(
                        (
                            0,
                            0,
                            {
                                "account_id": line_id.account_id.id,
                                "partner_id": line_id.partner_id.id,
                                "name": line_id.move_name + ' - ' + line.move_id.name,
                                "amount_currency": -amount_to_pay,
                                "debit": 0.0,
                                "credit": amount_to_pay,
                                "tax_ids": [(6, 0, line_id.tax_ids.ids)],
                                "date_maturity": line_id.date_maturity,
                            },
                        )
                    )
                    vals_list.append(
                        (
                            1,
                            line_id.id,
                            {
                                "debit": 0.0,
                                "credit": line_id.credit - amount_to_pay,
                                "amount_currency": -(line_id.credit - amount_to_pay),
                            },
                        )
                    )
                    line_id.payment_id.write({"sr_is_partial": True})
                    line_id.payment_id.move_id.write({"line_ids": vals_list})

                    partial_sequence = (
                        self.env["ir.sequence"].next_by_code("account.move.line") or ""
                    )
                    lines = line_id.payment_id.move_id.line_ids.filtered(
                        lambda l: l.credit == line.amount_to_pay
                        and l.move_id.id == line_id.payment_id.move_id.id
                    )
                    if lines and len(lines.ids) > 1:
                        lines = lines[-1]

                    if lines and not lines.partial_matching_number:
                        lines[-1].write({"partial_matching_number": partial_sequence})

                    move_line = line.move_id.line_ids.filtered(
                        lambda l: l.credit != line.amount_to_pay
                        and l.account_id.id == lines.account_id.id
                        and l.move_id.id == line.move_id.id
                    )
                    if move_line and not move_line.partial_matching_number:
                        move_line.write({"partial_matching_number": partial_sequence})
                    elif move_line and move_line.partial_matching_number:
                        move_line.write(
                            {
                                "partial_matching_number": "%s,%s"
                                % (move_line.partial_matching_number, partial_sequence)
                            }
                        )
                    lines += move_line
                    result = lines.reconcile()
        if line_id.payment_id.partner_type == "supplier":
            for line in self.move_line_ids:
                if line.curr_amount_to_pay > 0.0:
                    vals_list = []
                    amount_to_pay = self.currency_id.compute(
                        line.amount_to_pay, line.payment_currency_id
                    )
                    vals_list.append(
                        (
                            0,
                            0,
                            {
                                "account_id": line_id.account_id.id,
                                "partner_id": line_id.partner_id.id,
                                "name": line_id.move_name + ' - ' + line.move_id.name,
                                "amount_currency": amount_to_pay,
                                "debit": amount_to_pay,
                                "credit": 0.0,
                                "tax_ids": [(6, 0, line_id.tax_ids.ids)],
                                "date_maturity": line_id.date_maturity,
                            },
                        )
                    )
                    vals_list.append(
                        (
                            1,
                            line_id.id,
                            {
                                "debit": line_id.debit - amount_to_pay,
                                "credit": 0.0,
                                "amount_currency": (line_id.debit - amount_to_pay),
                            },
                        )
                    )
                    line_id.payment_id.write({"sr_is_partial": True})
                    line_id.payment_id.move_id.write({"line_ids": vals_list})

                    partial_sequence = (
                        self.env["ir.sequence"].next_by_code("account.move.line") or ""
                    )
                    lines = line_id.payment_id.move_id.line_ids.filtered(
                        lambda l: l.debit == line.amount_to_pay
                        and l.move_id.id == line_id.payment_id.move_id.id
                    )
                    if lines and len(lines.ids) > 1:
                        lines = lines[-1]

                    if lines and not lines.partial_matching_number:
                        lines.write({"partial_matching_number": partial_sequence})

                    move_line = line.move_id.line_ids.filtered(
                        lambda l: l.debit != line.amount_to_pay
                        and l.account_id.id == lines.account_id.id
                        and l.move_id.id == line.move_id.id
                    )
                    if move_line and not move_line.partial_matching_number:
                        move_line.write({"partial_matching_number": partial_sequence})
                    elif move_line and move_line.partial_matching_number:
                        move_line.write(
                            {
                                "partial_matching_number": "%s,%s"
                                % (move_line.partial_matching_number, partial_sequence)
                            }
                        )
                    lines += move_line
                    result = lines.reconcile()
        return {"type": "ir.actions.client", "tag": "reload"}


class srMultiMoveLine(models.TransientModel):
    _name = "multi.move.line"
    _description = "Multi Move Line"

    multi_partial_payment_id = fields.Many2one(
        comodel_name="partial.multi.payment.wizard", string="Multi Partial Payment"
    )
    move_type = fields.Selection(
        [("in_invoice", "Vendor Bill"), ("out_invoice", "Customer Invoice")],
        string="Move Type",
    )
    partner_id = fields.Many2one(comodel_name="res.partner", string="Partner")
    payment_move_id = fields.Many2one(
        comodel_name="account.move", string="Payment Account Move"
    )
    company_currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Company Currency",
        default=lambda self: self.env.user.company_id.currency_id.id,
    )
    payment_currency_id = fields.Many2one(
        comodel_name="res.currency", string="Payment Currency"
    )
    move_id = fields.Many2one(comodel_name="account.move", string="Account Move")
    currency_id = fields.Many2one(comodel_name="res.currency", string="Currency")
    amount_residual = fields.Monetary(string="Residual Amount")
    amount_residual_currency = fields.Monetary(
        related="move_id.amount_residual_signed", string="Currency Remain Amount"
    )
    curr_amount_to_pay = fields.Monetary(string="Current Amount to Pay")
    amount_to_pay = fields.Monetary(
        related="curr_amount_to_pay", string="Amount to Pay"
    )

    @api.onchange("curr_amount_to_pay")
    def onchange_curr_amount_to_pay(self):
        if self.curr_amount_to_pay:
            self.amount_to_pay = self.payment_currency_id.compute(
                self.curr_amount_to_pay, self.company_currency_id
            )
            remain_amount = self.currency_id.compute(
                self.multi_partial_payment_id.remain_amount, self.company_currency_id
            )
            self.multi_partial_payment_id.remain_amount = (
                self.multi_partial_payment_id.remain_amount - remain_amount
            )
            self.multi_partial_payment_id.remain_amount_currency = (
                self.multi_partial_payment_id.remain_amount_currency
                - self.curr_amount_to_pay
            )

    @api.onchange("move_id")
    def onchange_move_id(self):
        if self.move_id:
            self.currency_id = self.move_id.currency_id.id
            self.amount_residual = self.move_id.currency_id.compute(
                self.move_id.amount_residual, self.company_currency_id
            )
            self.amount_to_pay = self.payment_currency_id.compute(
                self.curr_amount_to_pay, self.company_currency_id
            )


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
