from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    def _compute_dynamic_content(self):
        provider = self.env['payment.provider'].sudo().search([('code', '=', 'cardpointe')], limit=1)
        provider_product = provider.payment_fee_product_id
        fee_percentage = provider.fee_percentage
        fee_percentage = fee_percentage * 100
        prod_list = []
        price_list = []
        for line in self.invoice_line_ids:
            prod_list.append(line.product_id)
            if provider_product == line.product_id:
                price_list.append(line.price_unit)
        if prod_list and provider_product in [x for x in prod_list]:
            if self.transaction_ids.payment_id.payment_method_code == 'cardpointe' and provider.is_payment_fee:

                narration = ("\n\nA " + str(fee_percentage) + "% Credit Card Processing "
                             "Fee was added to the total of the invoice."
                             "Original invoice total: " + str(round(self.amount_total - price_list[0], 2)) +
                             " New invoice total: " + str(round(self.amount_total, 2)))
                self.narration = narration
                return narration
        else:
            return self.narration

