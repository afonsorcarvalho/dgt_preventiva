# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date
from datetime import time
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from odoo.exceptions import UserError
import pytz
import logging

_logger = logging.getLogger(__name__)


class dgt_preventiva(models.Model):
    _name = 'dgt_preventiva.dgt_preventiva'

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
    )
    grupo_id = fields.Many2many(
        'dgt_os.instruction.grupo', string='Grupo de Instruções'
    )

    data_programada = fields.Datetime(
        string=u'Data Programada',

        default=fields.datetime.now(),
    )

    data_programada_fim = fields.Datetime(
        string=u'Data Programada fim',
        default=fields.datetime.now(),
    )

    data_execucao = fields.Datetime(
        string=u'Data Execução',
        default=fields.datetime.now(),
    )

    data_execucao_fim = fields.Datetime(
        string=u'Data Execução',
        default=fields.datetime.now(),
    )

    gerada_os = fields.Boolean(
        string=u'Gerada Os',
    )
    os_id = fields.Many2one(
        string="Ordem de serviço",
        comodel_name="dgt_os.os",
        ondelete="set null",
        help="Explain your field.",
    )
    preventiva_executada = fields.Boolean(
        string=u'Preventiva executada?',
    )
    
    @api.multi
    def write(self, vals):
        if self.gerada_os:
            raise UserError(
                _("Não pode alterar preventiva que já tem OS gerada"))
            
        result = super(dgt_preventiva, self).write(vals)
        return result
    
    @api.multi
    def cron_agenda_preventiva(self):
        _logger.info("Entrou no agendamento da preventiva...")
        hoje = fields.Date.today()
        
        res = self.env['dgt_preventiva.dgt_preventiva'].search(
            [('gerada_os', '=', False), ('data_programada', '>=', hoje),('data_programada', '<=', hoje + timedelta(days=30))])
        _logger.info(res)
        for r in res:
            _logger.info("Grupo...")
            _logger.info(r.grupo_id)
            
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
                
                
            })
            r.write({'gerada_os': True, 'os_id': os.id})
             
          
        


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
