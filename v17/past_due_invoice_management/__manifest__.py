# -*- coding: utf-8 -*-
{
    'name': "Past due invoice management",
    'summary': 'Past due invoice management',
    'description': """
        invoice management    
        """,
    'author': "Erpizo",
    'website': "",
    'version': '0.1',
    'depends': ['base', 'mail', 'sale_management', 'purchase', 'account','account_payment'],
    'data': [
        'security/ir.model.access.csv',
        'data/overdue_invoices_mail_template.xml',
        'views/account_move.xml',
        'views/template.xml',
        # 'wizard/confirmation.xml',
        'wizard/past_due_invoices_wizard.xml',

    ],
    'installable': True,

}
