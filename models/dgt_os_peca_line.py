# -*- coding: utf-8 -*-
import time
from datetime import datetime,timedelta
from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo import netsvc
from odoo.exceptions import UserError
import logging

class dgtOsPecasLineInherit(models.Model):
  
    _inherit = 'dgt_os.os.pecas.line'

    
    qty_contrato = fields.Float(
        'Qtd Contrato',compute = '_compute_qty_contrato',
        digits=dp.get_precision('Product Unit of Measure'),
        help="Quantidade de peças em contrato.\n"
             "Peças disponível em contrato ao qual o equipamento pertence.\n "
             "Caso não o equipamento não pertença a nenhum contrato o valor é zero.\n",readonly=True, copy=False)
    qty_autorizada = fields.Float(
        'Qtd Autorizada',compute = '_compute_qty_contrato',
        digits=dp.get_precision('Product Unit of Measure'),
        help="Quantidade de peças em autorizada.\n"
             "Peças autorizadas em contrato ao qual o equipamento pertence.\n "
             "Caso o equipamento não pertença a nenhum contrato o valor é zero.\n",readonly=True, copy=True)
    peca_autorizada = fields.Boolean(string=u'Peça autorizada')
    
    
    #TODO
    # refazer esta função está dando erro na contabilização das quantidades
    @api.one
    @api.depends('product_uom_qty', 'product_id')
    def _compute_qty_contrato(self):
        return 0
        #procura contrato de preventiva ativo
        contrato = self.env['dgt_preventiva.contratos'].search([
            ('client', '=', self.os_id.cliente_id.id),
            ('data_fim','>=', fields.date.today())
            ])
        #procura equipamentos do contrato
        if contrato.id:
            equip = self.env['dgt_preventiva.contratos.equip.lines'].search(['&',('contrato','=',contrato.id),('equipment_id','=',self.os_id.equipment_id.id)])
            #for equip in equips:
            if equip.id:
                #procura peças se todas as peças estão inclusas no contrato
                if contrato.pecas_inclusas == 'todas':
                    self.qty_contrato = 9999
                    self.peca_autorizada = True
                    self.qty_autorizada = self.product_uom_qty
                    return True
                
                elif contrato.pecas_inclusas == 'list':
                    #procura se peça esta na lista do contrato
                    peca = self.env['dgt_preventiva.contratos.pecas.lines'].search([
                        ('contrato','=', contrato.id),
                        ('pecas','=', self.product_id.id)])
                    if peca.id:
                        self.qty_contrato = peca.product_uom_qty - peca.product_uom_qty_used
                        self.qty_autorizada = self.qty_contrato - self.product_uom_qty
                        if self.qty_autorizada > 0:
                            
                            self.peca_autorizada = True
                        else:
                            self.qty_autorizada = 0
                            self.peca_autorizada = False
                        return True
         
        self.qty_contrato = 0
        self.peca_autorizada = False
                    
                           
                  
                    
            