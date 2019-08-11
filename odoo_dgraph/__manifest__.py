# -*- coding: utf-8 -*-
{
    'name': "Odoo Dgraph",

    'summary': """
        Odoo Dgraph""",

    'description': """
        Odoo Dgraph
    """,

    'author': "Zhiguo Yuan",
    'email': "oliver.yuan@openstone.cn",
    'website': "http://www.openstone.cn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Base',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/menu_views.xml',
        'views/graph_index_views.xml',
        'views/res_config_settings_views.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],

    'external_dependencies': {'python': ['pydgraph','rfc3339']},
    'application': True,
}