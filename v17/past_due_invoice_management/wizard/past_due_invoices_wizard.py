from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError
import base64


class PastDueInvoiceWizard(models.TransientModel):
    _name = 'past.due.invoice.wizard'
    _description = 'Wizard to show past due invoices'

    invoice_ids = fields.Many2many('account.move', string='Past Due Invoices')
    move_id = fields.Many2one('account.move',string='Current Invoice')


    def action_add_invoices(self):
        """ Open a window to compose an email
        """
        self.ensure_one()
        # report_action = self.send_past_due_invoices()
        template = self.env.ref('past_due_invoice_management.past_due_invoice_email_template')
        attachment_ids = []

        # Loop through all selected invoices and generate PDFs
        for invoice in self.invoice_ids:
            # Generate PDF for each invoice
            pdf_content, _ = self.env['ir.actions.report']._render('account.account_invoices', invoice.id)
            pdf_base64 = base64.b64encode(pdf_content)

            attachment_data = {
                'name': f"Invoice_{invoice.name}.pdf",
                'type': 'binary',
                'datas': pdf_base64,
                'store_fname': f"Invoice_{invoice.name}.pdf",
                'mimetype': 'application/pdf',
            }
            attachment = self.env['ir.attachment'].create(attachment_data)
            attachment_ids.append(attachment.id)
        template.attachment_ids = [(6, 0, attachment_ids)]

        return {
            'name': "Send",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move.send',
            'target': 'new',
            'context': {
                "default_model":'account.move',
                # "default_res_ids":self.move_ids,
                "default_template_id":template.id if template else False,
                'default_mail_template_id': template and template.id or False,
                'default_attachment_ids': template.attachment_ids if template and attachment_ids else False,
                "default_partner_ids": [(4, self.move_id.partner_id.id)] if self.move_id.partner_id else False,

            },
        }

    def send_past_due_invoices(self):
        """ Sends the selected invoices in a single mail as attachments
        """
        self.ensure_one()

        if not self.invoice_ids:
            raise UserError(_("No invoices selected to send."))

        # Reference the email template
        template = self.env.ref('past_due_invoice_management.past_due_invoice_email_template')

        # List to store attachment ids
        attachment_ids = []

        # Loop through all selected invoices and generate PDFs
        for invoice in self.invoice_ids:
            # Generate PDF for each invoice
            pdf_content, _ = self.env['ir.actions.report']._render('account.account_invoices', invoice.id)
            pdf_base64 = base64.b64encode(pdf_content)

            attachment_data = {
                'name': f"Invoice_{invoice.name}.pdf",
                'type': 'binary',
                'datas': pdf_base64,
                'store_fname': f"Invoice_{invoice.name}.pdf",
                'mimetype': 'application/pdf',
            }
            attachment = self.env['ir.attachment'].create(attachment_data)
            attachment_ids.append(attachment.id)

        # Attach all PDFs to the email template
        template.attachment_ids = [(6, 0, attachment_ids)]

        # Define email values
        email_values = {
            'email_to': 'shibli@sociusus.com',  # You can customize this with actual recipient email
            'email_from': 'shibli@sociusus.com',  # You can customize this with actual sender email
        }

        # Pass the list of invoices to the template via context
        template.with_context({
            'invoice_ids': self.invoice_ids,
            'user': self.env.user
        }).send_mail(self.id, email_values=email_values, force_send=True)


        # Unlink the attachments from the template after sending the email
        template.attachment_ids = [(3, att_id) for att_id in attachment_ids]

        return True
