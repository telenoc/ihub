from odoo import fields, models, _

PAYMENT_STATE_SELECTION = [
    ('not_paid', 'Not Paid'),
    ('in_payment', 'In Payment'),
    ('paid', 'Paid'),
    ('partial', 'Partially Paid'),
    ('reversed', 'Reversed'),
    ('invoicing_legacy', 'Invoicing App Legacy'),
]


class FilterDataLine(models.Model):
    _name = 'filter.data.line'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Filter Data Line"
    _order = 'invoice_date'

    invoice_id = fields.Many2one('account.move', string='Invoice')
    reference = fields.Char('Name')
    invoice_date = fields.Date('Invoice Date')
    due_invoice_date = fields.Date('Due Date')
    amount_total_signed = fields.Monetary(related='invoice_id.amount_total_signed', currency_field='currency_id', )
    credit_payment = fields.Float("Payments/Credits")
    partner_id = fields.Many2one('res.partner', string='Customer')
    balance_due_amount = fields.Float("Balance")
    amount_total = fields.Float("Invoices/Debits")
    company_id = fields.Many2one('res.company', string='Company')
    currency_id = fields.Many2one(related='invoice_id.currency_id')
    payment_id = fields.Many2one('account.payment', string='Payment')
    amount_residual = fields.Monetary(related='invoice_id.amount_residual')
    amount_residual_signed = fields.Monetary(related='invoice_id.amount_residual_signed',
                                             currency_field='currency_id', )
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled')
    ], string='State', readonly=True, copy=False, required=True,
        default='draft')
    payment_state = fields.Selection(PAYMENT_STATE_SELECTION, string="Payment Status",
                                     readonly=True, copy=False, tracking=True)
    transaction_ids = fields.Many2many(
        string="Transactions", comodel_name='payment.transaction',
        relation='account_invoice_filter_transaction_rel', column1='invoice_id', column2='transaction_id',
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


class SupplierFilterDataLine(models.Model):
    _name = 'filter.supplier.data.line'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Supplier Filter Data Line"
    _order = 'invoice_date'

    invoice_id = fields.Many2one('account.move', string='Invoice')
    reference = fields.Char('Name')
    invoice_date = fields.Date('Invoice Date')
    due_invoice_date = fields.Date('Due Date')
    amount_total_signed = fields.Monetary(related='invoice_id.amount_total_signed', currency_field='currency_id', )
    credit_payment = fields.Float("Payments/Credits")
    partner_id = fields.Many2one('res.partner', string='Customer')
    balance_due_amount = fields.Float("Balance")
    amount_total = fields.Float("Invoices/Debits")
    company_id = fields.Many2one('res.company', string='Company')
    currency_id = fields.Many2one(related='invoice_id.currency_id')
    payment_id = fields.Many2one('account.payment', string='Payment')
    amount_residual = fields.Monetary(related='invoice_id.amount_residual')
    amount_residual_signed = fields.Monetary(related='invoice_id.amount_residual_signed',
                                             currency_field='currency_id', )
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled')
    ], string='State', readonly=True, copy=False, required=True,
        default='draft')

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
