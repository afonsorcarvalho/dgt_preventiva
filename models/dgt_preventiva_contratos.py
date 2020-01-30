
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp
from datetime import date
from datetime import time
from datetime import datetime
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


#TODO 
# 1 faltando colocar o contato do contrato, para qual vai os emails de andamento do serviço de cada equipamento
# 2 faltando criar a sequencia dos contratos para name
# 3 faltando bloquear o usuário para não colocar um equipamento com contrato vigente
# 4 faltando não deixar usuário colocar dois equipamentos igual

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
    STATE_SELECTION = [
        ('draft', 'Criado'),
        ('vigente', 'Vigente'),
		('cancel', 'Cancelado'),
		('done', 'Concluído'),
	]
    state = fields.Selection(
        string=u'Status',
        selection=STATE_SELECTION
    )
    

    client = fields.Many2one(
        string=u'Cliente',
        comodel_name='res.partner',
        ondelete='set null',
    )
    equipment = fields.One2many(
        string=u'Equipamento',
        comodel_name='dgt_preventiva.contratos.equip.lines',
        
        inverse_name='contrato',
        ondelete='cascade',
    )
    tecnico = fields.Many2one(
        string=u'Técnico',
        comodel_name='hr.employee',
        ondelete='set null',
    )

    data_inicio = fields.Date(
        string=u'Data Início',

        default=fields.date.today(),
    )

    data_fim = fields.Date(
        string=u'Data Fim',
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
    
    cronograma_gerado = fields.Boolean(string="Cronograma gerado", )

    cronograma = fields.Many2one(
        string=u'Cronograma Preventiva',
        comodel_name='dgt_preventiva.cronograma',
        ondelete='set null',
    )
    analytic_account_id = fields.Many2one(
        string='Analytic Account',
        comodel_name='account.analytic.account',
        ondelete='set null',
    )
    
    fiscal_position_id = fields.Many2one(
        string="Fiscal Position",
        comodel_name="account.fiscal.position",
       
        
        ondelete="set null",
        help="Posição fiscal que ficara no faturamento das peças",
    )
    service_product_id = fields.Many2one(
        string="Serviço",
        comodel_name="product.product",
        ondelete="set null",
        help="Serviço que será usado na cotação para mão de obra do serviço",
    )
    
    
    

    # <field name="upload_file" filename="file_name"/>
    # <field name="file_name" invisible="1"/>
    #     
    contrato_upload_file = fields.Binary(string="Envia arquivo do contrato")
    contrato_file_name = fields.Char(string="Nome do aqrquivo")    
    
    @api.model
    def create(self, vals):
        """Salva ou atualiza os dados no banco de dados"""
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('dgt_preventiva.contratos') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('dgt_preventiva.contratos') or _('New')
            result = super(PreventivaContratos, self).create(vals)
        return result
    
   
    def get_ativo(self):
        _logger.debug("Entrando get_ativo()")
        _logger.debug("Data do final do contrato: %s", self.data_fim)
        _logger.debug("Data de hoje: %s", fields.date.today())
        if self.data_fim >= fields.date.today():
            _logger.debug("Contrato %s esta ativo",self.name)
            return True
        else:
            _logger.debug("Contrato %s está vencido",self.name)
            return False



class PreventivaContratosEquipmentLine(models.Model):
        _name = 'dgt_preventiva.contratos.equip.lines'
        _description = u'Contrato preventiva Equipamentos Line'
        _order = 'contrato, sequence, id'
        
        name = fields.Char('Descrição', size=64)

        contrato = fields.Many2one(
            'dgt_preventiva.contratos', 'Contrato',
            index=True, ondelete='cascade')
        
        equipment_id = fields.Many2one('dgt_os.equipment', u'Equipamentos', required=True)
        sequence = fields.Integer(string='Sequence', default=10)
        
        @api.onchange("equipment_id" )
        def _onchange_equipment(self):
            vals = {}
            if self.equipment_id:
                self.name = str(self.equipment_id.name) + " NS: " + str(self.equipment_id.serial_number)
                if self.equipment_id.tag:
                    self.name = self.name + " Tag: " + str(self.equipment_id.tag)
                if self.equipment_id.patrimony:
                    self.name = self.name + " Patrimonio: " + str(self.equipment_id.patrimony)
            # Remove warning if necessary
            
            return vals 
        

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
            'Qtd', default=0.0,
            digits=dp.get_precision('Product Unit of Measure'), required=True, 
            help='Se valor zero, quantidade sem limites para o contrato'
            )
        product_uom_qty_used =  fields.Float(
            'Qtd', default=0.0,
            digits=dp.get_precision('Product Unit of Measure'), required=True, 
            help='Quantidade usadas no contrato'
            )
       
        sequence = fields.Integer(string='Sequence', default=10)

        @api.onchange("product_id" )
        def _onchange_product_id(self):
            
            vals = {}
            if self.product_id:
                self.name = self.product_id.name 
                
            
            
            return vals    
    
    

        

    

    
