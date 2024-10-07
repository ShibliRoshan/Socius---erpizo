"""Inherit AccountMoveLine"""
# -*- coding: utf-8 -*-

from base64 import b64encode
import logging
import requests
from odoo import models, fields, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    """Account Move Line"""

    _inherit = "account.move.line"

    block_charge = fields.Boolean(
        string='Exclude from Next Charge Cycle',
        default=False
    )

    def action_register_payment(self):
        ''' Open the account.payment.register wizard to pay the selected journal items.
        :return: An action opening the account.payment.register wizard.
        '''
        cardpointe_journal_id = self.env['account.journal'].search([
            ('code', '=', 'Cardpointe')], limit=1)

        if cardpointe_journal_id:
            if self.move_id.type_name == 'Vendor Bill':
                return {
                    'name': _('Register Payment'),
                    'res_model': 'account.payment.register',
                    'view_mode': 'form',
                    'views': [[False, 'form']],
                    'context': {
                        'active_model': 'account.move.line',
                        'active_ids': self.ids,
                    },
                    'target': 'new',
                    'type': 'ir.actions.act_window',
                }
            else:
                return {
                    'name': _('Register Payment'),
                    'res_model': 'account.payment.register',
                    'view_mode': 'form',
                    'views': [[False, 'form']],
                    'context': {
                        'active_model': 'account.move.line',
                        'active_ids': self.ids,
                        'default_journal_id': self.env['account.journal'].search(
                            [('code', '=', 'Cardpointe')], limit=1).id,
                        'default_payment_method_line_id': self.env['account.payment.method.line'].search(
                            [('name', '=', 'Erpizo Pay')], limit=1).id,

                    },
                    'target': 'new',
                    'type': 'ir.actions.act_window',
                }
        else:
            return super().action_register_payment()
