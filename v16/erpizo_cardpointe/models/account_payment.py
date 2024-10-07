"""Inherit PaymentProvider"""
# -*- coding: utf-8 -*-

from odoo import _, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    #=== ACTION METHODS ===#

    def action_post(self):
        # Post the payments "normally" if no transactions are needed.
        # If not, let the provider update the state.

        payments_need_tx = self.filtered(
            lambda p: p.payment_token_id and not p.payment_transaction_id
        )
        # creating the transaction require to access data on payment providers, not always accessible to users
        # able to create payments
        transactions = payments_need_tx.sudo()._create_payment_transaction()

        res = super(AccountPayment, self - payments_need_tx).action_post()

        for tx in transactions:  # Process the transactions with a payment by token
            tx._send_payment_request()

        # Post payments for issued transactions
        transactions._finalize_post_processing()
        if transactions.provider_id.code == "cardpointe":
            transactions._set_done()
        payments_tx_done = payments_need_tx.filtered(
            lambda p: p.payment_transaction_id.state == 'done'
        )

        super(AccountPayment, payments_tx_done).action_post()
        payments_tx_not_done = payments_need_tx.filtered(
            lambda p: p.payment_transaction_id.state != 'done'
        )
        payments_tx_not_done.action_cancel()

        return res
