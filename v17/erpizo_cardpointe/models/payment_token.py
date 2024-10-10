"""Inherit PaymentProvider"""
# -*- coding: utf-8 -*-

from base64 import b64encode
import logging
import json
import requests
from odoo import fields, models, _
from odoo.exceptions import ValidationError,UserError

_logger = logging.getLogger(__name__)


class PaymentToken(models.Model):
    """Inherit PaymentToken"""

    _inherit = "payment.token"

    masked_provider_ref = fields.Char(compute="compute_masked_provider_ref",string="Provider Reference")

    cvv = fields.Char(
        "CVV",
        help="Stored only last four digit for re-use in " "next transaction",
        store=True
    )
    expyear = fields.Char("Expiration Year", store=True)
    routing_number = fields.Char("Routing Number", store=True)
    payment_mode = fields.Char("Payment Mode", store=True)
    card_number = fields.Char("Card/Account Number", store=True)
    cardpointe_ret_reference = fields.Char("Cardpointe Retref", store=True)
    temp_charge_refunded = fields.Boolean(default=False, store=True,
                                          string="Charged Amount Refunded")

    def compute_masked_provider_ref(self):
       for rec in self:
           if rec.provider_ref:
               rec.masked_provider_ref = (
                    "*" * (len(rec.provider_ref) - 4)
                    + rec.provider_ref[-4:]
                )
           else:
               rec.masked_provider_ref = False

    # def refund_token_amount(self):
    #     if not self.temp_charge_refunded:
    #         _logger.info(
    #             "Initiating the refund for temporary charge of $1")
    #
    #         api_url_template = "https://{site}.cardconnect.com/cardconnect/rest/auth"
    #         if self.provider_id.state != 'enabled':
    #             if "-uat" not in self.provider_id.site:
    #                 site = self.provider_id.site + "-uat"
    #             else:
    #                 site = self.provider_id.site
    #         else:
    #             site = self.provider_id.site.replace("-uat", "")
    #
    #         api_url = api_url_template.format(site=site)
    #
    #         headers = {
    #             "Content-Type": "application/json",
    #             "Authorization": self.basic_auth(
    #                 self.provider_id.username, self.provider_id.password
    #             ),
    #         }
    #         tokenized_account_number = self._get_tokenized_account_number(
    #             self.card_number, self.provider_id)
    #         cc_expiry = self.expyear.replace(" ", "").replace("/", "")
    #
    #         payload = {
    #             "merchid": str(self.provider_id.merchant_id),
    #             "account": tokenized_account_number,
    #             "expiry": cc_expiry,
    #             "amount": 0.00,
    #             "currency": "USD" or self.env.company.currency_id.name,
    #             "name": self.partner_id.name,
    #         }
    #         response = requests.post(api_url, json=payload, headers=headers)
    #         json_data = response.json()
    #         if response.status_code == 200 and json_data.get("respstat") == "A":
    #             self.temp_charge_refunded = True
    #             _logger.info(
    #                 "The refund for temporary charge of $1 is completed successfully")
    #             _logger.info("Response of the refund of $1 charge processing with data:\n%s",
    #                          json.dumps(json_data, indent=4))
    #         else:
    #             raise ValidationError(
    #                 _(
    #                     "The Refund service failed due to the following "
    #                     "error. %s.",
    #                     json_data['resptext'],
    #                 )
    #             )
    #
    #         return
    #
    # def basic_auth(self, username, password):
    #     """
    #     Generate Basic Authentication token.
    #     """
    #     token = b64encode(f"{username}:{password}".encode("utf-8")).decode(
    #         "ascii"
    #     )
    #     return f"Basic {token}"
    #
    #
    # def _get_tokenized_account_number(self, account_number, provider_id):
    #     """
    #     Tokenize the account number.
    #     """
    #     api_url_template = "https://{site}.cardconnect.com/cardsecure/api/v1/ccn/tokenize"
    #     if provider_id.state != 'enabled':
    #         if "-uat" not in provider_id.site:
    #             site = provider_id.site + "-uat"
    #         else:
    #             site = provider_id.site
    #     else:
    #         site = provider_id.site.replace("-uat", "")
    #
    #     api_url = api_url_template.format(site=site)
    #     headers = {"Content-Type": "application/json"}
    #     data = {"account": account_number}
    #
    #     response = requests.post(api_url, json=data, headers=headers)
    #     if response.status_code == 200:
    #         return response.json().get("token", "")
    #     else:
    #         raise UserError(_("Tokenization failed with status code %s. Check the card", response.text))
    #
