
from __future__ import with_statement
from decimal import Decimal
from trytond.model import ModelView, ModelSQL, ModelWorkflow, fields
from trytond.wizard import Wizard
from trytond.report import Report
from trytond.tools import reduce_ids
from trytond.pyson import Equal, Eval, Not, PYSONEncoder, Date, Bool, If, In, Get
from trytond.transaction import Transaction

import datetime
import time
import logging

log = logging.getLogger(__name__)

STATES = {
    'readonly': Not(Equal(Eval('state'), 'draft')),
}

class Contract(ModelWorkflow, ModelSQL, ModelView):
    """Contract Agreement"""
    _name = 'contract.contract'
    _description = __doc__

    company = fields.Many2One('company.company', 'Company', required=True,
                         states=STATES, select=1, domain=[
                             ('id', If(In('company', Eval('context', {})), '=', '!='),
                              Get(Eval('context', {}), 'company', 0)),
                         ])

    journal = fields.Many2One('account.journal', 'Journal', required=True,                                                                                                             
                                      states=STATES, domain=[('centralised', '=', False)])

    name = fields.Char('Name', required=True, translate=True)

    description = fields.Char('Description', size=None, translate=True)

    party = fields.Many2One('party.party', 'Party', required=True, 
                            states=STATES)
    product = fields.Many2One('product.product', 'Product', required=True,
                              states=STATES)
    account = fields.Many2One('account.account', 'Account',
                              states={
                                  'invisible': Bool(Eval('account_product')),
                                  'required': Not(Bool(Eval('account_product'))),
                              }
                             )
    account_product = fields.Boolean('Use Product\'s account')
    payment_term = fields.Many2One('account.invoice.payment_term',
                                   'Payment Term', required=True,
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
    interval_quant = fields.Integer('Interval count', states=STATES)
    next_invoice_date = fields.Date('Next Invoice', states=STATES)
    start_date = fields.Date('Since', states=STATES)
    stop_date = fields.Date('Until')
    lines = fields.One2Many('account.invoice.line', 'contract', 'Invoice Lines',
                           readonly=True, domain=[('contract','=',Eval('id'))])

    def default_state(self):
        return 'draft'

    def default_interval(self):
        return 'month'

    def default_account_product(self):
        return True

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

class CreateNextInvoice(Wizard):
    'Create Next Invoice'
    _name='contract.contract.create_next_invoice'
    states = {
        'init': {
            'actions': ['_next_invoice'],
            'result': {
                'type': 'state',
                'state': 'end',
            },
        },
    }

    def _next_invoice(self, data):
        id = data.get('id')
        contract_obj = self.pool.get('contract.contract')
        contract = contract_obj.browse([id])[0]
        if not contract.state == 'active':
            return {}

        invoice_obj = self.pool.get('account.invoice')
        line_obj = self.pool.get('account.invoice.line')

        invoice_addr = contract.party.addresses[0]
        for addr in contract.party.addresses:
            if addr.invoice == True:
                invoice_addr = addr
                break

        today = datetime.date.fromtimestamp(time.time())

        last_date = contract.next_invoice_date or contract.start_date or today

        if contract.interval == 'year':
            next_date = datetime.date(last_date.year + contract.interval_quant,
                                      last_date.month, 
                                      last_date.day)
        elif contract.interval == 'month':
            next_year = last_date.year + (last_date.month + int(contract.interval_quant)) / 12
            next_month = (last_date.month + int(contract.interval_quant)) % 12 
            next_date = datetime.date(next_year, next_month, last_date.day)

        elif contract.interval == 'week':
            delta = datetime.timedelta(0,0,0,0,0,0,contract.interval_quant)
            next_date = last_date + delta

        elif contract.interval == 'day':
            next_date = last_date + datetime.timedelta(contract.interval_quant)

        if contract.next_invoice_date and today + datetime.timedelta(30) < contract.next_invoice_date:
            log.info('too early to invoice: %s + 30 days < %s', today, next_date)
            return {}

        ## create a new invoice
        invoice = invoice_obj.create(dict(
            company=contract.company.id,
            type='out_invoice',
            reference=contract.product.code or contract.product.name,
            description=contract.description or contract.name,
            state='draft',
            currency=contract.company.currency.id,
            journal=contract.journal.id,
            account=contract.party.account_receivable.id,
            payment_term=contract.party.payment_term.id,
            party=contract.party.id,
            invoice_address=invoice_addr.id
        ))

        ## create invoice line
        account = contract.account or \
                contract.product.account_revenue or \
                contract.product.category.account_revenue

        line = line_obj.create(dict(
            type='line',
            product=contract.product.id,
            invoice=invoice,
            description="%s (%s) %s - %s" % (contract.product.description or
                                             contract.product.name,
                                             contract.name,
                                             last_date, next_date),
            quantity=contract.interval_quant,
            account=account.id,
            unit=contract.product.default_uom.id,
            unit_price=contract.product.list_price,
            contract=contract.id,
        ))

        ## open invoice
        invoice = invoice_obj.browse([invoice])[0]
        invoice.write(invoice.id, {'invoice_date': today})
        invoice.workflow_trigger_validate(invoice.id, 'draft')

        ## update fields
        contract.write(contract.id, {'next_invoice_date': next_date})

        return {}

CreateNextInvoice()



