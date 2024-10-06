/** @odoo-module **/

    import paymentForm from '@payment/js/payment_form';
    import publicWidget from "@web/legacy/js/public/public_widget";
    import {_t} from "@web/core/l10n/translation";
    import {jsonrpc, RPCError} from "@web/core/network/rpc_service";


    publicWidget.registry.CardPointefee = publicWidget.Widget.extend({
        selector: '#payment_method',
        events: {
            'change .o_payment_option_card': '_changePaymentForm',
            'click .o_payment_option_card': '_changePaymentForm',
            'change .o_payment_form input[name="payment_mode"]': '_changePaymentMode',
            'click .o_payment_submit_button': '_changePaymentMode',
            'click .o_payment_option_label': '_changePaymentLabelMode',
            'click .o_payment_form input[name="o_payment_expand_button"]': '_changePaymentLabelMode',

        },

        start: function() {
            var paymentCardInput = $('.o_payment_form input[id="payment_card"][value="card"]');
            var orderTotalWithFee = $('.order_total_with_fee');
            var orderTotalTaxesWithFee = $('.order_total_taxes_with_fee');
            var orderTotalWithoutFee = $('.order_total_without_fee');
            var orderTotalWithFeeAch = $('.order_total_with_fee_ach');
            var isCheckedCardpointe = $('.o_payment_form input[name="o_payment_radio"]:checked').attr('data-provider-code') === 'cardpointe';


            orderTotalWithFee.css('display', 'none');
            orderTotalTaxesWithFee.css('display', 'none');
            orderTotalWithFeeAch.css('display', 'revert');
            orderTotalWithoutFee.css('display', 'revert');


            var isCheckedCardpointe = $('.o_payment_form input[name="o_payment_radio"]:checked').attr('data-provider-code') === 'cardpointe';
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
            console.log('cardddd22222')
                document.getElementById('fee_badge').style.display = 'inline-block';
            } else if ($(ev.target).val() === 'ach') {
            console.log('accchhh222')
                document.getElementById('fee_badge').style.display = 'none';
            }
        },

        _changePaymentLabelMode: function(ev) {
            var paymentCardInput = $('.o_payment_form input[id="payment_card"][value="card"]');
            paymentCardInput.prop('checked', true);
            var orderTotalWithFee = $('.order_total_with_fee');
            var orderTotalTaxesWithFee = $('.order_total_taxes_with_fee');
            var orderTotalWithoutFee = $('.order_total_without_fee');
            var orderTotalWithFeeAch = $('.order_total_with_fee_ach');
            if (($('.o_payment_form input[name="o_payment_radio"]:checked').attr('data-provider-code')) == 'cardpointe')
            {
                orderTotalWithFee.css('display', 'none');
                orderTotalTaxesWithFee.css('display', 'none');
                orderTotalWithFeeAch.css('display', 'revert');
                orderTotalWithoutFee.css('display', 'revert');
            } else {
                 orderTotalWithFee.css('display', 'revert');
                orderTotalTaxesWithFee.css('display', 'revert');
                orderTotalWithFeeAch.css('display', 'none');
                orderTotalWithoutFee.css('display', 'none');
            }
        },

        _changePaymentForm: function(ev) {
            var paymentCardInput = $('.o_payment_form input[id="payment_card"][value="card"]');
            var orderTotalWithFee = $('.order_total_with_fee');
            var orderTotalTaxesWithFee = $('.order_total_taxes_with_fee');
            var orderTotalWithoutFee = $('.order_total_without_fee');
            var orderTotalWithFeeAch = $('.order_total_with_fee_ach');
            var isCheckedCardpointe = $('.o_payment_form input[name="o_payment_radio"]:checked').attr('data-provider-code') === 'cardpointe';

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

    publicWidget.registry.CardPointefeeForm = publicWidget.Widget.extend({
        selector: '#o_payment_form',
        events: {
            'change .o_payment_option_card': '_changePaymentForm',
            'click .o_payment_option_card': '_changePaymentForm',
            'change .o_payment_form input[name="payment_mode"]': '_changePaymentMode',
            'click .o_payment_submit_button': '_changePaymentMode',
            'click .o_payment_option_label': '_changePaymentLabelMode',
            'click .o_payment_form input[name="o_payment_expand_button"]': '_changePaymentLabelMode',

        },

        start: function() {
            var paymentCardInput = $('.o_payment_form input[id="payment_card"][value="card"]');
            var orderTotalWithFee = $('.order_total_with_fee');
            var orderTotalTaxesWithFee = $('.order_total_taxes_with_fee');
            var orderTotalWithoutFee = $('.order_total_without_fee');
            var orderTotalWithFeeAch = $('.order_total_with_fee_ach');
            var isCheckedCardpointe = $('.o_payment_form input[name="o_payment_radio"]:checked').attr('data-provider-code') === 'cardpointe';


            orderTotalWithFee.css('display', 'none');
            orderTotalTaxesWithFee.css('display', 'none');
            orderTotalWithFeeAch.css('display', 'revert');
            orderTotalWithoutFee.css('display', 'revert');


            var isCheckedCardpointe = $('.o_payment_form input[name="o_payment_radio"]:checked').attr('data-provider-code') === 'cardpointe';
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
                console.log('cardddd')
                document.getElementById('fee_badge').style.display = 'inline-block';
            } else if ($(ev.target).val() === 'ach') {
                console.log('aaccchhhhh')
                document.getElementById('fee_badge').style.display = 'none';
            }
        },

        _changePaymentLabelMode: function(ev) {
            var paymentCardInput = $('.o_payment_form input[id="payment_card"][value="card"]');
            paymentCardInput.prop('checked', true);
            var orderTotalWithFee = $('.order_total_with_fee');
            var orderTotalTaxesWithFee = $('.order_total_taxes_with_fee');
            var orderTotalWithoutFee = $('.order_total_without_fee');
            var orderTotalWithFeeAch = $('.order_total_with_fee_ach');
            if (($('.o_payment_form input[name="o_payment_radio"]:checked').attr('data-provider-code')) == 'cardpointe')
            {
                orderTotalWithFee.css('display', 'none');
                orderTotalTaxesWithFee.css('display', 'none');
                orderTotalWithFeeAch.css('display', 'revert');
                orderTotalWithoutFee.css('display', 'revert');
            } else {
                 orderTotalWithFee.css('display', 'revert');
                orderTotalTaxesWithFee.css('display', 'revert');
                orderTotalWithFeeAch.css('display', 'none');
                orderTotalWithoutFee.css('display', 'none');
            }
        },

        _changePaymentForm: function(ev) {
            var paymentCardInput = $('.o_payment_form input[id="payment_card"][value="card"]');
            var orderTotalWithFee = $('.order_total_with_fee');
            var orderTotalTaxesWithFee = $('.order_total_taxes_with_fee');
            var orderTotalWithoutFee = $('.order_total_without_fee');
            var orderTotalWithFeeAch = $('.order_total_with_fee_ach');
            var isCheckedCardpointe = $('.o_payment_form input[name="o_payment_radio"]:checked').attr('data-provider-code') === 'cardpointe';

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