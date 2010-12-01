#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.                                                                                                                
from trytond.model import ModelView, ModelSQL, ModelSingleton, fields
  
import logging
log = logging.getLogger(__name__)

class Configuration(ModelSingleton, ModelSQL, ModelView):
    'Contract Configuration' 
    _name = 'contract.configuration'
    _description = __doc__

    description = fields.Char('Contract Description', 
                                              translate=True, 
                                              help="Description used on created Invoices")

    def default_description(self):
        return 'Contract Invoice'

Configuration()
