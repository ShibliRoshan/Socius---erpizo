from odoo import api, fields, models,_
from odoo.tools.safe_eval import datetime
from datetime import datetime

class AccountMove(models.Model):
    _inherit = 'account.move'

    # wizard_id = fields.Many2one('past.due.invoice.wizard')
    selected_to_pay = fields.Boolean()

    def add_past_due_invoices(self):
        print('@@@@@@@@')
        today_date = datetime.today().date()

        due_invoice = self.search([('invoice_date_due', '<=', today_date),('partner_id', '=', self.partner_id.id),
                                   ('move_type', '=', 'out_invoice'), ('payment_state',"=",'not_paid')])

        return {
            'type': 'ir.actions.act_window',
            'name': 'Add Past Due Invoices',
            'view_mode': 'form',
            'res_model': 'past.due.invoice.wizard',
            # 'view_id': self.env.ref('past_due_invoice_management.view_past_due_invoice_confirmation_wizard_form').id,
            'target': 'new',  # Opens as a popup
            'context': {
                'default_move_id': self.id,  # Example context to filter invoices
                'default_invoice_ids': due_invoice.ids,  # Example context to filter invoices
            },
        }

    def portal_due_invoices(self):
        today_date = datetime.today().date()

        due_invoice = self.search([('invoice_date_due', '<=', today_date), ('partner_id', '=', self.partner_id.id),
                                   ('move_type', '=', 'out_invoice'), ('payment_state', "=", 'not_paid')])
        return due_invoice