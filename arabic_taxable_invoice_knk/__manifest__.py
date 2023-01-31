# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

{
    "name": "Arabic Taxable Invoice",
    "version": "16.0.1.0",
    "summary": "Arabic Taxable Invoice Module is the Invoice Receipt Layout which is printed in english as well as Arabic language to ensure customer's ease of readability and displays content in proper format ready to use for commercial purpose | Invoice Report | qweb report | Taxable Invoice | invoice report | arabic invoice report | Arabic Invoice | arabic invoice",
    "description": """
        Arabic Taxable Invoice Module is the Invoice Receipt Layout which is printed in english as well as Arabic language to ensure customer's ease of readability and displays content in proper format ready to use for commercial purpose.
    """,
    "author": "Kanak Infosystems LLP.",
    "website": "https://www.kanakinfosystems.com",
    "category": "Accounting/Accounting",
    "depends": ["account"],
    "data": [
        "data/report_paperformat.xml",
        "report/account_report.xml",
        "views/invoice_report.xml",
        "views/invoice_view.xml",
        "views/res_company.xml",
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'OPL-1',
    'installable': True,
    'application': True,
    'auto_install': False,
}
