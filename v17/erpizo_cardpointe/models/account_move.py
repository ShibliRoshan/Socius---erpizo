"""Inherit AccountMove"""
# -*- coding: utf-8 -*-

from base64 import b64encode
import logging
import requests
from odoo import models, fields, _, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    """Account Move"""

    _inherit = "account.move"

    cardpointe_ref = fields.Char(store=True, copy=False)
    cardpointe_refund_ref = fields.Char(store=True)
    cancel_btn = fields.Boolean(compute="_compute_cancel_visibility")

    def _compute_cancel_visibility(self):
        """
        Computes the visibility if cancel payment button in invoice form view.
        If the payment is done with erpizo pay cancel button will be visible else invisible
        """
        for rec in self:
            rec.cancel_btn = False
            if rec.state == 'posted':
                transaction = False
                transactions = rec.transaction_ids
                for trans in transactions:
                    if trans.payment_id != False:
                        transaction = trans
                if transaction and transaction.payment_method_code == 'cardpointe':
                    rec.cancel_btn = True
                else:
                    rec.cancel_btn = False
            else:
                rec.cancel_btn = False

    def _compute_cardpointe_ref(self):
        """
        Compute cardpointe_ref based on payment transactions associated with
        invoices.
        """
        for rec in self:
            transaction = (
                self.env["payment.transaction"]
                .search(
                    [("invoice_ids", "in", self.ids), ("state", "=", "done")],
                    limit=1,
                )
                .filtered(lambda x: x.provider_id.code == "cardpointe")
            )
            if transaction and transaction.cardpointe_ref:
                rec.cardpointe_ref = transaction.cardpointe_ref
            else:
                rec.cardpointe_ref = ""

    def button_inquire_refund(self):
        """
        Button action to inquire about a refund for a transaction.
        """
        if self.invoice_payments_widget:
            payment_id = self.env["account.payment"].browse(
                self.invoice_payments_widget["content"][0][
                    "account_payment_id"
                ]
            )
            provider_id = (
                payment_id.payment_method_line_id.payment_provider_id
                if payment_id and payment_id.payment_method_line_id
                else False
            )
            if provider_id:

                api_url_template = "https://{site}.cardconnect.com/cardconnect/rest/inquire/"+self.cardpointe_ref+"/"+ provider_id.merchant_id
                if provider_id.state != 'enabled':
                    if "-uat" not in provider_id.site:
                        site = provider_id.site + "-uat"
                    else:
                        site = provider_id.site
                else:
                    site = provider_id.site.replace("-uat", "")

                api_url = api_url_template.format(site=site)
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": self.basic_auth(
                        provider_id.username, provider_id.password
                    ),
                }

                response = requests.get(api_url, headers=headers)

                if response.status_code == 200:
                    json_data = response.json()
                    if json_data.get("refundable") == "N":
                        raise ValidationError(
                            _(
                                "The refund for this transaction is not "
                                "available"
                            )
                        )
                    else:
                        raise ValidationError(
                            _("The refund for this transaction is available")
                        )
                else:
                    raise ValidationError(
                        _(
                            "The request failed due to the following "
                            "reasons %s",
                            response.text,
                        )
                    )
        else:
            raise ValidationError(_("Please complete the payment first"))

    def button_cancel_payment(self):
        """
        Button action to cancel a payment.
        """
        payment_id = self.env["account.payment"].browse(
            self.invoice_payments_widget["content"][0]["account_payment_id"]
        )
        provider_id = (
            payment_id.payment_method_line_id.payment_provider_id
            if payment_id and payment_id.payment_method_line_id
            else False
        )
        if provider_id:
            api_url_template = "https://{site}.cardconnect.com/cardconnect/rest/void"
            if provider_id.state != 'enabled':
                if "-uat" not in provider_id.site:
                    site = provider_id.site + "-uat"
                else:
                    site = provider_id.site
            else:
                site = provider_id.site.replace("-uat", "")

            api_url = api_url_template.format(site=site)
            headers = {
                "Content-Type": "application/json",
                "Authorization": self.basic_auth(
                    provider_id.username, provider_id.password
                ),
            }
            data = {
                "retref": self.cardpointe_ref,
                "merchid": str(provider_id.merchant_id),
            }

            response = requests.post(api_url, json=data, headers=headers)
            if response.status_code == 200:
                self.button_draft()
                self.button_cancel()
                payment_id.action_draft()
                payment_id.action_cancel()
            else:
                raise ValidationError(
                    _(
                        "The Payment service failed due to the following "
                        "error. Tokenization failed with status code %s. Check"
                        "the card",
                        response.text,
                    )
                )

    def basic_auth(self, username, password):
        """
        Generate Basic Authentication token.
        """
        token = b64encode(f"{username}:{password}".encode("utf-8")).decode(
            "ascii"
        )
        return f"Basic {token}"

