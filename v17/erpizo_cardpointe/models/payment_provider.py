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


    @api.depends('code')
    def _compute_view_configuration_fields(self):
        """ Override of payment to hide the credentials page.

        :return: None
        """
        super()._compute_view_configuration_fields()
        self.filtered(lambda p: p.code == 'cardpointe').update({
            'show_credentials_page': True,
            'show_allow_tokenization': True,
        })


    def _compute_feature_support_fields(self):
        """ Override of `payment` to enable additional features. """
        super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == 'cardpointe').update({
            'support_express_checkout': True,
            'support_manual_capture': 'partial',
            'support_refund': 'partial',
            'support_tokenization': True,
        })

    def _get_default_payment_method_id(self, code):
        """Returns the default payment method"""
        self.ensure_one()
        if self.code != "cardpointe":
            return super()._get_default_payment_method_id(code)
        return self.env.ref("erpizo_cardpointe.payment_method_cardpointe").id

    def _get_default_payment_method_codes(self):
        """ Override of `payment` to return the default payment method codes. """
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'cardpointe':
            return default_codes
        return const.DEFAULT_PAYMENT_METHODS_CODES