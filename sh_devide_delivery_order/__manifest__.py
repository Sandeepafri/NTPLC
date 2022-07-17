# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
{
    'name': 'Create Multiple Delivery Orders From Sale Order',

    'author': 'Softhealer Technologies',

    "license": "OPL-1",

    'website': 'https://www.softhealer.com',

    "support": "support@softhealer.com",

    'version': '15.0.1',

    'category': 'sales',

    'summary': "Split Delivery Orders Module, Divide Delivery Orders, Extract Outgoing Order App, Generate Multiple Delivery Orders From Sale Order, Extract Delivery Order, Divide DO,Create Multi Delivery Order Odoo",

    'description': """
Do you want to split the delivery order? This module helps you to create multiple delivery orders from the single sale order. You can easily manage multiple outgoing orders and you can divide the delivery orders. cheers!
 Create Multiple Delivery Orders From Sale Order Odoo
 Split Delivery Orders Module, Divide Delivery Orders, Extract Outgoing Order, Generate Multiple Delivery Orders From Sale Order, Create Multi Delivery Order Odoo.
 Split Delivery Orders Module, Divide Delivery Orders, Extract Outgoing Order App, Generate Multiple Delivery Orders From Sale Order, Extract Delivery Order, Create Multi Delivery Order Odoo.
Crear múltiples órdenes de entrega a partir de la orden de venta Odoo
 Módulo de órdenes de entrega divididas, dividir órdenes de entrega, extraer orden de salida, generar múltiples órdenes de entrega de orden de venta, crear orden de entrega múltiple Odoo.
 Módulo de órdenes de entrega divididas, división de órdenes de entrega, aplicación de extracción de orden de salida, generación de múltiples órdenes de entrega a partir de orden de venta, extracción de orden de entrega, creación de orden de entrega múltiple Odoo.
""",

    'depends': ['sale_management', 'stock'],

    'data': [
        "views/sale_order_view.xml"
    ],
    "images": ["static/description/background.png", ],
    'auto_install': False,
    'installable': True,
    'application': True,
    "price": 30,
    "currency": "EUR"
}
