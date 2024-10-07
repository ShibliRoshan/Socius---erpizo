odoo.define('erpizo_cardpointe_fee.payment_fee', require => {
    'use strict';

    const core = require('web.core');
    const checkoutForm = require('payment.checkout_form');
    const manageForm = require('payment.manage_form');
    var publicWidget = require('web.public.widget');
    const _t = core._t;
    var ajax = require('web.ajax');

    publicWidget.registry.CardPointefee = publicWidget.Widget.extend({
        selector: '#payment_method',
        events: {
            'change .o_payment_option_card': '_changePaymentForm',
            'click .o_payment_option_card': '_changePaymentForm',
            'change .o_payment_form input[name="payment_mode"]': '_changePaymentMode',
            'click .o_payment_submit_button': '_changePaymentMode',

        },

        start: function() {
            var paymentCardInput = $('.o_payment_form input[id="payment_card"][value="card"]');
            var orderTotalWithFee = $('.order_total_with_fee');
            var orderTotalTaxesWithFee = $('.order_total_taxes_with_fee');
            var orderTotalWithoutFee = $('.order_total_without_fee');
            var orderTotalWithFeeAch = $('.order_total_with_fee_ach');
            var isCheckedCardpointe = $('.o_payment_form input[name="o_payment_radio"]:checked').attr('data-provider') === 'cardpointe';


            paymentCardInput.prop('checked', false);
                orderTotalWithFee.css('display', 'none');
                orderTotalTaxesWithFee.css('display', 'none');
                orderTotalWithFeeAch.css('display', 'revert');
                orderTotalWithoutFee.css('display', 'revert');
            var isCheckedCardpointe = $('.o_payment_form input[name="o_payment_radio"]:checked').attr('data-provider') === 'cardpointe';
            if (isCheckedCardpointe) {
                paymentCardInput.prop('checked', true);
                orderTotalWithFee.css('display', 'revert');
                orderTotalTaxesWithFee.css('display', 'revert');
                orderTotalWithFeeAch.css('display', 'none');
                orderTotalWithoutFee.css('display', 'none');
            } else {
                paymentCardInput.prop('checked', false);
                orderTotalWithFee.css('display', 'none');
                orderTotalTaxesWithFee.css('display', 'none');
                orderTotalWithFeeAch.css('display', 'revert');
                orderTotalWithoutFee.css('display', 'revert');
            }
            return this._super(...arguments);
        },


        _changePaymentMode: function(ev) {
            if ($(ev.target).val() === 'card') {
                document.getElementById('fee_badge').style.display = 'inline-block';
            } else if ($(ev.target).val() === 'ach') {
                document.getElementById('fee_badge').style.display = 'none';
            }
        },

        _changePaymentForm: function(ev) {
            var paymentCardInput = $('.o_payment_form input[id="payment_card"][value="card"]');
            var orderTotalWithFee = $('.order_total_with_fee');
            var orderTotalTaxesWithFee = $('.order_total_taxes_with_fee');
            var orderTotalWithoutFee = $('.order_total_without_fee');
            var orderTotalWithFeeAch = $('.order_total_with_fee_ach');
            var isCheckedCardpointe = $('.o_payment_form input[name="o_payment_radio"]:checked').attr('data-provider') === 'cardpointe';

            if (isCheckedCardpointe) {
                paymentCardInput.prop('checked', true);
                orderTotalWithFee.css('display', 'revert');
                orderTotalTaxesWithFee.css('display', 'revert');
                orderTotalWithFeeAch.css('display', 'none');
                orderTotalWithoutFee.css('display', 'none');
            } else {
                paymentCardInput.prop('checked', false);
                orderTotalWithFee.css('display', 'none');
                orderTotalTaxesWithFee.css('display', 'none');
                orderTotalWithFeeAch.css('display', 'revert');
                orderTotalWithoutFee.css('display', 'revert');
            }

        },


    });
});



$(document).ready(function() {
    // Listen for changes in the payment mode input field
    $('.o_payment_form input[name="payment_mode"]').change(function() {
        // Get the current value of the payment mode
        var paymentMode = $(this).val();

        // Select the elements by their class names
        var orderTotalWithFee = $('.order_total_with_fee');
        var orderTotalTaxesWithFee = $('.order_total_taxes_with_fee');
        var orderTotalWithoutFee = $('.order_total_without_fee');
        var order_total_with_fee_ach = $('.order_total_with_fee_ach');

        // Check the payment mode and show/hide the fee row accordingly
        if (paymentMode === "card") {
            // If payment mode is "card", show the fee row
            orderTotalWithFee.css('display', 'revert');
            orderTotalTaxesWithFee.css('display', 'revert');
            orderTotalWithoutFee.css('display', 'none');
            order_total_with_fee_ach.css('display', 'none');
        } else {
            // If payment mode is "ach", hide the fee row
            orderTotalWithFee.css('display', 'none');
            orderTotalTaxesWithFee.css('display', 'none');
            order_total_with_fee_ach.css('display', 'revert');
            orderTotalWithoutFee.css('display', 'revert');
        }
    });

    // Trigger the change event once on page load to initialize the fee row visibility
    $('.o_payment_form input[name="payment_mode"]').change();

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
