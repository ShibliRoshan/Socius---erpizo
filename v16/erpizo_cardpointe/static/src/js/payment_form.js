odoo.define('erpizo_cardpointe.payment_form', require => {
    'use strict';

    const core = require('web.core');
    const checkoutForm = require('payment.checkout_form');
    const manageForm = require('payment.manage_form');
    var publicWidget = require('web.public.widget');
    const _t = core._t;
    var ajax = require('web.ajax');

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
        console.log('start______Start');
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
            return this._super(...arguments);

        },
        _changePaymentMode: function(ev) {
            if ($(ev.target).val() === 'card') {
                $('.o_payment_form input[name="o_payment_save_as_token"]').parent().show();

                document.getElementById('card_payment_fields').style.display = 'block';
                document.getElementById('ach_payment_fields').style.display = 'none';
                document.getElementById('acc_number').value = "";
                document.getElementById('routing_number').value = "";

            } else if ($(ev.target).val() === 'ach') {
                document.getElementById('card_payment_fields').style.display = 'none';
                $('.o_payment_form input[name="o_payment_save_as_token"]').parent().hide();

                document.getElementById('ach_payment_fields').style.display = 'block';
                document.getElementById('card_number').value = "";
                document.getElementById('cvv_number').value = "";
            }


        },
    });


publicWidget.registry.CardPointeForm = publicWidget.Widget.extend({
     selector: '#payment_method',
        events: {
            'change .o_payment_form input[name="payment_mode"]': '_changePaymentMode',
            'click .o_payment_submit_button': '_changePaymentMode',
        },

    start: function() {
        console.log('start!!!!!!!!!!!!!!!');

        return this._super(...arguments);

    },

     _changePaymentMode: function(ev) {
            console.log('_changePaymentMode',self,this)
            if ($(ev.target).val() === 'card') {
                $('.o_payment_form input[name="o_payment_save_as_token"]').parent().show();
                document.getElementById('card_payment_fields').style.display = 'block';
                document.getElementById('ach_payment_fields').style.display = 'none';
                document.getElementById('acc_number').value = "";
                document.getElementById('routing_number').value = "";

            } else if ($(ev.target).val() === 'ach') {
                document.getElementById('card_payment_fields').style.display = 'none';
                $('.o_payment_form input[name="o_payment_save_as_token"]').parent().hide();

                document.getElementById('ach_payment_fields').style.display = 'block';
                document.getElementById('card_number').value = "";
                document.getElementById('cvv_number').value = "";
            }


        },

});


    const cardpointeMixin = {
        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * Simulate a feedback from a payment provider and redirect the customer to the status page.
         *
         * @override method from payment.payment_form_mixin
         * @private
         * @param {string} code - The code of the selected payment option's provider
         * @param {number} paymentOptionId - The id of the selected payment option
         * @param {object} processingValues - The processing values of the transaction
         * @return {Promise}
         */
        _processTokenPayment: (code, tokenId, processingValues) => {
            console.log("_processTokenPayment111111")
            if (code !== 'cardpointe') {
                window.location = '/payment/status';
            }
            const payment_mode = document.querySelector('input[name="payment_mode"]:checked').value;
            const requestData = {
                'tokenId': tokenId,
                'flow': 'token',
                'amount': processingValues.amount,
                'currency_id': processingValues.currency_id,
                'partner_id': processingValues.partner_id,
                'provider_code': processingValues.provider_code,
                'provider_id': processingValues.provider_id,
                'reference': processingValues.reference,



            };
            return ajax.rpc("/payment/cardpointe", requestData).then(function() {
                window.location = '/payment/status';
            });

        },

        _processDirectPayment: function(code, paymentOptionId, processingValues) {
            console.log('_processDirectPayment')
            if (code !== 'cardpointe') {
                return this._super(...arguments);
            }

            var landingRoute = $('.o_payment_form').data('landing-route');
            console.log(landingRoute);

            var transaction_values = this._prepareTransactionRouteParams(processingValues.provider_id)


            const cc_number = document.getElementById('card_number').value;
            const cc_expiry_month = document.getElementById('expiry_month').value;
            const cc_expiry_year = document.getElementById('expiry_year').value;
            const cc_cvc = document.getElementById('cvv_number').value;
            const account_number = document.getElementById('acc_number').value;
            const routing_number = document.getElementById('routing_number').value;
            const payment_mode = document.querySelector('input[name="payment_mode"]:checked').value;
            const cc_expiry = cc_expiry_month && cc_expiry_year ? `${cc_expiry_month}/${cc_expiry_year}` : null;
            const invalidInputs = [];
            console.log("cc_number",cc_number)
            console.log("account_number",account_number)
            console.log("payment_mode",payment_mode)
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

            if ((cc_number && cc_expiry && cc_cvc) || (account_number && routing_number)) {
                const params = {
                    'reference': processingValues.reference,
                    'acquirer_id': paymentOptionId,
                    'partner_id': processingValues.partner_id,
                    'cc_number': payment_mode === 'card' ? cc_number : account_number,
                    'cc_expiry': cc_expiry,
                    'routing_number': routing_number,
                    'token': cc_number,
                    'cc_cvc': cc_cvc,
                    'payment_mode': payment_mode,
                    'flow': 'direct',
                    'landingRoute': landingRoute === '/my/payment_method' ? landingRoute: false,
                    'tokenization_requested':  transaction_values.tokenization_requested


                };

                return this._rpc({
                    route: '/payment/cardpointe',
                    params: params,
                }).then(paymentResponse => {
                    if (paymentResponse && paymentResponse.error) {
                        this._displayError(
                            _t("Server Error"),
                            _t("We are not able to process your payment."),
                            paymentResponse.error
                        );
                    } else {
                        window.location = '/payment/status';
                    }
                }).guardedCatch(error => {
                    error.event.preventDefault();
                    this._displayError(
                        _t("Server Error"),
                        _t("We are not able to process your payment."),
                        error.message.data.message
                    );
                });
            } else {
                return this._displayError(
                    _t("Server Error"),
                    _t("Please Check/Fill card details"),
                );
            }
        },



        /**
         * Prepare the inline form for Cardpointe payment.
         *
         * @override method from payment.payment_form_mixin
         * @private
         * @param {string} provider - The provider of the selected payment option's acquirer
         * @param {integer} paymentOptionId - The id of the selected payment option
         * @param {string} flow - The online payment flow of the selected payment option
         * @return {Promise}
         */
        _prepareInlineForm: function(provider, paymentOptionId, flow) {
            if (provider !== 'cardpointe') {
                return this._super(...arguments);
            } else if (flow === 'token') {
                return Promise.resolve();
            }
            this._setPaymentFlow('direct');
            return Promise.resolve()
        },
    };

    checkoutForm.include(cardpointeMixin);
    manageForm.include(cardpointeMixin);
});

