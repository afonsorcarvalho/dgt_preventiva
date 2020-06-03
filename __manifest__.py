# -*- coding: utf-8 -*-
{
    'name': "dgt_preventiva",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Afonso Carvalho",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','dgt_os','sale_commission','br_sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/dgt_preventiva_views.xml',
        'views/equipment_category_view.xml',
        'views/dgt_os_form_view.xml',
        'views/dgt_preventiva_contratos.xml',
        'reports/report_assinatura_template.xml',
        'reports/reports_preventiva.xml',
        'reports/report_preventiva_template.xml',
        'reports/report_cronograma_preventiva_template.xml',
        'reports/report_cliente_equipment_template.xml',
        'reports/report_checklist_template.xml',

        'data/ir_sequence_data.xml',
        'data/mail_aviso_preventiva_template.xml'

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}