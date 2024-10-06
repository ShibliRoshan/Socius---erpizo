"""Inherit PaymentTransaction"""
# -*- coding: utf-8 -*-

import logging
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
from odoo import _, api, models, fields
import requests
import json
from base64 import b64encode


_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    """Payment transaction"""

    _inherit = "payment.transaction"

    cardpointe_ref = fields.Char(store=True)

    def _get_specific_processing_values(self, processing_values):
        """Override of payment to return access token as provider-specific
        processing values."""
        res = super()._get_specific_processing_values(processing_values)
        if self.provider_code != "cardpointe":
            return res
        return processing_values

    @api.model
    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Override of payment to find the transaction based on cardpointe
        data."""
        tx = super()._get_tx_from_notification_data(provider_code,
                                                    notification_data)
        if provider_code != "cardpointe":
            return tx
        if notification_data.get('landingRoute'):
            reference = notification_data.get("reference")
            tx = self.search(
                [
                    ("reference", "=", reference),
                    ("provider_code", "=", "cardpointe"),
                ]
            )
            if not tx:
                raise ValidationError(
                    _("No transaction found matching reference %s.", reference)
                )
            tx.write({'state': 'done'})
            self._cardpointe_tokenize_from_data(notification_data)
            return tx
        else:
            reference = notification_data.get("data").get("reference")
            tx = self.search(
                [
                    ("reference", "=", reference),
                    ("provider_code", "=", "cardpointe"),
                ]
            )
            if not tx:
                raise ValidationError(
                    _("No transaction found matching reference %s.", reference)
                )
            return tx

    def _cardpointe_tokenize_from_data(self, notification_data):
        """Create a new token based on the feedback data."""
        masked_number = (
            "*" * (len(notification_data.get("token")) - 4)
            + notification_data.get("token")[-4:]
        )
        cc_expiry = notification_data.get("cc_expiry").replace(" ", "").replace("/", "") if notification_data.get(
            "cc_expiry") else None
        sudo_self = self.sudo()
        existing_token = self.env["payment.token"].search(
            [("provider_id", "=", notification_data.get('acquirer_id')),
                ("partner_id", "=", notification_data.get("partner_id")),
                ("provider_ref", "=", notification_data.get("token"))])
        if notification_data.get('tokenization_requested') and existing_token and notification_data.get("token"):
            raise ValidationError(_("Payment method already saved.\n"
                                    "Please save another payment method"))
        token_data = {
            "payment_details": masked_number,
            "payment_method_id": self.env["payment.method"].search([
                ("code","=", notification_data.get("data").get("paymentMethodCode"),)] ).id,
            "provider_id": notification_data.get("acquirer_id"),
            "partner_id": notification_data.get("partner_id"),
            "provider_ref": notification_data.get("token"),
            "card_number": notification_data.get("token") if notification_data.get("payment_mode") == "card" else notification_data.get("cc_number"),
            "payment_mode": notification_data.get("payment_mode"),
            "cvv": notification_data.get("cc_cvc"),
            "expyear": cc_expiry,
            "routing_number": (notification_data.get("routing_number")),
            "cardpointe_ret_reference": (notification_data.get("retref")),
        }
        token = self.env["payment.token"].sudo().create(token_data)
        self.sudo().write({"token_id": token.id, "tokenize": False})
        _logger.info(
            "Created token with id %s for partner with id %s",
            token.id,
            sudo_self.partner_id.id,
        )
        # if notification_data.get("payment_mode") == "card":
        #     token.refund_token_amount()

    def _cardpointe_tokenize_from_feedback_data(self, notification_data):
        """Create a new token based on the feedback data."""
        self.ensure_one()
        masked_number = (
            "*" * (len(notification_data.get("token")) - 4)
            + notification_data.get("token")[-4:]
        )
        existing_token = self.env["payment.token"].search(
            [("provider_id", "=", notification_data.get('acquirer_id')),
                ("partner_id", "=", notification_data.get("partner_id")),
                ("provider_ref", "=", notification_data.get("token"))])
        if self.tokenize and existing_token and notification_data.get("data").get("token"):
            raise ValidationError(_("Payment method already saved.\n"
                                    "Please save another payment method"))

        token_data = {
            "payment_details": masked_number,
            "payment_method_id": self.env["payment.method"].search([
                ("code","=", notification_data.get("data").get("paymentMethodCode"),)] ).id,
            "provider_id": self.provider_id.id,
            "partner_id": self.partner_id.id,
            "provider_ref": notification_data.get("data").get("token"),
            "card_number": notification_data.get("data").get("token"),
            "payment_mode": notification_data.get("data").get("payment_mode"),
            "cvv": notification_data.get("data").get("cc_cvc"),
            "expyear": notification_data.get("expiry"),
            "routing_number": (notification_data.get("data").get
                               ("routing_number")),
        }

        token = self.env["payment.token"].create(token_data)
        self.write({"token_id": token.id, "tokenize": False})
        _logger.info(
            "Created token with id %s for partner with id %s",
            token.id,
            self.partner_id.id,
        )
        if notification_data.get("data").get("payment_mode") == "card" and notification_data.get("data").get("tokenization_requested"):
            api_url_template = "https://{site}.cardconnect.com/cardconnect/rest/auth"
            if self.provider_id.state != 'enabled':
                if "-uat" not in self.provider_id.site:
                    site = self.provider_id.site + "-uat"
                else:
                    site = self.provider_id.site
            else:
                site = self.provider_id.site.replace("-uat", "")

            api_url = api_url_template.format(site=site)

            headers = {
                "Content-Type": "application/json",
                "Authorization": self.basic_auth(self.provider_id.username,
                                                 self.provider_id.password)
            }
            payload = {
                "merchid": str(self.provider_id.merchant_id),
                "account": notification_data.get("data").get("token"),
                "expiry": notification_data.get("expiry"),
                "amount": 0.00,
                "currency": "USD" or self.env.company.currency_id.name,
                "ecomind": "E",
                "tokenize": "Y",
                "cvv2": notification_data.get("data").get("cc_cvc"),
                "postal": self.partner_id.zip,
                "name": self.partner_id.name,
                "address": self.partner_id.street,
                "city": self.partner_id.city,
                "country": self.partner_id.country_code
            }
            response = requests.post(api_url, json=payload, headers=headers)
            if response.status_code == 200:
                json_data = response.json()
                if json_data.get("respstat") == "A":
                    _logger.info("Response of $0 charge processing with data:\n%s",
                                 json.dumps(json_data, indent=4))

                    # token.refund_token_amount()
                else:
                    raise UserError(
                        _("The $0 Payment failed due to the following error"))

    def basic_auth(self, username, password):
        """
        Generate Basic Authentication token.
        """
        token = b64encode(
            f"{username}:{password}".encode("utf-8")).decode(
            "ascii"
        )
        return f"Basic {token}"


class PaymentTransactions(models.Model):
    """The transaction model"""

    _inherit = "payment.transaction"

    def _create_payment(self, **extra_create_values):
        """Create an `account.payment` record for the current transaction."""
        self.ensure_one()

        payment_method_line = (
            self.provider_id.journal_id.inbound_payment_method_line_ids.
            filtered(
                lambda l: l.code == self.provider_code
            )
        )
        payment_values = {
            "amount": abs(self.amount),
            "payment_type": "inbound" if self.amount > 0 else "outbound",
            "currency_id": self.currency_id.id,
            "partner_id": self.partner_id.commercial_partner_id.id,
            "partner_type": "customer",
            "journal_id": self.provider_id.journal_id.id,
            "company_id": self.provider_id.company_id.id,
            "payment_method_line_id": payment_method_line.id,
            "payment_token_id": self.token_id.id,
            "payment_transaction_id": self.id,
            "ref": f"{self.reference} - {self.partner_id.name} "
            f'- {self.provider_reference or ""}',
            **extra_create_values,
        }
        payment = self.env["account.payment"].create(payment_values)
        payment.action_post()

        self.payment_id = payment

        if self.invoice_ids:
            self.invoice_ids.filtered(lambda inv: inv.state
                                      == "draft").action_post()
            for inv in self.invoice_ids:
                inv.cardpointe_ref = self.cardpointe_ref

            (payment.line_ids + self.invoice_ids.line_ids).filtered(
                lambda line: line.account_id == payment.destination_account_id
                and not line.reconciled
            ).reconcile()
        return payment
