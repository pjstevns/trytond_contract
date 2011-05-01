#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
{
    'name': 'Recurrent invoicing contracts',
    'name_nl_NL': 'Factureren van periodieke contracten',
    'version': '2.0.0',
    'author': 'NFG',
    'email': 'info@nfg.nl',
    'website': 'http://www.nfg.nl/',
    'description': '''Generate recurring invoices based on agreements.
''',
    'xml': [
        'contract.xml',
        'party.xml',
        'invoice.xml',
        'configuration.xml',
    ],
    'depends': [
        'account',
        'account_invoice',
        'product',
        'company',
        'party',
        'currency',
    ],
}
