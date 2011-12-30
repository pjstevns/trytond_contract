
from __future__ import with_statement
from trytond.model import ModelSQL, ModelView, fields
from trytond.wizard import Wizard
from trytond.pool import Pool

import logging

log = logging.getLogger(__name__)

class Invoice(ModelSQL, ModelView):
    """Invoice"""
    _name = 'account.invoice'

    def set_next_invoice_date(self, ids, trigger_id):
        """Set next_invoice_date on contracts connected to invoice lines"""
        pool = Pool()
        invoice_obj = pool.get('account.invoice')
        invoice_line_obj = pool.get('account.invoice.line')
        contract_obj = pool.get('contract.contract')

        log.debug("set_next_invoice_date %s %s" %(ids, trigger_id))
        invoices = invoice_obj.browse(ids)
        for invoice in invoices:
            for invoice_line in invoice.lines:
                contract = invoice_line.contract
                if contract:
                    next_date = contract.opt_invoice_date
                    log.debug("set next_invoice_date %s %s" %(contract,
                                                              next_date))
                    contract_obj.write(contract.id, {'next_invoice_date': next_date})
        return

Invoice()

class InvoiceLine(ModelSQL, ModelView):
    """Invoice Line"""
    _name = 'account.invoice.line'

    contract = fields.Many2One('contract.contract', 'Contract', readonly=True)



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
        pool = Pool()
        log.debug("_batch_action: %s" % data)
        invoice_obj = pool.get('account.invoice')
        signal = None
        if data.get('form') and data['form'].get('signal'):
            signal = data['form']['signal']
        else:
            return {}
        for id in data.get('ids'):
            invoice_obj.workflow_trigger_validate(id, signal)
        return {}

InvoiceBatchAction()
