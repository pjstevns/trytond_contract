
from __future__ import with_statement
from trytond.model import ModelView, ModelSQL, fields

import logging

log = logging.getLogger(__name__)

class Party(ModelSQL, ModelView):
    """Party"""
    _name = 'party.party'
    _description = __doc__

    contracts = fields.One2Many('contract.contract', 'party', 'Contracts',
                               readonly=True)
    discount = fields.Numeric('Discount (%)',
                              digits=(4,2),
                             help="""Default Discount percentage on the list_price
                              for this party""")

Party()


