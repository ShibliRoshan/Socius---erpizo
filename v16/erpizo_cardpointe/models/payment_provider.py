"""Inherit PaymentProvider"""
# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.addons.erpizo_cardpointe import const


TIMEOUT = 60


class PaymentProviderCardpointe(models.Model):
    """Inherit PaymentProvider"""
    _inherit = "payment.provider"

    code = fields.Selection(
        selection_add=[("cardpointe", "Cardpointe")],
        ondelete={"cardpointe": "set default"},
    )
    username = fields.Char("Username")
    password = fields.Char("Password")
    site = fields.Char("Site")
    merchant_id = fields.Char("Merchant ID")

    def _compute_feature_support_fields(self):
        """ Override of `payment` to enable additional features. """
        super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == 'cardpointe').update({
            'support_tokenization': True,
        })

    def _get_default_payment_method_id(self, code):
        """Returns the default payment method"""
        self.ensure_one()
        if self.code != "cardpointe":
            return super()._get_default_payment_method_id(code)
        return self.env.ref("erpizo_cardpointe.payment_method_cardpointe").id

    def _get_compatible_providers(self, *args, **kwargs):
        """ Override of `payment` to filter cardpointe providers for validation operations. """
        providers = super()._get_compatible_providers(*args, **kwargs)
        return providers



    def _get_default_payment_method_codes(self):
        """ Override of `payment` to return the default payment method codes. """
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'cardpointe':
            return default_codes
        return const.DEFAULT_PAYMENT_METHODS_CODES