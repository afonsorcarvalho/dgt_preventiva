from odoo import models, fields, api, _
from odoo import netsvc
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from datetime import date
from datetime import time
from datetime import datetime
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)

class DgtOsInherit(models.Model):
    #_name = 'dgt_os.equipment.category.instruction.inherit'
    _inherit = 'dgt_os.os'

    	
   
    maintenance_grupo_instrucao = fields.Many2many(
		'dgt_os.instruction.grupo',string='Grupo de Instruções'
		)

    defeitos_true = fields.Boolean(
        string=u'Defeitos',
    )
    contrato = fields.Many2one(
		'dgt_preventiva.contratos',string='Contrato'
	)

    pendencias_true = fields.Boolean(
        string=u'Pendências',
    )
    gerado_cotacao = fields.Boolean(
        string=u'Cotação gerada?',
    )
    
    autorizada_execucao = fields.Boolean(
        string=u'Execução autorizada',
    )
    
    precisa_autorizacao = fields.Boolean(
        string=u'Precisa autorização',
    )
    
    # check_list = fields.One2many(
	# 	'dgt_os.os.verify.list', 'os_id', u'Check List',
	# 	copy=False, readonly=False,track_visibility='onchange')

    # assinatura digital
    name_digital_signature_client = fields.Char(
        string=u'Nome do Cliente Assinatura',
    )
    doc_digital_signature_client = fields.Char(
        string=u'Nome do Cliente Assinatura',
    )
    digital_signature_client = fields.Binary(string='Assinatura Cliente')

    @api.model
    def create(self, values):
        result = super().create(values)
        _logger.debug("Equipamento selecionado: %s",self.equipment_id)
        result.contrato = result.equipment_id.get_contrato()
        _logger.debug("Contrato: %s",self.contrato.name)
        _logger.debug(self.contrato)
        result.add_service()
        return result
    
    @api.onchange('date_scheduled')
    def onchange_scheduled_date(self):
        preventiva = self.env['dgt_preventiva.dgt_preventiva'].search([('os_id', '=', self.name)])
        if preventiva.id:
            msg = "Não pode alterar data programada de OS gerada por preventiva. Altere na preventiva que a gerou." 
            raise UserError(
                _(msg))
        self.date_execution = self.date_scheduled
        
    #TODO Colocar o add_service também na dgt_os.os para fazer somente um override aqui
    def add_service(self):
        _logger.debug("adicionando serviço atraves do contrato:")
        _logger.debug(self.contrato)
        
        _logger.debug("procurando serviço já adicionados na OS")
        line = self.env['dgt_os.os.servicos.line'].search([('os_id', '=',self.id )], offset=0, limit=None, order=None, count=False)
        servicos_line = []
        for serv_line in line: 
            servicos_line.append(serv_line.product_id)
            
        _logger.debug("Serviços achados para OS")
        _logger.debug(servicos_line)
        
        
        #TODO Pegar do tipo da OS que deverá também ser mudada de selection para classe contendo o serviço padrão
        #Procurando o id do serviço padrão
       
        _logger.debug("Serviços Padrão")
        service_default = self.env['product.product'].search([('name','ilike','Manutenção Geral')], limit=1)
        _logger.debug(service_default)
        
        _logger.debug("Serviços Padrão Corretiva")
        service_corrective_default = self.env['product.product'].search([('name','ilike','Manutenção corretiva')], limit=1)
        _logger.debug(service_corrective_default)
        
        _logger.debug("Serviços Padrão Preventiva")
        service_preventive_default = self.env['product.product'].search([('name','ilike','Manutenção Preventiva')], limit=1)
        _logger.debug(service_preventive_default)
        #produto padrao para serviços em geral
        
        if not service_default.id:
            raise UserError(_("Serviço padrão não configurado. Favor configurá-lo. Adicione o serviço 'Manutenção Geral'"))
        product_id = service_default
        
             
        if self.contrato.id:
            _logger.debug("Existe contrato para esse equipamento:")
            _logger.debug("Colocando serviço padrão para contrato:")
            if self.contrato.service_product_id.id:
                #verificando se tem esse serviço adicionado
                if self.contrato.service_product_id in servicos_line:
                    _logger.debug("Já existe serviço adicionado: %s", self.contrato.service_product_id.name)
                else:
                    _logger.debug("Serviço adicionado: %s", self.contrato.service_product_id.name)
                    product_id = self.contrato.service_product_id
               
        _logger.debug("Verificando tempo para adicionar no serviço")
        if self.time_execution > 0:
            _logger.debug("Colocado tempo de execução no serviço: %s",self.time_execution )
            product_uom_qty = self.time_execution
            
        else:
            _logger.debug("Colocado tempo estimado no serviço: %s", self.maintenance_duration)
            product_uom_qty = self.maintenance_duration
        _logger.debug("Create servicos line:")
        
       # res = self.env['dgt_os.os.servicos.line'].create({
       #     'os_id' : self.id,
       #     'name': self.description,
       #     'product_id' : product_id.id,
       #     'product_uom': product_id.uom_id.id,
       #     'product_uom_qty' : product_uom_qty
       # }) 
       #TODO verificar se está pegando mesmo a descrição
        if self.description:
            name = self.description
        else:
            name = product_id.display_name
        self.servicos = [(0,0,{
            'os_id' : self.id,
            'automatic': True,
            'name': name,
            'product_id' : product_id.id,
            'product_uom': product_id.uom_id.id,
            'product_uom_qty' : product_uom_qty
        })]
        _logger.debug( self.servicos)
        return self.servicos
    
    def default_analytic_account(self):
        #se tiver contrato
        self.analytic_account_id = 0
        _logger.debug("configurando conta analitica") 
        if self.contrato.id:
            _logger.debug("Equipamento em contrato") 
            if self.contrato.analytic_account_id.id:
                _logger.debug("Conta analitica do contrato: %s",self.contrato.analytic_account_id.name) 
                self.analytic_account_id = self.contrato.analytic_account_id.id
            else:
                _logger.debug("Não configurado conta analitica no contrato")
        else:
             _logger.debug("Equipamento fora de contrato, nenhuma conta analítica configurada")
                 
    @api.onchange('equipment_id')
    def _change_equipment(self):
        if self.equipment_id.id:
            _logger.debug("procurando contrato:")
            _logger.debug(self.equipment_id.id)
        
        
            _logger.debug("Equipamento selecionado: %s",self.equipment_id)
            self.contrato = self.equipment_id.get_contrato()
            _logger.debug("Contrato: %s",self.contrato.name)
            _logger.debug(self.contrato)
                                 
            self.add_service()
            self.default_analytic_account()
            
    def create_checklist(self):
        """Cria a lista de verificacao caso a OS seja preventiva"""
        if self.maintenance_type == 'preventive':
            ar1 = [('category_id', '=', self.equipment_id.category_id.name)]
           
            ar_grupo = []
            for grupo in self.maintenance_grupo_instrucao:
                ar_grupo = ar_grupo + [grupo.name]
            ar1 = ar1 + [('grupo_id', 'in', ar_grupo)]
            instructions = self.env['dgt_os.equipment.category.instruction'].search(ar1)
            os_check_list = self.env['dgt_os.os.verify.list']
            
            for instruction in instructions:
                check_list = os_check_list.create({
                    'dgt_os': self.id,
                    'instruction': str(instruction.name),
                    'unidade': instruction.grandeza.unidade,
                    'tem_medicao': instruction.tem_medicao,
                    'tipo_de_campo': str(instruction.tipo_de_campo),
                    'troca_peca': instruction.troca_peca,
                    'peca': instruction.peca.id,
                    'peca_qtd': instruction.peca_qtd
                })

                if check_list.troca_peca:
                    peca = self.env['dgt_os.os.pecas.line']                   
                    peca.create({
                        'os_id' : self.id,
                        'product_id': instruction.peca.id,
                        'name': instruction.peca.display_name,
                        'product_uom': instruction.peca.uom_id.id,
                        'product_uom_qty': instruction.peca_qtd
                    })
                 

    def update_preventiva(self):
    #TODO 
    # procura menor data e menor hora e coloca em data inicio da preventiva
    # depois procura maior data e maior hora e coloca em data de fim da preventiva
            
        preventiva = self.env['dgt_preventiva.dgt_preventiva'].search([('os_id', '=', self.id)])
       
        if preventiva.id:
            res = preventiva.write({
                'data_execucao': self.date_start,
                'data_execucao_fim': self.date_execution ,
                'preventiva_executada': True,
                'state':'done'
            })

    # ----------------------------------------
    # Actions Methods
    # ----------------------------------------
    
    #override
    @api.multi
    def action_repair_end(self):
        #TODO
        # atualizar status do equipamento
        # atualizar status da solicitacao de serviço
        #procura preventiva relacionada e coloca ela como executada e hora de início e fim da execução
        
        
        result = super(DgtOsInherit, self).action_repair_end()
        if result:
            self.update_preventiva()
            #TODO
            #self.update_status_equipment()   
            #self.update_status_solicicao()   
                                
        return result
    
    
    #retirada por enquanto não está sendo utilizada 
    def action_requisitar_pecas(self):
        _logger.info("requisitando peças:")
        
    #TODO Fazer em configurações uma posição fiscal padrão para que possa ser carregada nesta função
    def get_fiscal_position_default(self):
        name = self.contrato.fiscal_position_id.name
        return self.env['account.fiscal.position'].name_search(name=name, args=None, operator='ilike', limit=1)
    
     #TODO Fazer em configurações uma conta analitica padrão para que possa ser carregada nesta função
    def get_analytic_account_default(self):
        name = self.contrato.analytic_account_id.name
        _logget.debug("nome da conta analitica",name)
        
        return self.env['account.analytic.account'].name_search(name=name, args=None, operator='ilike', limit=1)   
    
    
    


class OsVerifyLisInherit(models.Model):
    _inherit = 'dgt_os.os.verify.list'

    tem_medicao = fields.Boolean("tem medição?")
    medicao = fields.Float("Medições")
    unidade = fields.Char('Unidades')
    tipo_de_campo = fields.Char("Tipo de campo")
    observations = fields.Char()
    troca_peca = fields.Boolean(string="Substituição de Peça?",required=False)    
    peca = fields.Many2one('product.product', u'Peça', required=False)
    peca_qtd = fields.Float('Qtd', default=0.0,	digits=dp.get_precision('Product Unit of Measure'))
