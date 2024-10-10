"""Inherit PaymentTransaction"""
# -*- coding: utf-8 -*-

import logging
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
from odoo import _, models


_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    """Payment transaction"""

    _inherit = "payment.transaction"

    def _process_notification_data(self, notification_data):
        """Override of payment to process the transaction based on cardpointe
        data."""
        super()._process_notification_data(notification_data)
        fee_percentage = self.env['payment.provider'].sudo().search([('code','=','cardpointe')], limit=1).fee_percentage
        if self.provider_code != "cardpointe":
            return

        if "respstat" in notification_data:
            status = notification_data.get("respcode")
            self.provider_reference = notification_data.get("data").get(
                "token"
            )
        else:
            status = notification_data.get("respcode")
            self.provider_reference = notification_data.get("data").get(
                "token"
            )

        if status in ("000", "00"):
            existing_token = self.env["payment.token"].search(
                [
                    ("provider_id", "=", self.provider_id.id),
                    ("partner_id", "=", self.partner_id.id),
                    (
                        "provider_ref",
                        "=",
                        notification_data.get("data").get("token"),
                    ),
                ]
            )
            if self.tokenize and existing_token:
                raise ValidationError(_("Payment method already saved.\n"
                                        "Please save another payment method"))
            if (
                self.tokenize
                and (notification_data.get("data").get("token") or notification_data.get("token"))
                and not existing_token
            ):
                self._cardpointe_tokenize_from_feedback_data(notification_data)
            if self.provider_id.is_payment_fee:
                if notification_data.get("data").get("flow") == 'token':
                    payment_mode = self.token_id.payment_mode
                else:
                    payment_mode = notification_data.get("data").get("payment_mode")

                if self.sale_order_ids and payment_mode != 'ach':
                    for sale_order in self.sale_order_ids:
                        if existing_token or payment_mode != 'ach':
                            order_line = self.env["sale.order.line"].create(
                                {
                                    "order_id": sale_order.id,
                                    "product_id": (self.provider_id.
                                                   payment_fee_product_id.id),
                                    "qty_invoiced": 1,
                                    "price_unit": self.amount * fee_percentage,
                                    "tax_id": False
                                }
                            )
                            self.amount += self.amount * fee_percentage
                            sale_order.write(
                                {"order_line": [(4, order_line.id)]}
                            )
                else:
                    if self.invoice_ids and payment_mode != 'ach':
                        for move in self.invoice_ids:
                            move_line_data = {
                                "move_id": move.id,
                                "product_id": self.provider_id.payment_fee_product_id.id,
                                "quantity": 1,
                                "price_unit": self.amount * fee_percentage,
                                "tax_ids": False,
                            }
                            move_line = self.env["account.move.line"].sudo().create(move_line_data)
                            move.narration = ("\n\nA " + str(fee_percentage * 100) + "% Credit Card "
                                                                                           "Processing "
                                                                                           "Fee was added to the total of "
                                                                                           "the invoice."
                                                                                           "Original invoice total: " + str(
                            self.amount) + " New invoice total: " + str(self.amount +(self.amount * fee_percentage)))
                            move.sudo().write({"invoice_line_ids": [(4, move_line.id)]})
                            if move.invoice_origin:
                                so = self.env['sale.order'].search([('name', '=', move.invoice_origin)], limit=1)
                                if so:
                                    order_line = self.env["sale.order.line"].create({
                                        "order_id": so.id,
                                        "product_id": self.provider_id.payment_fee_product_id.id,
                                        "qty_invoiced": 1,
                                        "price_unit": self.amount * fee_percentage,
                                    })
                                    self.amount += self.amount * fee_percentage
                                    so.write({"order_line": [(4, order_line.id)]})

            self._set_done()
            self.cardpointe_ref = notification_data.get("retref")
            if self.token_id and not self.token_id.cardpointe_ret_reference:
                self.token_id.cardpointe_ret_reference = notification_data.get("retref")
            return request.redirect("/payment/status")
        else:
            if status == 400:
                raise UserError(
                    _(
                        "The server was unable to decipher the request because"
                        "of invalid syntax."
                        "Please verify that the Merchant ID, Username, "
                        "Password, and Site information"
                        "provided in the configuration are correct"
                    )
                )
            if status == 401:
                raise UserError(
                    _(
                        "The credentials passed in the request were not "
                        "accepted by the server."
                        "Please verify that the Merchant ID, Username, "
                        "Password, and Site information"
                        "provided in the configuration are correct"
                    )
                )
            if status == 404:
                raise UserError(
                    _(
                        "The endpoint URL path specified in the request was "
                        "incorrect."
                    )
                )
            if status == 500:
                raise UserError(
                    _(
                        "The host server encountered an issue and was unable "
                        "to send a response."
                    )
                )
            else:
                failure = status

            self._set_error(_("The payment encountered an error, %s", failure))
