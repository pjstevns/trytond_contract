
from __future__ import with_statement
from decimal import Decimal
from trytond.model import ModelView, ModelSQL, fields
from trytond.wizard import Wizard
from trytond.report import Report
from trytond.tools import reduce_ids
from trytond.pyson import Equal, Eval, Not, PYSONEncoder, Date
from trytond.transaction import Transaction


STATES = {
    'readonly':  Not(Equal(Eval('active'))),
}

class Contract(ModelSQL, ModelView):
    """Contract Agreement"""
    _name = 'contract.contract'
    _description = __doc__

    name = fields.Char('Name', required=True, translate=True)
    party = fields.many2one('party.party', 'Party', required=True, 
                            states=STATES)
    product = fields.many2one('product.product', 'Product', required=True,
                              states=STATES)

    active = fields.Boolean('Active', select=1)
    interval = fields.Selection([
        ('day','Day'),
        ('week','Week'),
        ('month','Month'),
        ('year','Year'),
    ])
    interval_quant = fields.Property(fields.Numeric('Interval count',
                                                    digits=(16,2)))
    next_invoice_date = fields.Date('Next Invoice')
    start_date = fields.Date('Since')
    stop_date = fields.Date('Until')


Contract()


