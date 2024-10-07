"""Inherit PaymentProvider"""
# -*- coding: utf-8 -*-
from odoo import models, fields

TIMEOUT = 60


class PaymentProviderCardpointe(models.Model):
    """Inherit PaymentProvider"""

    _inherit = "payment.provider"

    is_payment_fee = fields.Boolean("Payment Fee", default=False)
    payment_fee_product_id = fields.Many2one(
        "product.product", string="Payment Fee Product"
    )
    fee_percentage = fields.Float('Fee Percentage')
