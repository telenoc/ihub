# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Sale Order Automation',
    'version' : '1.0',
    'author':'Craftsync Technologies',
    'category': 'Sales',
    'maintainer': 'Craftsync Technologies',
    'summary': """Enable auto sale workflow with sale order confirmation. Include operations like Auto Create Invoice, Auto Validate Invoice and Auto Transfer Delivery Order.""",
    'description': """

        You can directly create invoice and set done to delivery order by single click

    """,
    'website': 'https://www.craftsync.com/',
    'license': 'LGPL-3',
    'support':'info@craftsync.com',
    'depends' : ['sale_management', 'stock'],
    'data': [
        'reports/sale_report_inherit.xml',
        'reports/invoice_reprot_inherit.xml',
        'views/stock_warehouse.xml',
        'views/sale_order.xml',
        'views/account_move.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'images': ['static/description/main_screen.png'],

}
