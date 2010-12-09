
from __future__ import with_statement
from trytond.model import ModelView, fields
from trytond.wizard import Wizard

import logging

log = logging.getLogger(__name__)


class InvoiceBatchActionInit(ModelView):
    'Invoice Batch Action'
    _name = 'account.invoice.invoice_batch_action.init'
    _description = __doc__
    signal = fields.Selection([
        ('proforma','Proforma'),
        ('draft','Draft'),
        ('open', 'Open'),
        ('cancel','Cancel'),
    ], 'Change Invoice', help='Trigger workflow signal for all selected invoices' )

InvoiceBatchActionInit()

class InvoiceBatchAction(Wizard):
    'Trigger action on batch of invoices'
    _name='account.invoice.invoice_batch_action'
    states = {
        'init': {
            'result': {
                'actions': ['_init'],
                'type': 'form',
                'object': 'account.invoice.invoice_batch_action.init',
                'state': [
                    ('end', 'Cancel', 'tryton-cancel'),
                    ('modify', 'Modify Invoices', 'tryton-ok', True),
                ],
            }
        },

        'modify': {
            'actions': ['_batch_action'],
            'result': {
                'type': 'state',
                'state': 'end',
            },
        },
    }

    def _batch_action(self, data):
        log.debug("_batch_action: %s" % data)
        invoice_obj = self.pool.get('account.invoice')
        signal = None
        if data.get('form') and data['form'].get('signal'):
            signal = data['form']['signal']
        else:
            return {}
        for id in data.get('ids'):
            invoice_obj.workflow_trigger_validate(id, signal)
        return {}

InvoiceBatchAction()
