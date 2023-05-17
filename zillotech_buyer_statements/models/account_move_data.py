from odoo import fields, models, _


class AccountMoveResult(models.Model):
    _inherit = 'account.move'

    credit_payment = fields.Float(compute='_compute_credit_payment', string="Credit Amount")
    balance_due_amount = fields.Float(compute='_compute_balance_due_amount', string="Balance Due Amount")
    multi_access_token = fields.Char(string='Multi Access Token', copy=False)

    def _compute_balance_due_amount(self):
        def _get_data():
            move.balance_due_amount = 0.0
            return sign_of_move * (abs(move.amount_total_signed) - abs(move.credit_payment))

        for move in self:
            sign_of_move = -1 if move.is_outbound() else 1
            move.balance_due_amount = _get_data()

    def _compute_credit_payment(self):
        for move in self:
            move.credit_payment = 0.0
            move.credit_payment = abs(move.amount_total_signed) - abs(move.amount_residual_signed)
