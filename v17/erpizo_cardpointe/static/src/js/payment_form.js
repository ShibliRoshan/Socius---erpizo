/** @odoo-module **/


import paymentForm from '@payment/js/payment_form';
import publicWidget from "@web/legacy/js/public/public_widget";

import {_t} from "@web/core/l10n/translation";
import {jsonrpc, RPCError} from "@web/core/network/rpc_service";


publicWidget.registry.CardPointe = publicWidget.Widget.extend({
    selector: '#payment_method',
    events: {
        'change .o_payment_form input[name="payment_mode"]': '_changePaymentMode',
        'click .o_payment_submit_button': '_changePaymentMode',
    },

    /**
     * @override
     */
    start: function() {
        $('.o_payment_form input[name="payment_mode"]:checked').trigger('change');
        var selectElement = document.getElementById("expiry_year");

        // Check if selectElement is a valid HTML select element
        if (selectElement && selectElement.tagName === 'SELECT') {
            // Your code to append options
            var currentYear = new Date().getFullYear();
            for (var i = 0; i < 30; i++) {
                var option = document.createElement("option");
                option.value = currentYear + i;
                option.text = currentYear + i;
                selectElement.appendChild(option);
            }
        } else {
            console.error('selectElement is not a valid HTML select element.');
        }


        return this._super(...arguments);

    },
    _changePaymentMode: function(ev) {
        if ($(ev.target).val() === 'card') {
            $('.o_payment_form div[name="o_payment_tokenize_container"]').show();
            document.getElementById('card_payment_fields').style.display = 'block';
            document.getElementById('ach_payment_fields').style.display = 'none';
            document.getElementById('acc_number').value = "";
            document.getElementById('routing_number').value = "";

        } else if ($(ev.target).val() === 'ach') {
            document.getElementById('card_payment_fields').style.display = 'none';
//            $('.o_payment_form div[name="o_payment_tokenize_container"]').hide();

            document.getElementById('ach_payment_fields').style.display = 'block';
            document.getElementById('card_number').value = "";
            document.getElementById('cvv_number').value = "";
        }


    },
});


publicWidget.registry.CardPointeForm = publicWidget.Widget.extend({
    selector: '#o_payment_form',
    events: {
        'change .o_payment_form input[name="payment_mode"]': '_changePaymentMode',
        'click .o_payment_submit_button': '_changePaymentMode',
        'click .o_payment_inline_form': '_changePaymentMode',
    },

    /**
     * @override
     */
    start: function() {
        $('.o_payment_form input[name="payment_mode"]:checked').trigger('change');
        var selectElement = document.getElementById("expiry_year");

        // Check if selectElement is a valid HTML select element
        if (selectElement && selectElement.tagName === 'SELECT') {
            // Your code to append options
            var currentYear = new Date().getFullYear();
            for (var i = 0; i < 30; i++) {
                var option = document.createElement("option");
                option.value = currentYear + i;
                option.text = currentYear + i;
                selectElement.appendChild(option);
            }
        } else {
            console.error('selectElement is not a valid HTML select element.');
        }


        return this._super(...arguments);

    },
    _changePaymentMode: function(ev) {

        if ($(ev.target).val() === 'card') {
            $('.o_payment_form div[name="o_payment_tokenize_container"]').show();
            document.getElementById('card_payment_fields').style.display = 'block';
            document.getElementById('ach_payment_fields').style.display = 'none';
            document.getElementById('acc_number').value = "";
            document.getElementById('routing_number').value = "";

        } else if ($(ev.target).val() === 'ach') {
            document.getElementById('card_payment_fields').style.display = 'none';
//            $('.o_payment_form div[name="o_payment_tokenize_container"]').hide();

            document.getElementById('ach_payment_fields').style.display = 'block';
            document.getElementById('card_number').value = "";
            document.getElementById('cvv_number').value = "";
        }


    },
});


publicWidget.registry.CardPointeFormInline = publicWidget.Widget.extend({
    selector: '#o_payment_form',

    events: {
        'change .position-relative input[name="payment_mode"]': '_changePaymentMode',
        'click .o_payment_submit_button': '_changePaymentMode',
        'click .o_payment_inline_form': '_changePaymentMode',
    },

    /**
     * @override
     */
    start: function() {
        $('.o_payment_form input[name="payment_mode"]:checked').trigger('change');
        var selectElement = document.getElementById("expiry_year");

        // Check if selectElement is a valid HTML select element
        if (selectElement && selectElement.tagName === 'SELECT') {
            // Your code to append options
            var currentYear = new Date().getFullYear();
            for (var i = 0; i < 30; i++) {
                var option = document.createElement("option");
                option.value = currentYear + i;
                option.text = currentYear + i;
                selectElement.appendChild(option);
            }
        } else {
            console.error('selectElement is not a valid HTML select element.');
        }


        return this._super(...arguments);

    },
    _changePaymentMode: function(ev) {

        if ($(ev.target).val() === 'card') {
            $('.o_payment_form div[name="o_payment_tokenize_container"]').show();
            document.getElementById('card_payment_fields').style.display = 'block';
            document.getElementById('ach_payment_fields').style.display = 'none';
            document.getElementById('acc_number').value = "";
            document.getElementById('routing_number').value = "";

        } else if ($(ev.target).val() === 'ach') {
            document.getElementById('card_payment_fields').style.display = 'none';
//            $('.o_payment_form div[name="o_payment_tokenize_container"]').hide();

            document.getElementById('ach_payment_fields').style.display = 'block';
            document.getElementById('card_number').value = "";
            document.getElementById('cvv_number').value = "";
        }


    },
});

