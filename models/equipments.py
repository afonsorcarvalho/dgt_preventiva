from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class CategoryInstructionPreventiva(models.Model):
    #_name = 'dgt_os.equipment.category.instruction.inherit'
    _inherit = 'dgt_os.equipment.category.instruction'
    _order = 'section ASC'
    grupo_id = fields.Many2one(
        string="Grupo",
        comodel_name="dgt_os.instruction.grupo",
        
        ondelete="cascade",
        help="Grupo de instruções para dividir em preventivas em tempos diferentes.",
    )
    tempo_duracao = fields.Float(string="Tempo de duração",help="Tempo em minutos de duração da tarefa da preventiva")
    tem_medicao = fields.Boolean(string='Tem medição?')
    grandeza = fields.Many2one(string = 'Grandeza',comodel_name='dgt_os.equipment.category.instruction.grandeza', ondelete="set null", help="Grandeza da instrução caso envolve medições",)
    
    tipo_de_campo = fields.Selection(
        string=u'Tipo de Campo',
        selection=[('Valor', 'float'), ('Checkbox', 'ok'),('Seleção','Selection')]
    )
    troca_peca = fields.Boolean(string="Substituição de Peça?" )    
    peca = fields.Many2one('product.product', u'Peça')
    peca_qtd = fields.Float('Qtd', default=1.0,	digits=dp.get_precision('Product Unit of Measure'))
    section = fields.Many2one(
        string=u'Seção',
        comodel_name='dgt_os.equipment.category.instruction.secao',
        ondelete='set null',
    )
    
    
    
   
    

class CategoryInstrucionPreventivaGrupo(models.Model):
    """ The summary line for a class docstring should fit on one line.

    Fields:
      name (Char): Nome do grupo de instruções de preventiva.

    """

    _name = 'dgt_os.instruction.grupo'
    _description = u'Grupo de instruções de preventivas'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string=u'Grupo',
        required=True
       
    )   
    categoria = fields.Many2one(
        string="Categoria de equipamentos",
        comodel_name="dgt_os.equipment.category",
        ondelete="set null",
        help="Categoria de equipamento a qual pertence o grupo de instruções",
    )   

    periodicidade = fields.Integer(string="Periodicidade", help="Tempo em dias para próxima preventiva")
    instruction_type = fields.Selection(
        string="Tipo de instrução",
        selection=[
                ('preventiva', 'Preventiva'),
                ('instalacao', 'Instalação'),
                ('corretiva', 'Corretiva'),
                ('calibracao', 'Calibração'),
                
                
        ],
    )


class CategoryInstrucionPreventivaGrandeza(models.Model):
    """ The summary line for a class docstring should fit on one line.

    Fields:
      name (Char): Human readable name which will identify each record.

    """

    _name = 'dgt_os.equipment.category.instruction.grandeza'
    _description = u'Grandezas da instruççoes de preventiva'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string=u'Nome',
        required=True
       
    )
    
    unidade = fields.Char(
        string=u'Unidade',help="Unidade da grandeza. exemplo: KM/h, Joules"

    )

class CategoryInstrucionSecao(models.Model):
    """ The summary line for a class docstring should fit on one line.

    Fields:
      name (Char): Human readable name which will identify each record.

    """

    _name = 'dgt_os.equipment.category.instruction.secao'
    _description = u'Seção instruççoes de preventiva'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string=u'Nome',
        required=True
       
    )
   

    


    
