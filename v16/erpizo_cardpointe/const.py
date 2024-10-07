# Part of Odoo. See LICENSE file for full copyright and licensing details.

# The codes of the payment methods to activate when Authorize is activated.
DEFAULT_PAYMENT_METHODS_CODES = [
    # Primary payment methods.
    'cardpointe',
    'card',
    # Brand payment methods.
    'visa',
    'mastercard',
    'amex',
    'discover',
]

# Mapping of payment method codes to Authorize codes.
PAYMENT_METHODS_MAPPING = {
    'amex': 'americanexpress',
    'diners': 'dinersclub',
    'card': 'creditcard'
}

