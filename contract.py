
from __future__ import with_statement
from decimal import Decimal
from trytond.model import ModelView, ModelSQL, fields
from trytond.wizard import Wizard
from trytond.report import Report
from trytond.tools import reduce_ids
from trytond.pyson import Equal, Eval, Not, PYSONEncoder, Date, Bool
from trytond.transaction import Transaction


STATES = {
    'readonly':  Bool(Eval('active')),
}

class Contract(ModelSQL, ModelView):
    """Contract Agreement"""
    _name = 'contract.contract'
    _description = __doc__

    name = fields.Char('Name', required=True, translate=True)
    party = fields.Many2One('party.party', 'Party', required=True, 
                            states=STATES)
    product = fields.Many2One('product.product', 'Product', required=True,
                              states=STATES)

    active = fields.Boolean('Active', select=1)
    interval = fields.Selection([
        ('day','Day'),
        ('week','Week'),
        ('month','Month'),
        ('year','Year'),
    ], 'Interval', required=True, states=STATES)
    interval_quant = fields.Property(fields.Numeric('Interval count',
                                                    digits=(16,2)))
    next_invoice_date = fields.Date('Next Invoice')
    start_date = fields.Date('Since')
    stop_date = fields.Date('Until')


Contract()


