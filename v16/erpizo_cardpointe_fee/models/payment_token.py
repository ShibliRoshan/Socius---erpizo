"""Inherit PaymentProvider"""
# -*- coding: utf-8 -*-
from odoo import fields, models


class PaymentToken(models.Model):
    """Inherit PaymentToken"""

    _inherit = "payment.token"

    add_fee = fields.Boolean(default=True, string="Add fee",readonly=False)

