# -*- coding: utf-8 -*-

from base64 import b64encode
import logging
import json
import requests
from datetime import date
from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_saved_token = fields.Boolean(default=False, string='Is Saved Token',
                                    compute='_compute_saved_token')

    def _compute_saved_token(self):
        """Compute whether the partner has a saved payment token."""
        for record in self:
            payment_token = self.env['payment.token'].search([
                ('partner_id', '=', record.id)], limit=1)
            record.is_saved_token = bool(payment_token)

    def action_cardpointe_charge(self):
        """Initiate a cardpointe charge using a saved payment token or register a new payment."""
        payment_token = self.env['payment.token'].search([
            ('partner_id', '=', self.id),
            ('provider_id.code', '=', 'cardpointe')
        ])
        if len(payment_token) == 1:
            provider_id = payment_token.provider_id
            headers = {
                "Content-Type": "application/json",
                "Authorization": self.basic_auth(provider_id.username,
                                                 provider_id.password),
            }
            api_url_template = "https://{site}.cardconnect.com/cardconnect/rest/auth"

            site = provider_id.site.replace("-uat","") if provider_id.state == 'enabled' else provider_id.site + "-uat"
            inbound_url = api_url_template.format(site=site)
            if provider_id.state not in ["test", "enabled"]:
                raise UserError("The payment provider is disabled")

            payload = self._prepare_payload(provider_id, payment_token)
            response = self._make_request(inbound_url, payload, headers)
            return self._handle_response(response, payment_token)
        elif len(payment_token) > 1:
            return {
                'name': _('Select Token for Payment'),
                'res_model': 'payment.token.wizard',
                'view_mode': 'form',
                'views': [[False, 'form']],
                'context': {
                    'default_partner_id': self.id,
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
                    'active_ids': self.unreconciled_aml_ids.filtered(
                        lambda x: not x.block_charge).ids,
                    'default_amount': self.get_payable_amount(),
                    'default_journal_id': self.env['account.journal'].search(
                        [('code', '=', 'Cardpointe')], limit=1).id,
                    'default_payment_method_line_id': self.env[
                        'account.payment.method.line'].search(
                        [('name', '=', 'Erpizo Pay')], limit=1).id,
                    'default_group_payment': True
                },
                'target': 'new',
                'type': 'ir.actions.act_window',
            }

    def _prepare_payload(self, provider_id, payment_token):
        """Prepare the payload for the payment request."""
        payment_mode = payment_token.payment_mode
        cc_number = payment_token.card_number
        routing_number = payment_token.routing_number
        account_number = f"{routing_number}/{cc_number}" if routing_number and cc_number else cc_number
        tokenized_account_number = self._get_tokenized_account_number(account_number, provider_id)
        cc_expiry = payment_token.expyear

        payload = {
            "merchid": str(provider_id.merchant_id),
            "account": tokenized_account_number,
            "amount": self.get_payable_amount(),
            "ecomind": "E",
            "capture": "y",
            "name": self.name,
            "address": self.street,
            "city": self.city,
            "country": self.country_code
        }

        if payment_mode == "card":
            payload.update({
                "expiry": cc_expiry.replace(" ", "").replace("/", ""),
                "currency": self.env.company.currency_id.name,
                "tokenize": "Y",
                "cvv2": payment_token.cvv,
                "postal": self.zip,
            })
        elif payment_mode == "ach":
            payload["accttype"] = "ECHK"
            payload["achEntryCode"] = "WEB"

        return payload

    def _make_request(self, url, payload, headers):
        """Make a POST request and handle errors."""
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return json.loads(response.text)
        except requests.exceptions.RequestException as e:
            raise UserError(f"The Payment service failed due to the following error: {str(e)}")

    def _handle_response(self, response, payment_token):
        """Handle the response from the payment provider."""

        if response.get("respstat") == "A":
            payments = self._create_cardpointe_payments(payment_token)
            if payments.reconciled_invoice_ids:
                payments.reconciled_invoice_ids.cardpointe_ref = response.get("retref")

            action = {
                "name": _("Payments"),
                "type": "ir.actions.act_window",
                "res_model": "account.payment",
                "context": {"create": False},
            }
            if len(payments) == 1:
                action.update({"view_mode": "form", "res_id": payments.id})
            else:
                action.update({
                    "view_mode": "tree,form",
                    "domain": [("id", "in", payments.ids)],
                })
            return action
        elif response.get("respstat") in ["C", "B"]:
            if not self.unpaid_invoice_ids:
                return

                # Create the table rows for each unpaid invoice
            table_rows = ""
            for rec in self.unpaid_invoice_ids:
                amount = rec.amount_residual
                table_rows += (
                    f"<tr>"
                    f"<td>{rec.name}</td>"
                    f"<td>{rec.partner_id.name}</td>"
                    f"<td>{date.today()}</td>"
                    f"<td>{amount}</td>"
                    f"</tr>"
                )

            # Construct the email body with the table
            mail_body = f"""
                Hi,<br><br>
                The automatic billing cycle for the following overdue invoices failed to collect a payment and the invoices are still overdue:<br><br>
                <table border='1' style='border-collapse: collapse; width: 100%;'>
                    <thead>
                        <tr>
                            <th>Invoice</th>
                            <th>Partner</th>
                            <th>Attempt Date</th>
                            <th>Amount</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table><br>
                Please take the necessary actions to resolve these overdue invoices.<br><br>
                Best regards,<br>
                Your Company
                """

            # Create and send the email
            mail = self.env['mail.mail'].create({
                'body_html': mail_body,
                'email_to': ','.join(
                    self.unpaid_invoice_ids.mapped('invoice_user_id.email')),
                'subject': 'Overdue Invoices Notification',
                'recipient_ids': [(4, rec.partner_id.id) for rec in
                                  self.unpaid_invoice_ids],
            })
            mail.send()

            auto_charge = self.env['ir.config_parameter'].sudo().get_param(
                'erpizo_cardpointe.max_charge_amount')
            if auto_charge and float(self.get_payable_amount()) > float(auto_charge):

                # Post a message to the chatter
                self.message_post(body="Credit card charge exceeds the allowed limit. Please ensure"
                          " the amount does not exceed the set maximum limit for credit"
                          " card payments. Note: This limitation does not apply to ACH"
                          " payments.", message_type='email')

    def _redirect_to_payments(self, payments):
        """Redirect to payment records."""
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
            action.update({
                "view_mode": "tree,form",
                "domain": [("id", "in", payments.ids)],
            })
        return action


    def _create_cardpointe_payments(self, payment_token):
        """Create account payments for CardPointe transactions."""
        self.ensure_one()

        provider_id = self.env["payment.provider"].sudo().search(
            [("code", "=", "cardpointe")], limit=1
        )
        payment_method_line = provider_id.journal_id.inbound_payment_method_line_ids.filtered(
            lambda l: l.code == provider_id.code
        )

        payment_values = {
            "amount": self.get_payable_amount(),
            "payment_type": "inbound" if self.total_due or self.total_overdue > 0 else "outbound",
            "currency_id": self.currency_id.id,
            "partner_id": self.commercial_partner_id.id,
            "partner_type": "customer",
            "journal_id": provider_id.journal_id.id,
            "company_id": provider_id.company_id.id,
            "payment_method_line_id": payment_method_line.id,
            "payment_token_id": payment_token.id,
            "ref": self.name
        }
        payment = self.env["account.payment"].create(payment_values)
        payment.action_post()

        unpaid_invoices = self.unpaid_invoice_ids.filtered(
            lambda inv: inv.payment_state == "not_paid")
        if unpaid_invoices:
            for inv in unpaid_invoices:
                if inv.state == "draft":
                    unpaid_invoices.action_post()
                    inv.line_ids.write({'block_charge': False})

            (payment.line_ids + unpaid_invoices.line_ids).filtered(
                lambda
                    line: line.account_id == payment.destination_account_id and not line.reconciled and not line.block_charge
            ).reconcile()

            for move in unpaid_invoices:
                move.line_ids.filtered(lambda
                                           line: line.id in self.unreconciled_aml_ids.ids).write(
                    {'block_charge': False})
                move.line_ids.write({'block_charge': False})
        return payment



    def _cron_execute_followup_company(self):
        # Fetch follow-up data for all partners
        followup_data = self._query_followup_data(all_partners=True)
        partner_ids_in_need = [
            d['partner_id'] for d in followup_data.values()
            if d['followup_status'] == 'in_need_of_action'
        ]
        in_need_of_action = self.env['res.partner'].browse(partner_ids_in_need)

        # Filter partners needing automatic follow-up
        in_need_of_action_auto = in_need_of_action.filtered(
            lambda
                p: p.followup_line_id.auto_execute and p.followup_reminder_type == 'automatic'
        )

        for rec in in_need_of_action:
            partner_ids = [rec.id] + rec.child_ids.ids

            # Fetch payment tokens for the partners
            payment_tokens = self.env['payment.token'].search([
                ('partner_id', 'in', partner_ids),
                ('provider_id.code', '=', 'cardpointe')
            ])

            for payment_token in payment_tokens:
                provider_id = payment_token.provider_id
                if provider_id.state not in ["test", "enabled"]:
                    raise UserError("The payment provider is disabled")

                # Set up request headers and URL
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": rec.basic_auth(provider_id.username,
                                                    provider_id.password),
                }
                site = provider_id.site.replace("-uat",
                                                "") if provider_id.state == 'enabled' else f"{provider_id.site}-uat"
                inbound_url = f"https://{site}.cardconnect.com/cardconnect/rest/auth"

                # Prepare account details
                account_number = payment_token.routing_number + '/' + payment_token.card_number if payment_token.routing_number and payment_token.card_number else payment_token.card_number
                tokenized_account_number = rec._get_tokenized_account_number(
                    account_number, provider_id)

                # Prepare payload for the request
                payload = {
                    "merchid": str(provider_id.merchant_id),
                    "account": tokenized_account_number,
                    "amount": rec.get_payable_amount(),
                    "ecomind": "E",
                    "capture": "y",
                    "name": rec.name,
                    "address": rec.street,
                    "city": rec.city,
                    "country": rec.country_code,
                }

                if payment_token.payment_mode == "card":
                    payload.update({
                        "expiry": payment_token.expyear.replace(" ",
                                                                "").replace(
                            "/", ""),
                        "currency": rec.env.company.currency_id.name,
                        "tokenize": "Y",
                        "cvv2": payment_token.cvv,
                        "postal": rec.zip,
                    })
                elif payment_token.payment_mode == "ach":
                    payload.update({
                        "accttype": "ECHK",
                        "achEntryCode": "WEB"
                    })

                # Make the request and handle the response
                response = rec._make_request(inbound_url, payload, headers)
                if response.get("respstat") == "A":
                    rec._create_cardpointe_payments_cron(payment_token)
                elif response.get("respstat") in ["C", "B"]:
                    if rec.unpaid_invoice_ids:
                        self._send_failure_notification(rec)

                self._handle_unpaid_invoices_limit(rec)

        self._execute_followup_for_auto_partners(in_need_of_action_auto)

    def _send_failure_notification(self, partner):
        """Send notification for failed payment attempts."""
        table_rows = "".join(
            f"<tr><td>{inv.name}</td><td>{inv.partner_id.name}</td><td>{date.today()}</td><td>{inv.amount_residual}</td></tr>"
            for inv in partner.unpaid_invoice_ids
        )

        mail_body = f"""
            Hi,<br><br>
            The automatic billing cycle for the following overdue invoices failed to collect a payment and the invoices are still overdue:<br><br>
            <table border='1' style='border-collapse: collapse; width: 100%;'>
                <thead>
                    <tr>
                        <th>Invoice</th>
                        <th>Partner</th>
                        <th>Attempt Date</th>
                        <th>Amount</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table><br>
            Please take the necessary actions to resolve these overdue invoices.<br><br>
            Best regards,<br>
            Your Company
        """

        self.env['mail.mail'].create({
            'body_html': mail_body,
            'email_to': ','.join(
                partner.unpaid_invoice_ids.mapped('invoice_user_id.email')),
            'subject': 'Overdue Invoices Notification',
            'recipient_ids': [(4, partner.partner_id.id) for partner in
                              partner.unpaid_invoice_ids],
        }).send()

    def _handle_unpaid_invoices_limit(self, partner):
        """Check and handle cases where the payable amount exceeds auto charge limit."""
        auto_charge_limit = self.env['ir.config_parameter'].sudo().get_param(
            'erpizo_cardpointe.max_charge_amount')
        if auto_charge_limit and float(partner.get_payable_amount()) > float(
                auto_charge_limit):
            partner.message_post(
                body="Credit card charge exceeds the allowed limit. Please ensure the amount does not exceed the set maximum limit for credit card payments. Note: This limitation does not apply to ACH payments.",
                message_type='email'
            )

    def _execute_followup_for_auto_partners(self, partners):
        """Execute follow-up actions for partners marked for automatic follow-up."""
        for partner in partners:
            try:
                partner._execute_followup_partner()
            except UserError as e:
                _logger.warning(e, exc_info=True)

    def _create_cardpointe_payments_cron(self, payment_token):
        """Create account payments for CardPointe transactions."""
        partner = self
        provider_id = self.env["payment.provider"].sudo().search(
            [("code", "=", "cardpointe")], limit=1
        )
        payment_method_line = provider_id.journal_id.inbound_payment_method_line_ids.filtered(
            lambda l: l.code == provider_id.code
        )

        payment_values = {
            "amount": partner.get_payable_amount_cron(partner),
            "payment_type": "inbound" if partner.total_due or partner.total_overdue > 0 else "outbound",
            "currency_id": partner.currency_id.id,
            "partner_id": partner.commercial_partner_id.id,
            "partner_type": "customer",
            "journal_id": provider_id.journal_id.id,
            "company_id": provider_id.company_id.id,
            "payment_method_line_id": payment_method_line.id,
            "payment_token_id": payment_token.id,
            "ref": partner.name
        }

        payment = self.env["account.payment"].create(payment_values)
        payment.action_post()

        unpaid_invoices = partner.unpaid_invoice_ids.filtered(
            lambda inv: inv.payment_state == "not_paid"
        )

        if unpaid_invoices:

            (payment.line_ids + unpaid_invoices.line_ids).filtered(
                lambda
                    line: line.account_id == payment.destination_account_id and not line.reconciled and not line.block_charge
            ).reconcile()

        for move in partner.unpaid_invoice_ids:
            move.line_ids.write({'block_charge': False})


        return payment



    def basic_auth(self, username, password):
        """Generate Basic Authentication token."""
        token = b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        return f"Basic {token}"

    def _get_tokenized_account_number(self, account_number, provider_id):
        """Tokenize the account number using Cardpointe API."""
        api_url_template = "https://{site}.cardconnect.com/cardsecure/api/v1/ccn/tokenize"
        site = provider_id.site.replace("-uat", "") if provider_id.state == 'enabled' else provider_id.site + "-uat"
        api_url = api_url_template.format(site=site)
        headers = {"Content-Type": "application/json"}
        data = {"account": account_number}

        response = requests.post(api_url, json=data, headers=headers)
        if response.status_code == 200:
            token = response.json()["token"]
            return token
        else:
            raise UserError(_("Tokenization failed with status code %s. Check the card", response.status_code))


    def get_payable_amount(self):
        """
        Calculate the total payable amount for unpaid invoices by summing the
        amounts of lines that are not reconciled and not blocked for charge.

        :return: The total payable amount
        :rtype: float
        """
        amount = sum(
            line.amount_residual_currency
            for move in self.unpaid_invoice_ids
            for line in move.line_ids
            if
            line.id in self.unreconciled_aml_ids.ids and not line.block_charge
        )
        return amount

    def get_payable_amount_cron(self, partner):
        """
        Calculate the total payable amount for unpaid invoices by summing the
        amounts of lines that are not reconciled and not blocked for charge.

        :param partner: The partner whose unpaid invoices are being considered
        :type partner: res.partner
        :return: The total payable amount
        :rtype: float
        """
        total_payable = 0.0
        for move in partner.unpaid_invoice_ids:
            for line in move.line_ids:
                if line.id in partner.unreconciled_aml_ids.ids and not line.block_charge:
                    total_payable += line.amount_residual_currency

        return total_payable

