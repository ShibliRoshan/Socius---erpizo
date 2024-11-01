/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { patch } from '@web/core/utils/patch';
import { useService } from "@web/core/utils/hooks"; // To use dialog service for search more

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        console.log("FormController setup triggered", this);

        // Use the Dialog service to manage the search more dialog
        this.dialogService = useService("dialog");

        // Wait for the form view to be fully rendered
        this.onFormViewRendered();
    },

    onFormViewRendered() {
        // Bind the click event to the button after the form view is rendered
        const btn = document.querySelector(".btn_tree_view");
        if (btn) {
            btn.addEventListener("click", this._onClickSearchMore.bind(this));
        }
    },

    _onClickSearchMore() {
        // Call the search more logic
        console.log("Search More button clicked");

        // Simulating the onSearchMore functionality (based on many2one fields)
        const fieldName = 'your_field_name'; // Add the relevant many2one field's name
        const field = this.model.get(this.handle).fields[fieldName];

        if (field && field.onSearchMore) {
            field.onSearchMore();
        } else {
            console.error("Search More functionality not available for the field");
        }
    },
});
