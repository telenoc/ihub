# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Sitaram Solutions (<https://sitaramsolutions.in/>).
#
#    For Module Support : info@sitaramsolutions.in  or Skype : contact.hiren1188
#
##############################################################################

{
    'name': 'Partial Customer Invoices and Vendor Bills Payment Reconciliation',
    'version': '15.0.0.0',
    'category': 'Accounting',
    "license": "OPL-1",
    'summary': 'partial vendor bills payment vendor bills partial reconciliation partial reconciliation partial payment reconciliation vendor partial bills payment reconciliation vendor payment partial reconciliation multiple vendor bills partial reconciliation multiple partial reconciliation partial invoice payment invoice partial reconciliation partial reconciliation partial payment reconciliation customer partial invoice payment reconciliation customer payment partial reconciliation multiple invoice partial reconciliation multiple partial reconcilation',
    'description': """
    partial vendor bills payment
        vendor invoices partial reconciliation
        vendor bills partial reconciliation
        vendor partial payment reconciliation
        partial reconciliation payment
        partial reconciliation vendor bills payment
        multiple vendor bills partial reconciliation
        multiple vendor bills reconciliation
        multiple vendor bills payment reconciliation
        single vendor bills reconciliation
        single payment reconciliation with multiple bills
        partial payment
        vendor payment partial reconciliation
        partial reconciliation from outstanding payment
        partial reconciliation from payment
        vendor partial bills payment from vendor payment
        vendor bills reconciliation
        vendor payment reconciliation
        bills reconciliation form outstanding payment
        check outstanding balance
        check debit
        check credit
        check remaining outstanding balance
        vendor pay partially from outstanding balance
        pay partially
        partially pay bills amount
        partially pay multiple vendor bills
        partial invoice payment
        invoice partial reconciliation
        customer invoice partial reconciliation
        customer partial payment reconciliation
        partial reconciliation payment
        partial reconciliation invoice payment
        multiple invoice partial reconciliation
        multiple invoice reconciliation
        multiple invoice payment reconciliation
        single invoice reconciliation
        single payment reconciliation with multiple invoices
        partial payment
        customer payment partial reconciliation
        partial reconciliation from outstanding payment
        partial reconciliation from payment
        customer partial invoice payment from customer payment
        customer invoice reconciliation
        customer payment reconciliation
        invoice reconciliation form outstanding payment
        check outstanding balance
        check debit
        check credit
        check remaining outstanding balance
        customer pay partially from outstanding balance
        pay partially
        partially pay invoice amount
        partially pay multiple invoice

""",
    "price": 60,
    "currency": 'EUR',
    'author': 'Sitaram',
    'depends': ['account'],
    "data": [
        "data/partial_matching_number_data.xml",
        "security/ir.model.access.csv",
        # "views/inherited_account_move_view.xml",
        # "views/inherited_account_payment_view.xml",
        "wizard/partial_payment_view.xml",
        "wizard/partial_multi_payment_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "/sr_partial_bill_invoice_payment/static/src/js/inherited_account_payment_field.js",
        ],
    },
    'website':'https://sitaramsolutions.in',
    'installable': True,
    'auto_install': False,
    'live_test_url':'https://youtu.be/pOzD2zT8Luk',
    "images":['static/description/banner.png'],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
