from odoo import fields, models

PAYMENT_STATE_SELECTION = [
    ('not_paid', 'Not Paid'),
    ('in_payment', 'In Payment'),
    ('paid', 'Paid'),
    ('partial', 'Partially Paid'),
    ('reversed', 'Reversed'),
    ('invoicing_legacy', 'Invoicing App Legacy'),
]


class BuyerMonthlyStatement(models.Model):
    _name = 'buyer.monthly.statement'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Buyer Monthly Statement"
    _order = 'm_invoice_date'

    m_invoice_id = fields.Many2one('account.move', string='Invoice')
    m_reference = fields.Char('Name')
    m_invoice_date = fields.Date('Invoice Date')
    m_due_invoice_date = fields.Date('Due Date')
    m_amount_total_signed = fields.Monetary(related='m_invoice_id.amount_total_signed',
                                            currency_field='currency_id', )
    m_credit_payment = fields.Float("Payments/Credits")
    m_partner_id = fields.Many2one('res.partner', string='Customer')
    m_balance_due_amount = fields.Float("Balance")
    m_amount_total = fields.Float("Invoices/Debits")
    company_id = fields.Many2one('res.company', string='Company')
    currency_id = fields.Many2one(related='m_invoice_id.currency_id')
    m_payment_id = fields.Many2one('account.payment', string='Payment')
    m_amount_residual = fields.Monetary(related='m_invoice_id.amount_residual')
    m_amount_residual_signed = fields.Monetary(related='m_invoice_id.amount_residual_signed',
                                               currency_field='currency_id', )

    m_state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled')
    ], string='State', readonly=True, copy=False, required=True,
        default='draft')
    payment_state = fields.Selection(PAYMENT_STATE_SELECTION, string="Payment Status",
                                     readonly=True, copy=False, tracking=True)
    transaction_ids = fields.Many2many(
        string="Transactions", comodel_name='payment.transaction',
        relation='account_invoice_monthly_transaction_rel', column1='invoice_id', column2='transaction_id',
        readonly=True, copy=False)
    move_type = fields.Selection(selection=[
        ('entry', 'Journal Entry'),
        ('out_invoice', 'Customer Invoice'),
        ('out_refund', 'Customer Credit Note'),
        ('in_invoice', 'Vendor Bill'),
        ('in_refund', 'Vendor Credit Note'),
        ('out_receipt', 'Sales Receipt'),
        ('in_receipt', 'Purchase Receipt'),
    ], string='Type', required=True, store=True, index=True, readonly=True, tracking=True,
        default="entry", change_default=True)


class BuyerWeeklyStatement(models.Model):
    _name = 'buyer.weekly.statement'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Buyer Weekly Statement"
    _order = 'w_invoice_date'

    w_invoice_id = fields.Many2one('account.move', string='Invoice')
    w_reference = fields.Char('Name')
    w_invoice_date = fields.Date('Invoice Date')
    w_due_invoice_date = fields.Date('Due Date')
    w_amount_total_signed = fields.Monetary(related='w_invoice_id.amount_total_signed',
                                            currency_field='currency_id', )
    w_credit_payment = fields.Float("Payments/Credits")
    w_partner_id = fields.Many2one('res.partner', string='Customer')
    w_balance_due_amount = fields.Float("Balance")
    w_amount_total = fields.Float("Invoices/Debits")
    company_id = fields.Many2one('res.company', string='Company')
    currency_id = fields.Many2one(related='w_invoice_id.currency_id')
    w_payment_id = fields.Many2one('account.payment', string='Payment')
    w_amount_residual = fields.Monetary(related='w_invoice_id.amount_residual')
    w_amount_residual_signed = fields.Monetary(related='w_invoice_id.amount_residual_signed',
                                               currency_field='currency_id', )
    w_state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled')
    ], string='State', readonly=True, copy=False, required=True,
        default='draft')
    payment_state = fields.Selection(PAYMENT_STATE_SELECTION, string="Payment Status",
                                     readonly=True, copy=False, tracking=True)
    transaction_ids = fields.Many2many(
        string="Transactions", comodel_name='payment.transaction',
        relation='account_invoice_weekly_transaction_rel', column1='invoice_id', column2='transaction_id',
        readonly=True, copy=False)
    move_type = fields.Selection(selection=[
        ('entry', 'Journal Entry'),
        ('out_invoice', 'Customer Invoice'),
        ('out_refund', 'Customer Credit Note'),
        ('in_invoice', 'Vendor Bill'),
        ('in_refund', 'Vendor Credit Note'),
        ('out_receipt', 'Sales Receipt'),
        ('in_receipt', 'Purchase Receipt'),
    ], string='Type', required=True, store=True, index=True, readonly=True, tracking=True,
        default="entry", change_default=True)


class CustomBuyerStatement(models.Model):
    _name = 'buyer.custom.statement'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Buyer Custom Statement"
    _order = 'c_invoice_date'

    c_invoice_id = fields.Many2one('account.move', string='Invoice')
    c_reference = fields.Char('Name')
    c_invoice_date = fields.Date('Invoice Date')
    c_due_invoice_date = fields.Date('Due Date')
    c_amount_total_signed = fields.Monetary(related='c_invoice_id.amount_total_signed',
                                            currency_field='currency_id', )
    c_credit_payment = fields.Float("Payments/Credits")
    c_partner_id = fields.Many2one('res.partner', string='Customer')
    c_balance_due_amount = fields.Float("Balance")
    c_amount_total = fields.Float("Invoices/Debits")
    company_id = fields.Many2one('res.company', string='Company')
    currency_id = fields.Many2one(related='c_invoice_id.currency_id')
    c_payment_id = fields.Many2one('account.payment', string='Payment')
    c_amount_residual = fields.Monetary(related='c_invoice_id.amount_residual')
    c_amount_residual_signed = fields.Monetary(related='c_invoice_id.amount_residual_signed',
                                               currency_field='currency_id', )
    c_state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled')
    ], string='State', readonly=True, copy=False, required=True,
        default='draft')
    payment_state = fields.Selection(PAYMENT_STATE_SELECTION, string="Payment Status",
                                     readonly=True, copy=False, tracking=True)
    transaction_ids = fields.Many2many(
        string="Transactions", comodel_name='payment.transaction',
        relation='account_invoice_custom_transaction_rel', column1='invoice_id', column2='transaction_id',
        readonly=True, copy=False)
    move_type = fields.Selection(selection=[
        ('entry', 'Journal Entry'),
        ('out_invoice', 'Customer Invoice'),
        ('out_refund', 'Customer Credit Note'),
        ('in_invoice', 'Vendor Bill'),
        ('in_refund', 'Vendor Credit Note'),
        ('out_receipt', 'Sales Receipt'),
        ('in_receipt', 'Purchase Receipt'),
    ], string='Type', required=True, store=True, index=True, readonly=True, tracking=True,
        default="entry", change_default=True)
