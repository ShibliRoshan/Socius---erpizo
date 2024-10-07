from . import controllers
from . import models
from . import wizard
from odoo.addons.payment import reset_payment_provider


def uninstall_hook(cr, registry):
    reset_payment_provider(cr, registry, "cardpointe")
