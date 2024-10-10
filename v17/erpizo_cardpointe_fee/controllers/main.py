"""Cardpointe"""

# -*- coding: utf-8 -*-

import logging
import json
from base64 import b64encode
from odoo import http, _
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
import requests
from odoo.addons.erpizo_cardpointe.controllers.main import CardpointeController

_logger = logging.getLogger(__name__)


class CardpointeControllers(CardpointeController):
    """Cardpointe controller"""

    _process_url = "/payment/cardpointe"

    @http.route(
        _process_url,
        type="json",
        auth="public",
        methods=["GET", "POST"],
        csrf=False,
    )
    def cardpointe_process_transaction(self, **data):
        """
        Process the Cardpointe transaction.
        """
        _logger.info("Handling custom processing with data:\n%s",
                     json.dumps(data, indent=4))

        provider_id = request.env["payment.provider"].sudo().browse(
            data.get("provider_id") or data.get("acquirer_id"))
        customer_id = request.env["res.partner"].sudo().browse(
            data.get("partner_id"))
        token_id = request.env["payment.token"].sudo().browse(
            data.get("tokenId"))
        process_values = request.env["payment.transaction"].sudo().search([(
            "reference",
            "=",
            data.get(
                "reference"))])._get_processing_values()

        api_url_template = "https://{site}.cardconnect.com/cardconnect/rest/auth"
        if provider_id.state != 'enabled':
            if "-uat" not in provider_id.site:
                site = provider_id.site + "-uat"
            else:
                site = provider_id.site
        else:
            site = provider_id.site.replace("-uat", "")

        api_url = api_url_template.format(site=site)

        if provider_id.state not in ["test", "enabled"]:
            raise UserError("The payment provider is disabled")

        headers = {
            "Content-Type": "application/json",
            "Authorization": self.basic_auth(provider_id.username,
                                             provider_id.password),
        }

        if data.get("flow") == "token":
            payload = self._prepare_token_payload(data, provider_id,
                                                  customer_id, token_id,
                                                  process_values)
        elif data.get("flow") == "direct" and data.get("landingRoute"):
            return self.create_portal_token(data)

        elif data.get("flow") == "direct" and not data.get("landingRoute"):
            payload = self._prepare_direct_payload(data, provider_id,
                                                   customer_id, process_values)
        else:
            raise UserError("Invalid flow specified")

        self._send_request(api_url, headers, payload, data)

    def create_portal_token(self, data):
        _logger.info("Handling payment method processing to save token by"
                     " temporary charge of $1 payment:\n%s",
                     json.dumps(data, indent=4))

        provider_id = request.env["payment.provider"].sudo().browse(
            data.get("provider_id") or data.get("acquirer_id")
        )
        customer_id = request.env["res.partner"].sudo().browse(
            data.get("partner_id"))

        process_values = request.env["payment.transaction"].sudo().search([
            ("reference", "=", data.get("reference"))
        ])._get_processing_values()
        process_values.update({'amount': 1.0})
        api_url_template = "https://{site}.cardconnect.com/cardconnect/rest/auth"
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
            "Authorization": self.basic_auth(provider_id.username,
                                             provider_id.password)
        }
        payload = self._prepare_payment_method_payload(data, provider_id, customer_id,
                                               process_values)
        self._send_request(api_url, headers, payload, data)
        return

    def _prepare_payment_method_payload(self, data, provider_id, customer_id, process_values):
        account_number = self._get_account_number(data)
        tokenized_account_number = self._get_tokenized_account_number(account_number, provider_id)
        cc_expiry = data.get("cc_expiry").replace(" ", "").replace("/", "") if data.get("cc_expiry") else None

        payload = {
            "merchid": str(provider_id.merchant_id),
            "account": tokenized_account_number,
            "expiry": cc_expiry,
            "amount": 0.01,
            "currency": "USD" or request.env.company.currency_id.name,
            "ecomind": "E",
            "tokenize": "Y",
            "orderid": data.get("reference"),
            "cvv2": data.get("cc_cvc"),
            "postal": customer_id.zip,
            "name": customer_id.name,
            "address": customer_id.street,
            "city": customer_id.city,
            "country": customer_id.country_code
        }

        if data.get("payment_mode") == "ach":
            payload["accttype"] = "ECHK"
            payload["achEntryCode"] = "WEB"

        return payload
    def _prepare_token_payload(self, data, provider_id, customer_id, token_id,
                               process_values):
        fee_percentage = request.env['payment.provider'].sudo().search([('code', '=', 'cardpointe')], limit=1).fee_percentage
        account_number = self._get_account_number(token_id)
        tokenized_account_number = self._get_tokenized_account_number(
            account_number, provider_id)
        cc_expiry = token_id.expyear.replace(" ", "").replace("/", "") if token_id.expyear else False
        payable_amount = float((process_values.get(
            "amount")) + float(process_values.get(
            "amount")) * fee_percentage) if provider_id.is_payment_fee else process_values.get(
            "amount")

        payload = {
            "merchid": str(provider_id.merchant_id),
            "account": tokenized_account_number,
            "expiry": cc_expiry,
            "amount": payable_amount,
            "currency": request.env.company.currency_id.name,
            "ecomind": "E",
            "tokenize": "Y",
            "capture": "y",
            "orderid": data.get("reference"),
            "cvv2": token_id.cvv,
            "postal": customer_id.zip,
            "name": customer_id.name,
            "address": customer_id.street,
            "city": customer_id.city,
            "country": customer_id.country_code
        }

        if token_id.payment_mode == "ach":
            payload["accttype"] = "ECHK"
            payload["achEntryCode"] = "WEB"

        return payload

    def _prepare_direct_payload(self, data, provider_id, customer_id,
                                process_values):
        fee_percentage = request.env['payment.provider'].sudo().search([('code', '=', 'cardpointe')], limit=1).fee_percentage
        account_number = self._get_account_number(data)
        tokenized_account_number = self._get_tokenized_account_number(
            account_number, provider_id)
        cc_expiry = data.get("cc_expiry").replace(" ", "").replace("/",
                                                                   "") if data.get(
            "cc_expiry") else None
        payable_amount = float((process_values.get(
            "amount")) + float(process_values.get(
            "amount")) * fee_percentage) if provider_id.is_payment_fee else process_values.get(
            "amount")

        payload = {
            "merchid": str(provider_id.merchant_id),
            "account": tokenized_account_number,
            "expiry": cc_expiry,
            "amount": payable_amount,
            "currency": request.env.company.currency_id.name,
            "ecomind": "E",
            "tokenize": "Y",
            "capture": "y",
            "orderid": data.get("reference"),
            "cvv2": data.get("cc_cvc"),
            "postal": customer_id.zip,
            "name": customer_id.name,
            "address": customer_id.street,
            "city": customer_id.city,
            "country": customer_id.country_code
        }

        if data.get("payment_mode") == "ach":
            payload["accttype"] = "ECHK"
            payload["achEntryCode"] = "WEB"

        return payload

    def _get_account_number(self, token_or_data):
        cc_number = token_or_data.card_number if hasattr(token_or_data,
                                                                 'card_number') else token_or_data.get("cc_number")

        routing_number = token_or_data.routing_number if hasattr(token_or_data,
                                                                 'routing_number') else token_or_data.get(
            "routing_number")

        if cc_number and routing_number:
            return f"{routing_number}/{cc_number}"
        elif cc_number:
            return cc_number
        else:
            return f"{routing_number}/{token_or_data.provider_ref}" if token_or_data.provider_ref else False


    def _send_request(self, api_url, headers, payload, data):
        provider_id = request.env['payment.provider'].sudo().search([('code', '=', 'cardpointe')], limit=1)
        try:
            _logger.info("URL:\n%s",
                         json.dumps(api_url, indent=4))
            _logger.info("Payload:\n%s",
                         json.dumps(payload, indent=4))

            response = requests.post(api_url, json=payload, headers=headers)
            if response.status_code == 200:
                json_data = response.json()

                if json_data.get("respstat") == "A" and not data.get(
                        "landingRoute"):
                    json_data.update({"data": data})
                    request.env[
                        "payment.transaction"].sudo()._handle_notification_data(
                        "cardpointe", json_data)
                    return request.redirect("/payment/status")
                if json_data.get("respstat") == "A" and data.get(
                        "landingRoute"):
                    data.update({"retref": json_data.get('retref')})
                    _logger.info(
                        "Response of $0.01 charge processing with data:\n%s",
                        json.dumps(json_data, indent=4))
                    if data.get('payment_mode') == 'ach':
                        self.refund_or_void_transaction(provider_id, json_data.get('retref'), 0.01)
                    request.env[
                        "payment.transaction"].sudo()._get_tx_from_notification_data(
                        "cardpointe", data)
                    return request.redirect("/payment/status")
                else:
                    self._handle_error(json_data.get("resptext"))
            else:
                self._handle_http_error(response.status_code)
        except requests.exceptions.ConnectionError as e:
            _logger.error(e)
            raise UserError(
                _("The Payment service failed due to a connection error"))

    def _handle_error(self, error_text):
        raise ValidationError(
            _("The Payment service failed due to the following error: %s! Please ensure that the details are correct",
              error_text))

    def _handle_http_error(self, status_code):
        error_messages = {
            400: "Invalid syntax. Please verify the Merchant ID, Username, Password, and Site information.",
            401: "Credentials not accepted by the server. Please verify the Merchant ID, Username, Password, and Site information.",
            404: "Endpoint URL path specified in the request was incorrect.",
            500: "Host server encountered an issue and was unable to send a response."
        }

        error_message = error_messages.get(status_code,
                                           "Unknown error occurred.")
        raise UserError(
            _("The Payment service failed due to the following error: %s",
              error_message))

    def basic_auth(self, username, password):
        """
        Generate basic authentication token.
        """
        token = b64encode(f"{username}:{password}".encode("utf-8")).decode(
            "ascii")
        return f"Basic {token}"

    def _get_tokenized_account_number(self, account_number, provider_id):
        """
        Tokenize the account number.
        """
        api_url_template = "https://{site}.cardconnect.com/cardsecure/api/v1/ccn/tokenize"
        if provider_id.state != 'enabled':
            if "-uat" not in provider_id.site:
                site = provider_id.site + "-uat"
            else:
                site = provider_id.site
        else:
            site = provider_id.site.replace("-uat", "")

        api_url = api_url_template.format(site=site)
        headers = {"Content-Type": "application/json"}
        data = {"account": account_number}

        response = requests.post(api_url, json=data, headers=headers)
        if response.status_code == 200:
            return response.json().get("token", "")
        else:
            response_data = response.json()
            raise UserError(
                _("Tokenization failed with status code %s. Check the card",
                  response.text))

    def refund_transaction(self, provider_id, retref, amount=0.01):
        """Refunds a transaction by retref (reference)."""
        refund_url_template = "https://{site}.cardconnect.com/cardconnect/rest/refund"
        site = provider_id.site if provider_id.state == 'enabled' else f"{provider_id.site}-uat"
        refund_url = refund_url_template.format(site=site)

        headers = {
            "Content-Type": "application/json",
            "Authorization": self.basic_auth(provider_id.username, provider_id.password)
        }

        refund_payload = {
            "merchid": str(provider_id.merchant_id),
            "retref": retref,
            "amount": "{:.2f}".format(amount),  # Refund the $0.01 charge
        }

        try:
            _logger.info("Refund URL:\n%s", refund_url)
            _logger.info("Refund Payload:\n%s", json.dumps(refund_payload, indent=4))

            response = requests.post(refund_url, json=refund_payload, headers=headers)

            if response.status_code == 200:
                refund_response = response.json()
                _logger.info("Refund Response:\n%s", json.dumps(refund_response, indent=4))
                return refund_response  # Return the refund response for further handling
            else:
                _logger.error("Refund HTTP error: %s", response.status_code)
                raise ValidationError(_("Refund failed with status code: %s", response.status_code))

        except requests.exceptions.ConnectionError as e:
            _logger.error("Refund connection error: %s", e)
            raise UserError(_("The refund process failed due to a connection error"))

    def void_transaction(self, provider_id, retref):
        """Voids an unsettled transaction by retref (reference)."""
        void_url_template = "https://{site}.cardconnect.com/cardconnect/rest/void"
        site = provider_id.site if provider_id.state == 'enabled' else f"{provider_id.site}-uat"
        void_url = void_url_template.format(site=site)

        headers = {
            "Content-Type": "application/json",
            "Authorization": self.basic_auth(provider_id.username, provider_id.password)
        }

        void_payload = {
            "merchid": str(provider_id.merchant_id),
            "retref": retref,  # Transaction reference returned from the verification response
            "amount":0.01
        }

        try:
            _logger.info("Void URL:\n%s", void_url)
            _logger.info("Void Payload:\n%s", json.dumps(void_payload, indent=4))

            response = requests.post(void_url, json=void_payload, headers=headers)

            if response.status_code == 200:
                void_response = response.json()
                _logger.info("Void Response:\n%s", json.dumps(void_response, indent=4))
                return void_response  # Return the void response for further handling
            else:
                _logger.error("Void HTTP error: %s", response.status_code)
                raise ValidationError(_("Void failed with status code: %s", response.status_code))

        except requests.exceptions.ConnectionError as e:
            _logger.error("Void connection error: %s", e)
            raise UserError(_("The void process failed due to a connection error"))

    def refund_or_void_transaction(self, provider_id, retref, amount=0.01):
        """Tries to refund the transaction. If it's not settled, it will void it."""
        try:
            _logger.info("Attempting to refund or void the transaction...")

            # Try refund first
            refund_response = self.refund_transaction(provider_id, retref, amount)
            if refund_response and refund_response.get("respstat") == "A":
                _logger.info("Refund of $0.01 was successful.")
                return  # Refund succeeded, exit function.
            else:
                _logger.warning("Refund failed with message: %s", refund_response.get("resptext", "Unknown reason"))
                _logger.warning("Trying to void the transaction...")

                # If refund fails, try voiding the unsettled transaction
                void_response = self.void_transaction(provider_id, retref)
                if void_response and void_response.get("respstat") == "A":
                    _logger.info("Transaction void was successful.")
                else:
                    raise ValidationError(
                        _("Void failed with error: %s", void_response.get("resptext", "Unknown reason")))

        except Exception as e:
            _logger.error("Error during refund or void process: %s", e)
            raise UserError(_("The refund or void process failed."))
