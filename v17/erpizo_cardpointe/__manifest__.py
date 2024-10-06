{
    "name": "Erpizo Pay",
    "summary": """Erpizo Pay""",
    "description": """Erpizo Pay Payment Provider""",
    "license": "Other proprietary",
    "author": "Erpizo",
    "website": "",
    "category": "Accounting/Payment",
    "version": "17.0.1.0.0",
    "depends": ["payment", "account_payment", "account", "account_followup"],
    "data": [
        "security/ir.model.access.csv",
        "views/payment_provider_view.xml",
        "views/payment_views.xml",
        "views/account_move_view.xml",
        "views/payment_transaction_view.xml",
        "views/payment_token_view.xml",
        # "views/auto_charge_views.xml",
        "views/account_followup_views.xml",
        "views/account_move_line_view.xml",
        'views/res_config_settings_views.xml',
        "wizard/account_payment_register_views.xml",
        "wizard/payment_token_wizard_views.xml",

        "data/payment_provider_data.xml",
        "data/account_journal.xml",
        # "data/mail_template_data.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "erpizo_cardpointe/static/src/scss/payment_cardpointe.scss",
            "erpizo_cardpointe/static/lib/cardpointe_jquery.payment/"
            "jquery.payment.js",
            "erpizo_cardpointe/static/src/js/payment_form.js",
        ]
    },
    "installable": True,
    'post_init_hook': 'post_init_hook',
    "uninstall_hook": "uninstall_hook",
}

