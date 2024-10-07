{
    "name": "Erpizo Pay Fee",
    "summary": """Additional Card Fee for Erpizo Pay Payment Provider""",
    "description": """Additional Card Fee for Erpizo Pay Payment Provider""",
    "license": "Other proprietary",
    "author": "Erpizo",
    "website": "",
    "category": "Accounting/Payment",
    "version": "16.0.1.0.0",
    "depends": ["erpizo_cardpointe", "product", "website", "website_sale",
                "account"],
    "data": [
        "views/payment_provider_view.xml",
        "views/payment_token_view.xml",
        "views/templates.xml",
        "wizard/account_payment_register_views.xml",
        "data/account_data.xml",
        "data/payment_fee_data.xml",

    ],
    "assets": {
        "web.assets_frontend": [
            "erpizo_cardpointe_fee/static/src/js/payment_fee.js",
        ]
    },
    "installable": True,
    "uninstall_hook": "",
}
