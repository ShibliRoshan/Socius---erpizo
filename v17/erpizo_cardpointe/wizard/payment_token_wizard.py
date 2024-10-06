# -*- coding: utf-8 -*-

from base64 import b64encode
import logging
import json
import requests
from datetime import date
from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError

class PaymentTokenWizard(models.TransientModel):
    _name = 'payment.token.wizard'
    _description = 'Payment Token Selection Wizard'

    token_id = fields.Many2one(
        comodel_name='payment.token',
        string='Payment Token',
        required=True
    )
    partner_id = fields.Many2one('res.partner', string='Partner')

    def action_confirm(self):
        self.ensure_one()
        # Add your logic here. For example, link the selected tokens to the related record.
        # Example: self.env['your.model'].browse(self._context.get('active_ids')).write({'token_ids': [(6, 0, self.token_ids.ids)]})

        provider_id = self.token_id.provider_id
        headers = {
            "Content-Type": "application/json",
            "Authorization": self.basic_auth(provider_id.username,
                                             provider_id.password),
        }
        api_url_template = "https://{site}.cardconnect.com/cardconnect/rest/auth"

        site = provider_id.site.replace("-uat",
                                        "") if provider_id.state == 'enabled' else provider_id.site + "-uat"
        inbound_url = api_url_template.format(site=site)

        if provider_id.state not in ["test", "enabled"]:
            raise UserError("The payment provider is disabled")

        payload = self.partner_id._prepare_payload(provider_id, self.token_id)
        response = self.partner_id._make_request(inbound_url, payload, headers)
        return self.partner_id._handle_response(response, self.token_id)

    def basic_auth(self, username, password):
        """Generate Basic Authentication token."""
        token = b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        return f"Basic {token}"