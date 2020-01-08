
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date
from datetime import time
from datetime import datetime
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)

class PreventivaContratos(models.Model):
    _name = 'dgt_preventiva.contratos'
    _description = u'Contrato de preventiva'

    _order = 'name ASC'

    name = fields.Char(
        string=u'Name',
        required=True,
        default=lambda self: _('New'),
        copy=False
    )

    client = fields.Many2one(
        string=u'Cliente',
        comodel_name='res.partner',
        ondelete='set null',
    )

    equipment = fields.Many2one(
        string=u'Equipamento',
        comodel_name='dgt_os.equipment',
        ondelete='cascade',
    )
    tecnico = fields.Many2one(
        string=u'Técnico',
        comodel_name='hr.employee',
        ondelete='set null',
    )

    data_inicio = fields.Datetime(
        string=u'Data Programada',

        default=fields.date.today(),
    )

    data_fim = fields.Datetime(
        string=u'Data Programada fim',
        default=fields.date.today() + timedelta(days=365),
    )
    tempo_chamado = fields.Integer(
        string=u'Tempo Chamado em Horas',
    )

   
    pecas_inclusas = fields.Selection(
        string=u'Peças Inclusas',
        selection=[('todas', 'Todas'), ('lista', 'Lista'),]
    )

    pecas = fields.One2many(
		'dgt_preventiva.contratos.pecas.lines', 'contrato', 'Pecas Inclusas',
        copy=True)

    # <field name="upload_file" filename="file_name"/>
    # <field name="file_name" invisible="1"/>
    #     
    contrato_upload_file = fields.Binary(string="Envia arquivo do contrato")
    contrato_file_name = fields.Char(string="Nome do aqrquivo")    
    


class PreventivaContratosPecasLine(models.Model):
        _name = 'dgt_preventiva.contratos.pecas.lines'
        _description = u'Contrato preventiva Peças Planejadas Line'
        _order = 'contrato, sequence, id'
        
        name = fields.Char('Descrição', size=64)

        contrato = fields.Many2one(
            'dgt_preventiva.contratos', 'Contrato',
            index=True, ondelete='cascade')
        
        product_id = fields.Many2one('product.product', u'Peças', required=True)
        product_uom_qty = fields.Float(
            'Qtd', default=1.0,
            digits=dp.get_precision('Product Unit of Measure'), required=True)
        product_uom = fields.Many2one(
            'product.uom', 'Unidade de medida',
            required=True) 
        sequence = fields.Integer(string='Sequence', default=10)
    

        

    

    
