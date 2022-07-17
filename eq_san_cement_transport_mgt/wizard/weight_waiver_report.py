# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

from odoo import models, api, fields, _
from odoo.exceptions import ValidationError


class weight_waiver_report(models.TransientModel):
    _name = 'weight.waiver.report'
    _description = "Weight Waiver Report"

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id)
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    state = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    name = fields.Char(string='File Name', readonly=True)
    data = fields.Binary(string='File', readonly=True)

    def print_pdf_report(self):
        if self.end_date < self.start_date:
            raise ValidationError(_('End Date should be greater than Start Date.'))
        return self.env.ref('eq_san_cement_transport_mgt.custom_weight_waiver_report').report_action(self)

    def get_weight_waiver_report_data(self):
        domain = [('sale_id','!=',False),('picking_type_code','=','outgoing'),('transport_status','=','Done'),
            ('company_id','=',self.company_id.id),('date_done','>=',self.start_date),('date_done','<=',self.end_date)]
        picking_ids = self.env['stock.picking'].search(domain)
        lst = []
        for picking in picking_ids:
            lst.append({'picking_name':picking.name,'loaded_truck_weight':picking.loaded_truck_weight,
                    'empty_truck_weight':picking.empty_truck_weight,'difference_weight':picking.difference_weight})
        return lst

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