$(document).ready(function() {
    function changePaymentMode(ev) {
        console.log('Payment mode changed:', $(ev.target).val());
        if ($(ev.target).val() === 'card') {
            $('#card_payment_fields').show();
            $('#ach_payment_fields').hide();
            $('#acc_number').val('');
            $('#routing_number').val('');
        } else if ($(ev.target).val() === 'ach') {
            $('#card_payment_fields').hide();
            $('#ach_payment_fields').show();
            $('#card_number').val('');
            $('#cvv_number').val('');
        }
    }

    // Ensure the select element exists before manipulating it
    var selectElement = document.getElementById("expiry_year");

    if (selectElement) {
        // Get the current year
        var currentYear = new Date().getFullYear();

        // Loop to add options for the next 30 years
        for (var i = 0; i < 30; i++) {
            var option = document.createElement("option");
            option.value = currentYear + i;
            option.text = currentYear + i;
            selectElement.appendChild(option);
        }
    } else {
        console.error('selectElement with id "expiry_year" not found.');
    }

    // Set 'card' as the initial payment mode and trigger the change event
    const initialPaymentMode = 'card';
    const paymentModeElement = $('input[name="payment_mode"][value="' + initialPaymentMode + '"]');
    if (paymentModeElement.length) {
        paymentModeElement.prop('checked', true);
        console.log('Initial payment mode:', initialPaymentMode);
        changePaymentMode({ target: paymentModeElement.get(0) });
    } else {
        console.error('Payment mode with value "card" not found.');
    }

    // Attach event handlers
    $('.o_payment_form').on('change', 'input[name="payment_mode"]', changePaymentMode);
});
