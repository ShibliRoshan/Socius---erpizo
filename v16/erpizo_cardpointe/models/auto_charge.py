"""Inherit PaymentProvider"""
# -*- coding: utf-8 -*-


from odoo import fields, models, _, api
from odoo.exceptions import ValidationError




class ErpizoAutoCharge(models.Model):
    """Erpizo Auto Charge"""
    _name = "erpizo.auto.charge"
    _rec_name = "id"
    _description = 'Erpizo Auto Charge'
    _check_company_auto = True

    max_charge_amount = fields.Float(string='Maximum CC Charge amount',
                                     default=1.0,
                                     required=True,
                                     store=True)

    @api.constrains('max_charge_amount')
    def _check_payment_amount(self):
        for record in self:
            if not (1 <= record.max_charge_amount <= 50000):
                raise ValidationError("The amount must be between 1 and 50,"
                                      "000.")