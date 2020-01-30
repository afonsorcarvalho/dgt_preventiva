# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date
from datetime import time
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from calendar import monthrange
from calendar import monthcalendar
from odoo.exceptions import UserError
import pytz
import logging
import calendar

_logger = logging.getLogger(__name__)


class dgt_preventiva(models.Model):
    _name = 'dgt_preventiva.dgt_preventiva'
    
    _description = 'Preventiva'
    _order = 'dias_de_atraso ASC'
    _inherit =['mail.thread', 'mail.activity.mixin', 'portal.mixin','utm.mixin']
   
    
    STATE_SELECTION = [
        ('draft', 'Criada'),
        ('cancel', 'Cancelada'),
        ('atrasada', 'Atrasada'),
        ('programada', 'Ordem Gerada'),
        ('reagendada','Reagendada'),
        ('done', 'Concluída'),
    ]
    state = fields.Selection(STATE_SELECTION, string='Status',
                             copy=False, default='draft',  track_visibility='onchange',
                             help="*  \'Criada\' usado quando a preventiva está somente criada.\n"
                                  "*  \'Cancelada\' usado quando a preventiva foi cancelada pelo usuário.\n"
                                  "*  \'Atrasada\' usado quando a preventiva não foi executada no dia programado.\n"
                                  "*  \'Ordem Gerada\' usado quando já existe OS gerada para execução.\n"
                                  "*  \'Reagenda\' usada quando OS gerada e foi reagendada a execução.\n"
                                  "*  \'Concluída\' a ordem de serviço já foi executada."
                            )
    name = fields.Char()
    equipment = fields.Many2one(
        string=u'Equipamento',
        comodel_name='dgt_os.equipment',
        ondelete='cascade',
    )
    client = fields.Many2one(
        string=u'Cliente',
        comodel_name='res.partner',
        ondelete='set null',
    )
    cronograma = fields.Many2one(
        string=u'Cronograma',
        comodel_name='dgt_preventiva.cronograma',
        ondelete='set null',
    )
    
    tecnico = fields.Many2one(
        string=u'Técnico',
        comodel_name='hr.employee',
        ondelete='set null',
        track_visibility='onchange',
    )
    grupo_id = fields.Many2many(
        'dgt_os.instruction.grupo', string='Grupo de Instruções',track_visibility='onchange',
    )
    
    tempo_estimado = fields.Float(
        string=u'Tempo Estimado', 
        help="Tempo estimado de conclusão da preventiva.",
    )
    
    data_programada = fields.Datetime(
        string=u'Data Programada',

        default=fields.datetime.now(),track_visibility='onchange',
        help="Data e hora programada do início da preventiva.",
    )

    data_programada_fim = fields.Datetime(
        string=u'Data Programada fim',
        default=fields.datetime.now(),track_visibility='onchange',
        help="Data e hora programada do fim da preventiva.",
    )

    data_execucao = fields.Datetime(
        string=u'Início Execução',
        default=fields.datetime.now(),track_visibility='onchange',
        help="Data e hora do início da execuão da preventiva.",
    )

    data_execucao_fim = fields.Datetime(
        string=u'Fim da Execução',
        default=fields.datetime.now(),track_visibility='onchange',
        help="Data e hora do fim da execuão da preventiva.",
    )
    
    dias_de_atraso = fields.Integer(
        string=u'Dias de atraso',
        help="Dias de atraso da prevetiva, valores negativos indicam quantos dias para a data programada de execução.",
    )
    
    gerada_os = fields.Boolean(
        string=u'Gerada Os',track_visibility='onchange',
        help="Indica ordem de serviço gerada.",
    )
    os_id = fields.Many2one(
        string="Ordem de serviço",
        comodel_name="dgt_os.os",
        ondelete="set null",
        help="Ordem de serviço referente a preventiva.",track_visibility='onchange',
    )
    preventiva_executada = fields.Boolean(
        string=u'Preventiva executada?',track_visibility='onchange',
        help="Indica que preventiva foi executada.",
    )
    
    
    @api.onchange('data_programada')
    def _onchange_data_programada(self):
        tempo = timedelta(hours=1)
        tempo_estimado = timedelta(hours=self.tempo_estimado)
        if tempo_estimado.total_seconds() > 3600:
            tempo = tempo_estimado
        self.data_programada_fim = self.data_programada + tempo
    
    @api.onchange('data_programada_fim')
    def _onchange_data_programada_fim(self):
        tempo = self.data_programada_fim - self.data_programada
        if tempo.total_seconds() < 3600:
            tempo = timedelta(hours=1)
            self.data_programada_fim = self.data_programada + tempo
        self.tempo_estimado = tempo.total_seconds()/3600
    
    @api.onchange('tempo_estimado')
    def _onchange_tempo_estimado(self):
        if self.tempo_estimado < 1:
            self.tempo_estimado = 1
        
        tempo_estimado = timedelta(hours=self.tempo_estimado)
        self.data_programada_fim = self.data_programada + tempo_estimado
        
         
    
    @api.onchange('gerada_os')
    def _onchange_gerada_os(self):
        self.state = 'programada'
        
    @api.onchange('preventiva_executada')
    def _onchange_preventiva_executada(self):
        self.state = 'done'
    
    @api.model
    def set_executada(self):
        self.state = 'done'
        self.preventiva_executada = True
        
    @api.multi
    def write(self, vals):
        self.ensure_one()
        
        
        if self.gerada_os == True and self.preventiva_executada == False:
            if ('data_programada' in vals):
                self.os_id.date_scheduled = vals['data_programada']
                self.os_id.date_start = vals['data_programada']
            if ('data_programada_fim' in vals):
                self.os_id.date_execution = vals['data_programada_fim']
                #todo não está funcionando colocar o tempo estimado na OS
            if ('tempo_estimado' in vals):
                self.os_id.maintenance_duration = vals['tempo_estimado']
            self.dias_de_atraso = self.calc_dias_de_atraso()
            
        if self.preventiva_executada == True:
            raise UserError(
                _("Não pode alterar preventiva que já tem OS executada"))    
        result = super(dgt_preventiva, self).write(vals)
        return result
    
    
    @api.multi
    def action_gera_os(self):
       
        for record in self:
            os = record.gera_os()
            if os.id:
                msg = "A Ordem de serviço {} foi gerada com sucesso!!!.".format(os.name)
                message_id = self.env['dgt_preventiva.message.wizard'].create({'message': _(msg)})
                return {
                    'name': _('Sucesso!!'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'dgt_preventiva.message.wizard',
                    # pass the id
                    'res_id': message_id.id,
                    'target': 'new'
                }
               
        
        return True
    
    
    @api.multi
    def gera_os(self):
        r = self
        _logger.info("Grupo...")
        _logger.info(r.grupo_id)
        
        #pegando grupo de instruções
        grps_inst = [] 
        for g in r.grupo_id:
            _logger.info(g.id)
            grps_inst.append(g.id)
        
        os = self.env['dgt_os.os'].create({
                'origin':r.name, 
                'maintenance_type':'preventive',
                'cliente_id': r.client.id,
                'contact_os': 'Automático',
                'description': r.name,
                'equipment_id': r.equipment.id,
                'date_scheduled':  r.data_programada,
                'date_execution':  r.data_programada,
                'maintenance_grupo_instrucao': [(6, 0, grps_inst)],
                'state':'execution_ready',
            })
        r.write({'gerada_os': True,'state':'programada', 'os_id': os.id})
        return os
    
    @api.one
    def set_preventiva_atrasada(self):
        if not self.preventiva_executada:
            self.state = 'atrasada'
    
    @api.multi
    def envia_email_aviso_preventiva(self,tipo='aviso') :
        _logger.info("Email de Preventivas.. ")
        _logger.info(self)
        for preventiva in self:
            if tipo == 'aviso':
                _logger.info("Email de aviso de Preventivas.. ")
                template_client_id = self.env.ref('dgt_preventiva.mail_aviso_preventiva_cliente')
                template_tecnico_id = self.env.ref('dgt_preventiva.mail_aviso_preventiva_tecnico')
             
            if tipo == 'atraso':
                _logger.info("Email de aviso de atraso de Preventivas.. ")
                template_client_id = self.env.ref('dgt_preventiva.mail_aviso_atraso_preventiva_cliente')
                template_tecnico_id = self.env.ref('dgt_preventiva.mail_aviso_atraso_preventiva_tecnico')
                
            _logger.info("Eviando email para tecnico: ")
            preventiva.message_post_with_template( template_tecnico_id.id)
            _logger.info("Eviando email para cliente: ")
            preventiva.message_post_with_template( template_client_id.id)
            
           
    @api.multi
    def aviso_preventiva(self):
        hoje = fields.Date.today()
        dias_aviso_preventiva = 2
       # dia_procura_inicio = hoje + timedelta(days=dias_aviso_preventiva)
       # dia_procura_fim
        res = self.env['dgt_preventiva.dgt_preventiva'].search(
            [('gerada_os', '=', True),
             ('data_programada', '>=', hoje + timedelta(days=0,hours=0)),('data_programada', '<=', hoje + timedelta(days=dias_aviso_preventiva,hours=0))])
        _logger.info("Aviso de Preventivas.. ")
        _logger.info(res)
        
        res.envia_email_aviso_preventiva()
        
       
      #  for r in res:
      #      dias_de_atraso = r.calc_dias_de_atraso()
      #      _logger.info(dias_de_atraso)
      #      r.dias_de_atraso = dias_de_atraso[0]
      #      if dias_de_atraso[0] > 0:
    #         r.set_preventiva_atrasada()
    
    @api.multi
    def aviso_preventiva_atrasada(self):
        _logger.info("entrou no aviso de preventiva atrasada...")
        hoje = fields.Datetime.now()
        _logger.info("procurando preventiva atrasada...")
       # dia_procura_inicio = hoje + timedelta(days=dias_aviso_preventiva)
       # dia_procura_fim
        res = self.env['dgt_preventiva.dgt_preventiva'].search(
            [('gerada_os', '=', True),('preventiva_executada','=',False),
             ('data_programada', '<', hoje)])
        
        _logger.info("Preventivas atrasadas...")
        _logger.info(res)
        res.envia_email_aviso_preventiva('atraso')
        
    @api.one
    def calc_dias_de_atraso(self):
        p=self
        umdia = (3600*24)  
        # res = []
        #for p in self:
        
        dias =  datetime.now() - p.data_programada
        res = dias.total_seconds()
        res = res/umdia
        return res 
    
    # *************************
    #  CRON  gera OS e verifica atrasos de preventiva
    #
    # *************************
    @api.multi
    def cron_agenda_preventiva(self):
        dias_antecipa_gera_os = 30
        dias_avisa_prev = 2
        _logger.info("Entrou no agendamento da preventiva...")
        hoje = fields.Date.today()
        
        res = self.env['dgt_preventiva.dgt_preventiva'].search(
            [('gerada_os', '=', False), ('data_programada', '>=', hoje),('data_programada', '<=', hoje + timedelta(days=dias_antecipa_gera_os))])
        _logger.info(res)
        
        for r in res:
            os = r.gera_os()
        _logger.info("chamando aviso de preventiva...")
        #aviso prévio de vencimento de preventivas
        self.aviso_preventiva()
                
        _logger.info("calculando dias de atraso de preventiva...")
        #atualizando dias de atraso/que faltam das preventivas
        #valores negativos dias que faltam para preventiva
        #valores positivos dias de atraso
        res = self.env['dgt_preventiva.dgt_preventiva'].search([('preventiva_executada', '=', False)])
        for r in res:
            dias_de_atraso = r.calc_dias_de_atraso()
            #_logger.info(dias_de_atraso)
            r.dias_de_atraso = dias_de_atraso[0]
            if dias_de_atraso[0] > 0:
                r.set_preventiva_atrasada()
        
        _logger.info("chamando aviso de atraso de preventiva...")        
        #aviso de manutenção preventiva atrasada
        self.aviso_preventiva_atrasada()


class dgtPreventivaMessageWizard(models.TransientModel):
    _name = 'dgt_preventiva.message.wizard'
    _description = u'Model para menus Popups de confirmação de ações'
    

    message = fields.Text('Message', required=True)

    @api.multi
    def action_ok(self):
        """ close wizard"""
        return {'type': 'ir.actions.act_window_close'}       


class CronogramaPreventiva(models.Model):
    _name = 'dgt_preventiva.cronograma'
    _description = u'Cronogramas de preventivas'

    _rec_name = 'name'
    _order = 'name ASC'
    
    STATE_SELECTION = [
		('draft', 'nova'),
		('cancel', 'Cancelada'),
		('done', 'Concluída'),
	]
    Diasemana = ['S','T','Q',
                'Q','S','S','D']
    Meses=['Janeiro','Fevereiro','Março','Abril','Maio','Junho',
           'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
    
    name = fields.Char(
        string=u'Name',
        required=True,
        default=lambda self: _('New'),
        copy=False
    )
    state = fields.Selection(
        string="Status",
        selection=STATE_SELECTION,
    )
    cal = calendar.Calendar()
    

#
# funcão de criação do cronograma
#
    @api.model
    def create(self, vals):
        """Salva ou atualiza os dados no banco de dados"""
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(
                    force_company=vals['company_id']).next_by_code('dgt_preventiva.cronograma') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'dgt_preventiva.cronograma') or _('New')

        result = super(CronogramaPreventiva, self).create(vals)
        return result
    
        
    description = fields.Text(
        required=True, help="Descreva o cronograma com nome de cliente se faz parte de algum contrato etc...")
    equipments = fields.Many2many(
        'dgt_os.equipment', string='Equipamentos', required=True, help="Insira os equipamentos que farão parte deste cronograma"
    )
    date_start = fields.Date(
        string="Data de início do cronograma", help="Data de início do cronograma")
    date_stop = fields.Date(
        string="Data de fim do cronograma", help="Data de fim do cronograma")
    tecnicos = fields.Many2many(
		'hr.employee',	
		string = 'Técnicos')
    
    #TODO
    # Pegar o ano do cronograma 
    #usado no report da impressao
    def get_preventivas(self, ano=2020,mes=0):
               
        
        if mes:
            first_day =datetime(ano,mes,1,0,0,0,0).strftime("%Y-%m-%d %I:%M:%S")
            if mes == 12:
                mes = 1
                ano = ano+1
            last_day = datetime(ano,mes,monthrange(ano,mes)[1],23,59,59,0).strftime("%Y-%m-%d %I:%M:%S")
            res=self.env['dgt_preventiva.dgt_preventiva'].search([('cronograma', '=', self.id),('data_programada', '>=', first_day),('data_programada', '<', last_day)], offset=0, limit=None, order='data_programada ASC', count=False)
            self.preventiva_data = res
        else:
            res=self.env['dgt_preventiva.dgt_preventiva'].search([('cronograma', '=', self.id)], offset=0, limit=None, order='data_programada ASC', count=False)
            self.preventiva_data = res
        return res
   
    #usado no report da impressao
    def get_meses_que_tem_preventivas(self):
        res=self.env['dgt_preventiva.dgt_preventiva'].search([('cronograma', '=', self.id)], offset=0, limit=None, order='data_programada ASC', count=False)
        meses_com_preventiva = []
        for rec in res:
            rec_mes = rec.data_programada.month
            meses_com_preventiva = list(set(meses_com_preventiva) | set([rec_mes]))
        return meses_com_preventiva
   
    #usado no report da impressao
    def get_calendar(self):
        cal = calendar.Calendar()
        res = cal.yeardayscalendar(2020,1)
        return res
    #usado no report da impressao
    def get_calendar_mes(self,ano,mes):
        cal = calendar.Calendar()
        res = cal.yeardayscalendar(ano,mes)
        return res
    #usado no report da impressao
    def get_preventivas_date(self,data_programada):
        res = self.env['dgt_preventiva.dgt_preventiva'].search([('cronograma', '=', self.id),('data_programada','=',data_programada)], offset=0, limit=None, order=None, count=False)
        return res
    #usado no report da impressao
    def get_number_weeks(self,ano, mes):
        
        
        res = len(monthcalendar(ano,mes))
        return res
#
# funcão de gera cronograma de preventivas
#  para cada equipamento cadastrado no cronograma
#

    @api.multi
    def action_gera_cronograma(self):
        user_tz = self.env.user.tz
        local = pytz.timezone(user_tz)
        _logger.info(local)
        today = date.today()
        hora_ini_dia = time(11,0,0, tzinfo=timezone.utc) # hora de início do dia
        hora_fim_dia = time(21,0,0, tzinfo=timezone.utc) # hora de fim do dia
        today_time = datetime.combine(today,hora_ini_dia) #começa sempre 8 da manhã brazil
        if self.date_start > self.date_stop:
            raise UserError(
                _("Data de início maior que data de fim da geração do cronograma. Não é possivel gerar cronograma"))
        if self.date_stop < today:
            raise UserError(
                _("Data de fim do cronograma menor que a data atual. Não é possivel gerar cronograma"))
        for equipment in self.equipments:
            _logger.info("equipment.category_id.name:")
            _logger.info(equipment.category_id.id)
            instructions = self.env['dgt_os.equipment.category.instruction'].search([('category_id','=',equipment.category_id.id)])
            _logger.info("instruções:")
            _logger.info(instructions)
            for instruction in instructions:
                _logger.info("instrução:")
                _logger.info(instruction)
                #grupo = [instruction.grupo_id]
                #_logger.info("grupo:")
                #_logger.info(grupo)
                grupo_instructions = []
                if instruction.grupo_id.instruction_type == 'preventiva':
                    if instruction.grupo_id not in grupo_instructions:
                        _logger.info("novo grupo:")
                        grupo_instructions = grupo_instructions + [instruction.grupo_id]
            _logger.info("grupo de instruções:")
            _logger.info(grupo_instructions)
            for grupo_instruction in grupo_instructions:
                dias = grupo_instruction.periodicidade
                if self.date_start >= today:
                    date_current = datetime.combine(self.date_start,hora_ini_dia)
                else:
                    date_current = today_time
                while (date_current.date() < self.date_stop):
                    data_programada = date_current + timedelta(days=dias)
                    # Adiciona a preventiva no cronograma
                    _logger.info("NOVA data preventiva:")
                    _logger.info(data_programada)
                    date_current = data_programada
                    _logger.info("data agora:")
                    _logger.info(date_current)

                    # ajustando a data programada para dias que não sejam finais de semana
                    dia_sem = datetime.weekday(data_programada)
                    _logger.info("dia da semana:")
                    _logger.info(dia_sem)
                    if dia_sem == 5:
                        _logger.info("é sabado:")          
                        data_programada=data_programada + timedelta(days=2)
                        _logger.info("somando dois dias:") 
                        _logger.info(data_programada)
                    if dia_sem == 6:
                        _logger.info("é domingo:") 
                        data_programada=data_programada + timedelta(days=1)
                        _logger.info("somando um dia:") 
                        _logger.info(data_programada)
                    
                    # verificando se existe alguma preventiva já programada para esse equipamento
                   # str_data_prog = data_programada.strftime("%d/%m/%Y")
                    _logger.info("data_procura")
                    _logger.info(data_programada)
                    da = datetime(data_programada.year, data_programada.month, data_programada.day,0,0,0,0,tzinfo=local).strftime("%Y-%m-%d %H:%M:%S")
                    dp = datetime(data_programada.year, data_programada.month, data_programada.day,23,59,59,0,tzinfo=local).strftime("%Y-%m-%d %H:%M:%S")

                    prev = self.env['dgt_preventiva.dgt_preventiva'].search([
                        ['data_programada','>=',da],['data_programada','<=',dp],
                        ['equipment','=',equipment.id],
                        ['cronograma','=',self.id]])
                    _logger.info("Preventiva igual, mano:")
                    _logger.info(prev)
                    if prev:
                        _logger.info("jA TEM PREVENTIVA")
                        _logger.info(prev)
                        prev.write({
                            "name": str(self.name) + "/" + str(equipment.name),
                            "client": equipment.client_id.id,
                            "equipment": equipment.id,
                            "grupo_id": [(4,grupo_instruction.id)],
                            "data_programada": data_programada.replace(hour=hora_ini_dia.hour,minute=hora_ini_dia.minute, tzinfo=timezone.utc),
                            "data_programada_fim": data_programada.replace(hour=15,minute=0, tzinfo=timezone.utc),
                            "cronograma":self.id,
                            "tecnico": self.tecnicos[0].id,
                        })
                    else:   
                        self.env['dgt_preventiva.dgt_preventiva'].create({
                            "name": str(self.name) + "/" + str(equipment.name),
                            "client": equipment.client_id.id,
                            "equipment": equipment.id,
                            "grupo_id": [(4,grupo_instruction.id)],
                            "data_programada": data_programada.replace(hour=hora_ini_dia.hour,minute=hora_ini_dia.minute, tzinfo=timezone.utc),
                            "data_programada_fim": data_programada.replace(hour=15,minute=0, tzinfo=timezone.utc),
                            "cronograma":self.id,
                            "tecnico": self.tecnicos[0].id,

                        })
            # chama adiciona_preventiva(self,equipments, data_programada, grupo_instrucao)
