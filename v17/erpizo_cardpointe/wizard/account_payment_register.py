"""Account Payment Register"""
# -*- coding: utf-8 -*-

from base64 import b64encode
from datetime import datetime
import logging
import json
import requests
from odoo import models, fields, _, api, Command
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

MONTH_CHOICES = [
    ("01", "January"),
    ("02", "February"),
    ("03", "March"),
    ("04", "April"),
    ("05", "May"),
    ("06", "June"),
    ("07", "July"),
    ("08", "August"),
    ("09", "September"),
    ("10", "October"),
    ("11", "November"),
    ("12", "December"),
]


class AccountPaymentRegister(models.TransientModel):
    """Account payment register"""

    _inherit = "account.payment.register"

    @api.onchange('can_edit_wizard', 'payment_method_line_id', 'journal_id')
    def _compute_payment_token_id(self):
        codes = [key for key in dict(
            self.env['payment.provider']._fields[
                'code']._description_selection(self.env)
        )]
        for wizard in self:
            if (
                    wizard.can_edit_wizard
                    and wizard.payment_method_line_id.code in codes
                    and wizard.journal_id
                    and (wizard.partner_id or wizard.partner_id.child_ids)
            ):
                partner_ids = [wizard.partner_id.id] + wizard.partner_id.child_ids.ids
                domain = [
                    *self.env['payment.token']._check_company_domain(
                        wizard.company_id),
                    ('partner_id', 'in', partner_ids),
                    ('provider_id.capture_manually', '=', False),
                    ('provider_id', '=',
                     wizard.payment_method_line_id.payment_provider_id.id),
                ]
                wizard.payment_token_id = self.env[
                    'payment.token'].sudo().search(domain, limit=1)
            else:
                wizard.payment_token_id = False

    @api.depends('payment_method_line_id')
    def _compute_suitable_payment_token_ids(self):
        for wizard in self:
            if wizard.can_edit_wizard and wizard.use_electronic_payment_method:
                partner_ids = [wizard.partner_id.id] + wizard.partner_id.child_ids.ids

                wizard.suitable_payment_token_ids = self.env['payment.token'].sudo().search([
                    *self.env['payment.token']._check_company_domain(wizard.company_id),
                    ('provider_id.capture_manually', '=', False),
                    ('partner_id', 'in', partner_ids),
                    ('provider_id', '=', wizard.payment_method_line_id.payment_provider_id.id),
                ])
            else:
                wizard.suitable_payment_token_ids = [Command.clear()]

    cardpointe_payment_mode = fields.Selection(
        [("card", "Card"), ("ach", "ACH")], string="Payment " "Mode"
    )

    def _get_year_selection(self):
        """Returns the year selection"""
        current_year = datetime.now().year
        return [
            (str(year), str(year))
            for year in range(current_year, current_year + 31)
        ]

    payment_code = fields.Char(
        string="Code", related="payment_method_line_id.code"
    )
    card_number = fields.Char(string="Card Number")
    expiry_date = fields.Selection(MONTH_CHOICES, string="Expiry Date")
    expiry_year = fields.Selection(_get_year_selection, string="Expiry Year")
    card_cvv = fields.Char(string="CVV")
    account_number = fields.Char(string="Account Number")
    routing_number = fields.Char(string="Routing Number")

    @api.onchange("cardpointe_payment_mode")
    def _onchange_cardpointe_payment_mode(self):
        """Onchange Card Payment Mode"""
        self.payment_token_id = None
        if self.cardpointe_payment_mode == "card":
            self.account_number = None
            self.routing_number = None
        elif self.cardpointe_payment_mode == "ach":
            self.card_number = None
            self.expiry_date = None
            self.expiry_year = None
            self.card_cvv = None

    @api.onchange("payment_method_line_id")
    def _onchange_payment_method_line_id(self):
        """Change the payment method line"""
        if self.payment_code == "cardpointe":
            self.payment_token_id = False

    @api.constrains("expiry_date", "expiry_year")
    def _check_expiry_date(self):
        """Check the expiry date"""
        current_date = datetime.now().date()
        expiry_date_str = (
            f"{self.expiry_year}-{self.expiry_date}-01"
            if self.expiry_date
            else None
        )
        expiry_date = (
            datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
            if expiry_date_str
            else None
        )
        if expiry_date and expiry_date_str and expiry_date < current_date:
            raise ValidationError(
                "Card has expired. Please select a valid expiry date."
            )

    def action_create_payments(self):
        """Create a new payment"""
        auto_charge = self.env['ir.config_parameter'].sudo().get_param(
            'erpizo_cardpointe.max_charge_amount')
        if auto_charge and float(self.amount) > float(
                auto_charge) and self.cardpointe_payment_mode == "card":
            raise ValidationError(
                _("Credit card charge exceeds the allowed limit. Please ensure"
                  " the amount does not exceed the set maximum limit for credit"
                  " card payments. Note: This limitation does not apply to ACH"
                  " payments."))

        if self.payment_code == 'cardpointe':

            provider_id = self.env["payment.provider"].sudo().search(
                [("code", "=", "cardpointe")], limit=1
            )
            headers = {
                "Content-Type": "application/json",
                "Authorization": self.basic_auth(
                    provider_id.username, provider_id.password
                ),
            }
            api_url_template = "https://{site}.cardconnect.com/cardconnect/rest/auth"
            if provider_id.state != 'enabled':
                if "-uat" not in provider_id.site:
                    site = provider_id.site + "-uat"
                else:
                    site = provider_id.site
            else:
                site = provider_id.site.replace("-uat", "")

            inbound_url = api_url_template.format(site=site)


            if provider_id.state not in ["test", "enabled"]:
                raise UserError("The payment provider is disabled")


            if (
                self.payment_type == "inbound"
                and self.payment_method_code == "cardpointe"
            ):

                payload = self._prepare_payload(provider_id)
                response = self._make_request(inbound_url, payload, headers)
                return self._handle_response(response)

            if (
                self.payment_type == "outbound"
                and self.journal_id.name == "Cardpointe"
            ):
                return self._handle_outbound_payments(provider_id)

            payments = self._create_payments()

            return self._redirect_to_payments(payments)

        else:
            return super(AccountPaymentRegister, self).action_create_payments()

    def _prepare_payload(self, provider_id):
        """Prepare payload"""
        payment_mode = (
            self.cardpointe_payment_mode or self.payment_token_id.payment_mode
        )
        cc_number = (
            self.card_number
            or self.account_number
            or self.payment_token_id.card_number
        )
        routing_number = (
            self.routing_number or self.payment_token_id.routing_number
        )
        account_number = (
            f"{routing_number}/{cc_number}"
            if routing_number and cc_number
            else cc_number
        )
        tokenized_account_number = self._get_tokenized_account_number(
            account_number, provider_id
        )
        cc_expiry = (
            (f"{self.expiry_date}{self.expiry_year}").replace("/", "")
            if self.expiry_date and self.expiry_year
            else self.payment_token_id.expyear
        )
        currency_id = self.currency_id
        currency_text = self.env["res.currency"].browse(currency_id)


        payload = {
            "merchid": str(provider_id.merchant_id),
            "account": tokenized_account_number,
            "amount": self.amount,
            "ecomind": "E",
            "capture": "y",
            "name": self.partner_id.name,
            "address": self.partner_id.street,
            "city": self.partner_id.city,
            "country": self.partner_id.country_code
        }
        if payment_mode == "card":
            payload.update(
                {
                    "expiry": cc_expiry.replace(" ", "").replace("/", ""),
                    "currency": self.env.company.currency_id.name,
                    "tokenize": "Y",
                    "cvv2": self.card_cvv,
                    "postal": self.partner_id.zip,

                }
            )
        elif payment_mode == "ach":
            payload["accttype"] = "ECHK"
            payload["achEntryCode"] = "WEB"

        return payload

    def _make_request(self, url, payload, headers):
        """Make a POST request"""
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return json.loads(response.text)
        except requests.exceptions.RequestException as e:
            raise UserError(
                f"The Payment service failed due to the following error:"
                f" {str(e)}"
            )

    def _handle_response(self, response):
        """Handle the response"""
        if response.get("respstat") == "A":
            payments = self._create_payments()
            if payments.reconciled_invoice_ids:
                payments.reconciled_invoice_ids.cardpointe_ref = response.get(
                    "retref"
                )

            for move in payments.partner_id.unpaid_invoice_ids:
                move.line_ids.write({'block_charge': False})

            if self._context.get("dont_redirect_to_payments"):
                return True
            action = {
                "name": _("Payments"),
                "type": "ir.actions.act_window",
                "res_model": "account.payment",
                "context": {"create": False},
            }
            if len(payments) == 1:
                action.update({"view_mode": "form", "res_id": payments.id})
            else:
                action.update(
                    {
                        "view_mode": "tree,form",
                        "domain": [("id", "in", payments.ids)],
                    }
                )
            return action
        elif response.get("respstat") in ["C", "B"]:
            raise UserError(
                f"The Payment service failed due to the following error:"
                f" {response.get('resptext')}"
            )

    def _handle_outbound_payments(self, provider_id):
        """Handle outbound payments"""
        payments = self._create_payments()
        if payments.reconciled_invoice_ids.cardpointe_refund_ref:
            api_url_template = "https://{site}.cardconnect.com/cardconnect/rest/refund"

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
            payload = {
                "merchid": str(provider_id.merchant_id),
                "retref": (payments.reconciled_invoice_ids.
                           cardpointe_refund_ref),
                "amount": self.amount,
            }
            response = self._make_request(api_url, payload, headers)
            if (
                response.get("respproc") == "PPS"
                and response.get("respstat") == "A"
            ):
                payments.payment_transaction_id._set_done()
                if self._context.get("dont_redirect_to_payments"):
                    return True
                action = {
                    "name": _("Payments"),
                    "type": "ir.actions.act_window",
                    "res_model": "account.payment",
                    "context": {"create": False},
                }
                if len(payments) == 1:
                    action.update({"view_mode": "form", "res_id": payments.id})
                else:
                    action.update(
                        {
                            "view_mode": "tree,form",
                            "domain": [("id", "in", payments.ids)],
                        }
                    )
                return action
            elif (
                response.get("respproc") == "PPS"
                and response.get("respstat") == "C"
            ):
                raise UserError(
                    f"The Payment service failed due to the following error:"
                    f" {response.get('resptext')}"
                )

    def _redirect_to_payments(self, payments):
        """Redirect to  payments"""

        for move in payments.partner_id.unpaid_invoice_ids:
            move.line_ids.write({'block_charge': False})
        if self._context.get("dont_redirect_to_payments"):
            return True
        action = {
            "name": _("Payments"),
            "type": "ir.actions.act_window",
            "res_model": "account.payment",
            "context": {"create": False},
        }
        if len(payments) == 1:
            action.update({"view_mode": "form", "res_id": payments.id})
        else:
            action.update(
                {
                    "view_mode": "tree,form",
                    "domain": [("id", "in", payments.ids)],
                }
            )
        return action

    def basic_auth(self, username, password):
        """Basic authentication"""
        token = b64encode(f"{username}:{password}".encode("utf-8")).decode(
            "ascii"
        )
        return f"Basic {token}"

    def _get_tokenized_account_number(self, account_number, provider_id):
        """Get the tokenized account number"""
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
            token = response.json()["token"]
            return token
        else:
            raise UserError(
                _(
                    "The Payment service failed due to the following error.  "
                    "Tokenization failed with status code %s. Check the card",
                    response.text,
                )
            )


class AccountMoveReversal(models.TransientModel):
    """AccountMoveReversal"""

    _inherit = "account.move.reversal"

    def reverse_moves(self, is_modify=False):
        """Returns a list of reverse moves"""
        action = super(AccountMoveReversal, self).reverse_moves()
        for refund in self.new_move_ids:
            refund.cardpointe_refund_ref = self.move_ids.cardpointe_ref
        return action
