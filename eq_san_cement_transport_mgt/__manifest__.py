# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

{
    'name': "Transport Management",
    'category': 'Stock',
    'version': '15.0.1.1',
    'author': 'Equick ERP',
    'summary': """Cement Transport Management.""",
    'depends': ['base', 'stock','sh_devide_delivery_order'],
    'license': 'OPL-1',
    'website': "",
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/res_config_settings_view.xml',
        'wizard/stock_split_picking.xml',
        'views/stock_picking_view.xml',
        'reports/report.xml',
        'reports/report_custom_delivery_slip_temp.xml',
        'wizard/weight_waiver_report_view.xml',
        'reports/report_weight_waiver_report.xml',
        'views/cement_allocation_view.xml',
        'reports/report_cement_allocation.xml',
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