paymentForm.include({

    async _prepareInlineForm(providerId, providerCode, paymentOptionId, paymentMethodCode, flow) {
        if (providerCode !== 'cardpointe') {
            this._super(...arguments);
            return;
        } else if (flow === 'token') {
            return;
        }
        this._setPaymentFlow('direct');
    },

    _processTokenFlow: (providerCode, paymentOptionId, paymentMethodCode, processingValues) => {

        if (providerCode !== 'cardpointe') {
            window.location = '/payment/status';
        }


        const requestData = {
            'tokenId': paymentOptionId,
            'flow': 'token',
            'amount': processingValues.amount,
            'currency_id': processingValues.currency_id,
            'partner_id': processingValues.partner_id,
            'provider_code': processingValues.provider_code,
            'provider_id': processingValues.provider_id,
            'reference': processingValues.reference,
        };

        jsonrpc("/payment/cardpointe", requestData).then(function() {
            window.location = '/payment/status';
        });

    },

    _processDirectFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues) {
        if (providerCode !== 'cardpointe') {
            return this._super(...arguments);
        }
        var landingRoute = $('#o_payment_form').data('landing-route');

        const cc_number = document.getElementById('card_number').value;
        const cc_expiry_month = document.getElementById('expiry_month').value;
        const cc_expiry_year = document.getElementById('expiry_year').value;
        const cc_cvc = document.getElementById('cvv_number').value;
        const account_number = document.getElementById('acc_number').value;
        const routing_number = document.getElementById('routing_number').value;
        const payment_mode = document.querySelector('input[name="payment_mode"]:checked').value;
        const cc_expiry = cc_expiry_month && cc_expiry_year ? `${cc_expiry_month}/${cc_expiry_year}` : null;
        const invalidInputs = [];

        if (!cc_number && payment_mode === 'card') invalidInputs.push('card_number');
        if (!account_number && payment_mode === 'ach') invalidInputs.push('acc_number');
        if (!routing_number && payment_mode === 'ach') invalidInputs.push('routing_number');
        if (!cc_expiry && payment_mode === 'card') {
            invalidInputs.push('expiry_month');
            invalidInputs.push('expiry_year');
        }
        if (!cc_cvc && payment_mode === 'card') invalidInputs.push('cvv_number');

        invalidInputs.forEach(inputId => {
            $(`input#${inputId}`).addClass('is-invalid o_has_error').removeClass('o_has_success is-valid');
        });

        //        if ((cc_number && cc_expiry && cc_cvc) || (account_number && routing_number)) {

        var transaction_values = this._prepareTransactionRouteParams(processingValues.provider_id)
        const params = {
            'reference': processingValues.reference,
            'acquirer_id': processingValues.provider_id,
            'paymentMethodCode': paymentMethodCode,
            'partner_id': processingValues.partner_id,
            'cc_number': payment_mode === 'card' ? cc_number : account_number,
            'cc_expiry': cc_expiry,
            'routing_number': routing_number,
            'token': cc_number,
            'cc_cvc': cc_cvc,
            'payment_mode': payment_mode,
            'flow': 'direct',
            'landingRoute': landingRoute === '/my/payment_method' ? landingRoute : false,
            'tokenization_requested':  transaction_values.tokenization_requested
        };


        jsonrpc('/payment/cardpointe', params).then(() => {
            window.location = '/payment/status';
        }).catch(error => {
            if (error instanceof RPCError) {
                this._displayErrorDialog(_t("Payment Processing Failed"), error.data.message);
                this._enableButton();

            } else {
                return Promise.reject(error);
            }
        });



        //        } else {
        //            this._displayErrorDialog(_t("Incorrect payment details"));
        //            window.location = '/shop/payment';
        //        }
    },
});



document.addEventListener("DOMContentLoaded", function() {
    // Your code here
    $('.o_payment_form input[name="payment_mode"]:checked').trigger('change');
    var selectElement = document.getElementById("expiry_year");

    // Get the current year
    var currentYear = new Date().getFullYear();

    // Loop to add options for the next 30 years
    for (var i = 0; i < 30; i++) {
        var option = document.createElement("option");
        option.value = currentYear + i;
        option.text = currentYear + i;
        selectElement.appendChild(option);
    }
});