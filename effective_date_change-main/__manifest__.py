# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Change Effective Date',
    'author': 'Altela Softwares',
    'version': '15.0.0.8.0',
    'summary': 'Change Effective Date in Stock Picking',
    'license': 'OPL-1',
    'sequence': 1,
    'description': """Allows You Changing Effective Date of DO, RO, Internal and All Inventory Transfers""",
    'category': 'Inventory',
    'website': 'https://www.altela.net',
    'price':'25',
    'currency':'USD',
    'depends': [
        'stock',
        'account',
        'sale_management',
        'mrp',
        'mrp_account'
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/effective_date_change.xml',
        'wizard/change_effective_wizard_views.xml',

    ],
    'images': [
        'static/description/assets/banner.gif',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'pre_init_hook': 'pre_init_check',
}
