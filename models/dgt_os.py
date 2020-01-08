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

    	
    STATE_SELECTION = [
		('draft', 'Criada'),
		('cancel', 'Cancelada'),
		('under_repair', 'Em execução'),
		('done', 'Concluída'),
	]

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
   
        
        
      

    # assinatura digital
    name_digital_signature_client = fields.Char(
        string=u'Nome do Cliente Assinatura',
    )
    doc_digital_signature_client = fields.Char(
        string=u'Nome do Cliente Assinatura',
    )
    digital_signature_client = fields.Binary(string='Assinatura Cliente')
    
    @api.onchange('date_scheduled')
    def onchange_scheduled_date(self):
        preventiva = self.env['dgt_preventiva.dgt_preventiva'].search([('os_id', '=', self.name)])
        if preventiva.id:
            msg = "Não pode alterar data programada de OS gerada por preventiva. Altere na preventiva que a gerou." 
            raise UserError(
                _(msg))
        self.date_execution = self.date_scheduled
        
    #TODO Pegar de alguma configuração o serviço do contrato   
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
            raise UserError(_("Serviço padrão não configurado. Favor configurá-lo"))
        product_id = service_default
        
             
        if self.contrato.id:
            _logger.debug("Existe contrato para esse equipamento:")
            _logger.debug("Colocando serviço padrão para contrato:")
            if self.contrato.service_product_id.id:
                #verificando se tem esse serviço adicionado
                if self.contrato.service_product_id in servicos_line:
                    _logger.debug("Já existe serviço adicionado: %s", self.contrato.service_product_id.id)
                else:
                    _logger.debug("Serviço adicionado: %s", self.contrato.service_product_id.id)
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
        self.servicos = [(0,0,{
            'os_id' : self.id,
            'name': self.description,
            'product_id' : product_id.id,
            'product_uom': product_id.uom_id.id,
            'product_uom_qty' : product_uom_qty
        })]
        _logger.debug( self.servicos)
        
    @api.onchange('equipment_id')
    def _change_equipment(self):
        
        _logger.debug("procurando contrato:")
        _logger.debug(self.equipment_id.id)
        
        if self.equipment_id.id:
            _logger.debug("Equipamento selecionado: %s",self.equipment_id)
            equipline = self.env['dgt_preventiva.contratos.equip.lines'].search([('equipment_id','=',self.equipment_id.id)],offset=0, limit=1)
            #Equipamento tem  contrato?
            if len(equipline) > 0:
                #contrato está vigente?
                if equipline.contrato.data_fim >= fields.date.today():
                    self.contrato = equipline.contrato
                    _logger.debug("contrato vigente achado:")
                    _logger.debug(self.contrato)
                    
                    
                else:
                    self.contrato = False
            else:
                self.contrato = False
        self.add_service()
                
    
    
    
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
                 

    # ----------------------------------------
    # Actions Methods
    # ----------------------------------------
    
    #override
    @api.multi
    def action_repair_end(self):
        #TODO
        #procura preventiva relacionada e coloca ela como executada e hora de início e fim da execução
        
        
        result = super(DgtOsInherit, self).action_repair_end()
        if result:
            relatorios = self.relatorios
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
                
                    
        return result
     
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
    
    
    #TODO Colocar também o técnico que irá receber a comissão 
    # colocar tempo de execução no serviço do contrato, mas isso tem que ser feito ao realizar fim da execução ou qd 
    # aciona o botão de gerar o orçamento   
    def action_gera_orcamento(self):
        if self.filtered(lambda dgt_os: dgt_os.gerado_cotacao == True):
            raise UserError(_("Cotação para esse Ordem de serviço já foi gerada"))
        if not len(self.servicos):
            raise UserError(_("Para gerar cotação deve ter pelo menos um serviço adicionado"))
        
        _logger.info("dados do contrato:")
        _logger.info("posicão fiscal:")
        _logger.info(self.contrato.fiscal_position_id)
        _logger.info("Conta Analítica:")
        _logger.info(self.contrato.analytic_account_id)
        _logger.info("gerando cotação:")
        _logger.info(self)
        
        saleorder = self.env['sale.order'].create({
            "origin": self.name,
            "partner_id" : self.cliente_id.id,
            "analytic_account_id":self.contrato.analytic_account_id,
            "fiscal_position_id":self.contrato.fiscal_position_id
            
        })
        _logger.info("sale_order:")
        _logger.info(saleorder)

        if saleorder.id:
            _logger.info("criar linhas da sale.order:")
            _logger.info(saleorder.name)
            
            name_note = "Referente ao equipamento "
            if self.equipment_id.name: name_note = name_note + self.equipment_id.name
            if self.equipment_serial_number: name_note = name_note + " NS " + str(self.equipment_serial_number)
            if self.equipment_model: name_note = name_note + " Modelo: " + str(self.equipment_model)
               
            # Adicionando as peças
            self.env['sale.order.line'].create({
                    'name' : name_note,
                    'display_type' : 'line_note',
                    'order_id': saleorder.id,
                    'product_id': False,
                    'product_uom': False,
                    
                })
            self.env['sale.order.line'].create({
                    'name' : "Peças da " + self.name +":",
                    'display_type' : 'line_section',
                    'order_id': saleorder.id,
                    'product_id': False,
                    'product_uom': False,
                    
                })
            _logger.info("Sessão criada:")
            for peca in self.pecas:
                _logger.info("adicionando linhas de pecas:")
                saleline = self.env['sale.order.line'].create({
                    
                    'order_id': saleorder.id,
                    'product_id': peca.product_id.id,
                    'product_uom_qty': peca.product_uom_qty,
                    'product_uom': peca.product_uom.id,
                    'invoice_lines': peca.invoice_line_id.id,
                })
                _logger.info("linha peca adicionada:")
                _logger.info(saleline)
            
            #adicionando serviços

            self.env['sale.order.line'].create({
                    'name' : "Serviços da " + self.name + ":",
                    'display_type' : 'line_section',
                    'order_id': saleorder.id,
                    'product_id': False,
                    'product_uom': False,
                    
                })
            _logger.info("Sessão criada:")
            #TODO Pegar do contrato o serviço product_id caso tenha configurado no contrato
            for servico in self.servicos:
                _logger.info("adicionando linhas:")
                saleline = self.env['sale.order.line'].create({
                    
                    'order_id': saleorder.id,
                    'product_id': servico.product_id.id,
                    'product_uom_qty': servico.product_uom_qty,
                    'product_uom': servico.product_uom.id,
                    'invoice_lines': servico.invoice_line_id.id,
                })
                _logger.info("linha serviço adicionada:")
                _logger.info(saleline)
            
            self.write({'sale_id': saleorder.id,'gerado_cotacao': True})   
        
        return True


class OsVerifyLisInherit(models.Model):
    _inherit = 'dgt_os.os.verify.list'

    dgt_os = fields.Many2one('dgt_os.os', "OS")
    instruction = fields.Char('Instruções')
    check = fields.Boolean()
    tem_medicao = fields.Boolean(string='Tem medição?')
    medicao = fields.Float("Medições")
    unidade = fields.Char('Unidades')
    tipo_de_campo = fields.Char("Tipo de campo")
    observations = fields.Char()
    troca_peca = fields.Boolean(string="Substituição de Peça?",required=False)    
    peca = fields.Many2one('product.product', u'Peça', required=False)
    peca_qtd = fields.Float('Qtd', default=0.0,	digits=dp.get_precision('Product Unit of Measure'))

    
  
    
  
    
  
    
    