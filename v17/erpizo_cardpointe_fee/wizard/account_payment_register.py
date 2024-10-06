"""Account Payment Register"""
# -*- coding: utf-8 -*-


from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountPaymentRegister(models.TransientModel):
    """Account payment register"""

    _inherit = "account.payment.register"

    is_payment_fee = fields.Boolean(default=False, string="Add Fee")
    fee_amount = fields.Monetary(
        "Fee Amount", currency_field="currency_id", store=True
    )
    is_fee_enabled = fields.Boolean(compute='_compute_fee_enabled')
    token_fee = fields.Boolean(related='payment_token_id.add_fee',readonly=False)


    @api.depends('payment_type', 'company_id', 'can_edit_wizard')
    def _compute_available_journal_ids(self):
        """
        Remove erpizo pay from journals list if the payment is used for vendor bill
        payment
        """
        res = super(AccountPaymentRegister, self)._compute_available_journal_ids()
        filtered_list = []
        cardpointe_id = self.env['account.journal'].search([('code','=','Cardp')],limit=1)
        for journal in self.available_journal_ids:
            if journal.code != cardpointe_id.code:
                filtered_list.append(int(str(journal.id).split('_')[-1]))
        if self.partner_type == 'supplier':
            self.available_journal_ids = [(6, 0, filtered_list)]

    @api.depends('payment_method_line_id')
    def _compute_fee_enabled(self):
        if self.payment_method_line_id.payment_provider_id.is_payment_fee:
            self.is_fee_enabled = True
        else:
            self.is_fee_enabled = False

    @api.onchange('is_payment_fee', 'cardpointe_payment_mode',
                  'payment_token_id', 'payment_method_line_id','token_fee')
    def onchange_payment_fee(self):
        fee_percentage = self.env['payment.provider'].sudo().search([('code','=','cardpointe')], limit=1).fee_percentage
        if self.is_payment_fee and self.cardpointe_payment_mode == "card":
            self.fee_amount = self.amount * fee_percentage
            self.amount += self.fee_amount
            self.write({'payment_difference_handling': 'reconcile',
                        'writeoff_account_id': self.env.ref
                        ('erpizo_cardpointe_fee.cardpointe_fee_account').id})
            move_names = ", ".join(self.line_ids.mapped('move_id.name'))
            self.write({'writeoff_label': 'Fee:' + move_names})
        elif self.payment_token_id and self.token_fee:
            self.fee_amount = self.source_amount * fee_percentage
            self.amount = self.source_amount + self.fee_amount
            self.write({'payment_difference_handling': 'reconcile',
                        'writeoff_account_id': self.env.ref
                        ('erpizo_cardpointe_fee.cardpointe_fee_account').id})
            move_names = ", ".join(self.line_ids.mapped('move_id.name'))
            self.write({'writeoff_label': 'Fee:' + move_names})
        elif (not self.is_payment_fee and
              self.cardpointe_payment_mode == 'card'):
            self.fee_amount = 0.0
            self.amount = self.source_amount
        elif self.cardpointe_payment_mode == 'ach':
            self.fee_amount = 0.0
            self.amount = self.source_amount
            self.is_payment_fee = False
        else:
            self.fee_amount = 0.0
            self.amount = self.source_amount

    @api.onchange("payment_method_line_id")
    def _onchange_payment_method_line_id(self):
        """Change the payment method line"""
        if self.payment_code == "cardpointe":
            self.write({'payment_difference_handling': 'reconcile',
                        'writeoff_account_id': self.env.ref
                        ('erpizo_cardpointe_fee.cardpointe_fee_account').id})
            move_names = ", ".join(self.line_ids.mapped('move_id.name'))
            self.write({'writeoff_label': 'Fee:' + move_names})

    def add_erpizo_payment_line(self):
        """
        Add the erpizo pay fee line to sale order and its invoice based on provider used
        and if is_payment_fee or token_fee is enabled
        """
        provider = self.env['payment.provider'].sudo().search([('code', '=', 'cardpointe')], limit=1)
        fee_percentage = provider.fee_percentage if provider else 0.0

        # so_origin = self.line_ids.invoice_origin
        for move_line in self.line_ids:
            so_origin = move_line.invoice_origin
            order_line = False
            if self.payment_method_code == 'cardpointe' and (self.is_payment_fee or self.token_fee):
                valid_payment_conditions = (self.cardpointe_payment_mode != 'ach' or self.payment_token_id) and \
                                           provider.is_payment_fee

                if valid_payment_conditions and so_origin:
                    so = self.env['sale.order'].sudo().search([('name', '=', so_origin)], limit=1)
                    if so:
                        order_line = self.env["sale.order.line"].create({
                            "order_id": so.id,
                            "product_id": provider.payment_fee_product_id.id,
                            "qty_invoiced": 1,
                            "price_unit": self.source_amount * fee_percentage,
                        })
                        so.write({"order_line": [(4, order_line.id)]})

            move = move_line.move_id
            if move and self.payment_method_code == 'cardpointe' and (self.is_payment_fee or self.token_fee):
                valid_payment_conditions = (self.cardpointe_payment_mode != 'ach' or self.payment_token_id) and \
                                            provider.is_payment_fee
                if valid_payment_conditions:
                    move_line_data = {
                        "move_id": move.id,
                        "product_id": provider.payment_fee_product_id.id,
                        "quantity": 1,
                        "price_unit": self.source_amount * fee_percentage,
                        "tax_ids": False,
                    }
                    if order_line:
                        move_line_data["sale_line_ids"] = [(4, order_line.id)]
                    move_line = self.env["account.move.line"].sudo().create(move_line_data)
                    move.sudo().write({"invoice_line_ids": [(4, move_line.id)]})

    def action_create_payments(self):
        """Create a new payment and add a narration for card payment fees."""
        # Add payment fee line before creating payments
        self.add_erpizo_payment_line()

        # Call the parent method to handle the payment creation
        res = super(AccountPaymentRegister, self).action_create_payments()
        provider = self.env['payment.provider'].sudo().search([('code', '=', 'cardpointe')], limit=1)
        fee_percentage = (provider.fee_percentage * 100) if provider else 0.0
        if self.payment_method_code == 'cardpointe' and (self.is_payment_fee or self.token_fee):
            valid_payment_conditions = (self.cardpointe_payment_mode != 'ach' or self.payment_token_id) and \
                                       provider.is_payment_fee
            if valid_payment_conditions:
                for move_line in self.line_ids:
                    total_amount = move_line.balance
                    narration = (
                        f"\n\nA {fee_percentage}% Credit Card Processing Fee was added to the total of the invoice. "
                        f"Original invoice total: {self.source_amount} New invoice total: {total_amount}"
                    )
                    move_line.move_id.narration = narration

        return res

    @api.onchange('payment_token_id')
    def _onchange_payment_token_id(self):
        if self.payment_token_id:
            self.cardpointe_payment_mode = False


class AccountMoveReversal(models.TransientModel):
    """AccountMoveReversal"""

    _inherit = "account.move.reversal"

    def reverse_moves(self, is_modify=False):
        """Returns a list of reverse moves"""
        action = super(AccountMoveReversal, self).reverse_moves()
        for refund in self.new_move_ids:
            refund.cardpointe_refund_ref = self.move_ids.cardpointe_ref
            provider_id = (
                self.move_ids.transaction_ids.provider_id
                if self.move_ids.transaction_ids
                else None
            )
            product_id = (
                self.env["product.product"].browse(
                    provider_id.payment_fee_product_id.id
                )
                if provider_id
                else None
            )
            if product_id:
                for line in self.new_move_ids.invoice_line_ids:
                    if line.product_id.id == product_id.id:
                        line.unlink()
        return action
