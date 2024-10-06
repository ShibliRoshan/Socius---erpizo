# -*- coding: utf-8 -*-
"""
Describes fields that maps to Shopware Configuration
"""
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    """ Describes fields mapping to Max Charge Amount Configuration """
    _inherit = 'res.config.settings'

    max_charge_amount = fields.Float(string='Maximum CC Charge amount',
                                     default=1.0,
                                     required=True,
                                     store=True)

    def set_values(self):
        """
            Set values for the fields for Shopware Configuration
        """
        res = super(ResConfigSettings, self).set_values()
        (self.env['ir.config_parameter'].sudo().set_param
         ('erpizo_cardpointe.max_charge_amount', self.max_charge_amount))
        return res

    @api.model
    def get_values(self):
        """
            Return values for the fields for Shopware Configuration
        """
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            max_charge_amount=params. \
                get_param('erpizo_cardpointe.max_charge_amount'))
        return res

    @api.constrains('max_charge_amount')
    def _check_payment_amount(self):
        for record in self:
            if not (1 <= record.max_charge_amount <= 50000):
                raise ValidationError("The amount must be between 1 and 50,"
                                      "000.")