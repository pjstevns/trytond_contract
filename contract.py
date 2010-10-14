
from __future__ import with_statement
from decimal import Decimal
from trytond.model import ModelView, ModelSQL, ModelWorkflow, fields
from trytond.wizard import Wizard
from trytond.report import Report
from trytond.tools import reduce_ids
from trytond.pyson import Equal, Eval, Not, PYSONEncoder, Date, Bool
from trytond.transaction import Transaction

import logging

log = logging.getLogger(__name__)

STATES = {
    'readonly': Not(Equal(Eval('state'), 'draft')),
}

class Contract(ModelWorkflow, ModelSQL, ModelView):
    """Contract Agreement"""
    _name = 'contract.contract'
    _description = __doc__

    name = fields.Char('Name', required=True, translate=True)
    party = fields.Many2One('party.party', 'Party', required=True, 
                            states=STATES)
    product = fields.Many2One('product.product', 'Product', required=True,
                              states=STATES)
    state = fields.Selection([
        ('draft','Draft'),
        ('active','Active'),
        ('canceled','Canceled'),
    ], 'State', readonly=True)
    interval = fields.Selection([
        ('day','Day'),
        ('week','Week'),
        ('month','Month'),
        ('year','Year'),
    ], 'Interval', required=True, states=STATES)
    interval_quant = fields.Numeric('Interval count', digits=(16,2),
                                    states=STATES)
    next_invoice_date = fields.Date('Next Invoice', states=STATES)
    start_date = fields.Date('Since', states=STATES)
    stop_date = fields.Date('Until')
    lines = fields.One2Many('account.invoice.line', 'contract', 'Invoice Lines')

    def default_state(self):
        return 'draft'

    def default_interval(self):
        return 'month'

    def default_interval_quant(self):
        return Decimal("3.0")

    def write(self, ids, vals):
        log.info("%s:%s" % ( ids, vals))
        super(Contract, self).write(ids, vals)
        if 'state' in vals:
            self.workflow_trigger_trigger(ids)

        return None

Contract()


class InvoiceLine(ModelSQL, ModelView):
    """Invoice Line"""
    _name = 'account.invoice.line'
    contract = fields.Many2One('contract.contract', 'Contract')


InvoiceLine()


