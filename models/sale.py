from odoo import models, fields, api
from odoo import netsvc
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError

class PreventivaSale(models.Model):
   
    _inherit = 'sale.order'

    os_id = fields.Many2one(
        string="Ordem de Serviço:", comodel_name='dgt_os.os',
        ondelete='restrict',
    )
    