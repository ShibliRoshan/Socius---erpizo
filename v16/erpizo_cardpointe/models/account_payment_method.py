"""Inherit AccountPaymentMethod"""
# -*- coding: utf-8 -*-

from odoo import api, models


class AccountPaymentMethod(models.Model):
    """Inherit AccountPaymentMethod"""

    _inherit = "account.payment.method"

    @api.model
    def _get_payment_method_information(self):
        """
        Override method to extend payment method information.
        """
        res = super()._get_payment_method_information()
        res["cardpointe"] = {
            "mode": "unique",
            "domain": [("type", "=", "bank")],
        }
        return res
