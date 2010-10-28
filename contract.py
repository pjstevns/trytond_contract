
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
                            states=STATES, on_change=['party'])
    product = fields.Many2One('product.product', 'Product', required=True,
                              states=STATES)
    list_price = fields.Numeric('List Price', states=STATES,
                                digits=(16, 4),
                               help='''Fixed-price override. Leave at 0.0000 for no override. Use discount at 100% to set actual price to 0.0''')
    discount = fields.Numeric('Discount (%)', states=STATES,
                              digits=(4,2),
                             help='Discount percentage on the list_price')
    quantity = fields.Numeric('Quantity', digits=(16,2), states=STATES)
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


    def __init__(self):
        super(Contract, self).__init__()
        self._rpc.update({
            'create_next_invoice': True,
            'create_invoice_batch': True,
            'cancel_with_credit': True,
        })

    def default_state(self):
        return 'draft'

    def default_interval(self):
        return 'month'

    def default_quantity(self):
        return Decimal('1.0')

    def default_company(self):
        return Transaction().context.get('company') or False

    def default_start_date(self):
        return datetime.date.fromtimestamp(time.time())

    def default_interval_quant(self):
        return Decimal("3.0")

    def default_payment_term(self):
        company_id = self.default_company()
        company_obj = self.pool.get('company.company')
        company = company_obj.browse(company_id)
        if company and company.payment_term:
            return company.payment_term.id
        return False

    def default_journal(self):
        journal_obj = self.pool.get('account.journal')
        journal_ids = journal_obj.search([('type','=','revenue')], limit=1)
        if journal_ids:
            return journal_ids[0]
        return False

    def on_change_party(self, vals):
        party_obj = self.pool.get('party.party')
        address_obj = self.pool.get('party.address')
        payment_term_obj = self.pool.get('account.invoice.payment_term')
        res = {
            'invoice_address': False,
        }
        if vals.get('party'):
            party = party_obj.browse(vals['party'])
            payment_term = party.payment_term or False
            if payment_term:
                res['payment_term'] = payment_term.id
                res['payment_term.rec_name'] = payment_term_obj.browse(
                    res['payment_term']).rec_name
        return res

    def write(self, ids, vals):
        super(Contract, self).write(ids, vals)
        if 'state' in vals:
            self.workflow_trigger_trigger(ids)

        return None

    def _invoice_init(self, contract):
        invoice_obj = self.pool.get('account.invoice')
        invoice_address = contract.party.address_get(contract.party.id, type='invoice')
        invoice = invoice_obj.create(dict(
            company=contract.company.id,
            type='out_invoice',
            reference=contract.product.code or contract.product.name,
            description=contract.description or contract.name,
            state='draft',
            currency=contract.company.currency.id,
            journal=contract.journal.id,
            account=contract.party.account_receivable.id or contract.company.account_receivable.id,
            payment_term=contract.payment_term.id or contract.party.payment_term.id,
            party=contract.party.id,
            invoice_address=invoice_address,
        ))
        return invoice_obj.browse([invoice])[0]

    def _invoice_append(self, invoice, contract, period):
        (last_date, next_date) = period
        line_obj = self.pool.get('account.invoice.line')
        linedata = dict(
            type='line',
            product=contract.product.id,
            invoice=invoice.id,
            description="%s (%s) %s - %s" % (contract.product.description or
                                             contract.product.name,
                                             contract.name,
                                             last_date, next_date),
            quantity=Decimal("%f" % (contract.interval_quant * contract.quantity)),
            unit=contract.product.default_uom.id,
            unit_price=contract.product.list_price,
            contract=contract.id,
            taxes=[],
        )

        account = contract.product.get_account([contract.product.id],'account_revenue_used')
        if account: 
            linedata['account'] = account.popitem()[1]

        taxes = contract.product.get_taxes([contract.product.id], 'customer_taxes_used')
        for tax in taxes.items():
            linedata['taxes'].append(('add',tax[1]))

        return line_obj.create(linedata)

    def cancel_with_credit(self, ids):
        """ 
        
        Contract is canceled. Open invoices are credited.
        i.e. in case of failure to provide proper and
        valid credentials such as an initial payment.

        """
        contract_obj = self.pool.get('contract.contract')
        contract = self.browse(ids)[0]
        if not contract.state == 'active':
            return {}

        for id in ids:
            self.workflow_trigger_validate(id, 'cancel')

        invoice_obj = self.pool.get('account.invoice')
        invoice_line_obj = self.pool.get('account.invoice.line')
        line_ids = invoice_line_obj.search([('contract','in',ids)])
        if not line_ids:
            return {}

        invoices = []
        lines = invoice_line_obj.browse(line_ids)
        for l in lines:
            invoices.append(l.invoice.id)
        invoice_obj.credit(invoices, refund=True)

        return {}


    def create_next_invoice(self, ids):
        contract_obj = self.pool.get('contract.contract')
        contract = self.browse(ids)[0]

        if not contract.state == 'active':
            return {}

        period = self._check_contract(contract)
        if not period:
            return {}

        (last_date, next_date) = period
        today = datetime.date.fromtimestamp(time.time())

        ## create a new invoice
        invoice = self._invoice_init(contract)
        ## create invoice line
        line = self._invoice_append(invoice, contract, (last_date, next_date))

        ## open invoice
        invoice.write(invoice.id, {'invoice_date': today})
        self.write(contract.id, {'next_invoice_date': next_date})

        return invoice.id


    def _check_contract(self, contract):
        """
        returns tuple 'period' or False 

        False is returned if this contract is not up for billing at this 
        moment.

        period is defined as (last_date, next_date) 
        which are datetime values indicating the next billing period this
        contract is due for.

        """
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
            return False

        if next_date and contract.stop_date and next_date >= contract.stop_date:
            log.info('contract stopped: %s >= %s' % (next_date, contract.stop_date))
            return False

        return (last_date, next_date)


    def create_invoice_batch(self, party=None):
        now = datetime.date.fromtimestamp(time.time())
        end = now + datetime.timedelta(30)
        
        """ 
        get a list of all active contracts
        """
        contract_obj = self.pool.get('contract.contract')
        query = [('state','=','active'), 
                 ('start_date','<=',now),
                ]

        """
        filter on party if required
        """
        if party:
            if type(party) != type([1,]):
                party = [party,]
            query.append(('party','in',party))

        contract_ids = contract_obj.search(query)

        if not contract_ids:
            return []

        """
        build the list of all billable contracts
        and aggragate the result per party
        """
        batch = {}
        contracts = contract_obj.browse(contract_ids)
        for contract in contracts:
            period = self._check_contract(contract)
            if period:
                key = contract.party.id
                if not batch.get(key): batch[key] = []
                batch[key].append((contract, period))

        """
        create draft invoices per party with lines
        for all billable contracts
        """
        res = []
        for party, info in batch.items():
            invoice = self._invoice_init(info[0][0])
            for (contract, period) in info:
                self._invoice_append(invoice, contract, period)
                self.write(contract.id, {'next_invoice_date': period[1]})
            invoice.write(invoice.id, {'invoice_date': now})
            res.append(invoice.id)
        return res
 

Contract()

class InvoiceLine(ModelSQL, ModelView):
    """Invoice Line"""
    _name = 'account.invoice.line'
    contract = fields.Many2One('contract.contract', 'Contract')

InvoiceLine()

class Party(ModelSQL, ModelView):
    """Party"""
    _name = 'party.party'
    contracts = fields.One2Many('contract.contract', 'party', 'Contracts',
                               readonly=True)

Party()

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
        contract_obj = self.pool.get('contract.contract')
        contract_obj.create_next_invoice([data['id']])
        return {}

CreateNextInvoice()


class CreateInvoiceBatch(Wizard):
    'Create Invoice Batch'
    _name='contract.contract.create_invoice_batch'
    states = {
        'init': {
            'actions': ['_invoice_batch'],
            'result': {
                'type': 'state',
                'state': 'end',
            },
        },
    }

    def _invoice_batch(self, data):
        contract_obj = self.pool.get('contract.contract')
        contract_obj.create_invoice_batch()
        return {}

CreateInvoiceBatch()
