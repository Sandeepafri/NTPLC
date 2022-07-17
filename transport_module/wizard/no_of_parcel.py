# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields , api, _
from datetime import datetime,date,timedelta
from odoo.exceptions import UserError, Warning


class parcel_entry_wizard(models.TransientModel):
    
    _name = 'parcel.entry.wizard'
    
    no_of_parcel = fields.Integer('No Of Parcel')

    def add_no_of_parcels(self):
        if self._context:
            if self._context.get('active_model') == 'stock.picking':
                active_id  = self._context.get('active_id')
                stock_picking_object = self.env['stock.picking'] 
                current_record = stock_picking_object.browse(active_id)
                current_record.no_of_parcels = self.no_of_parcel
                transport_entry_record = self.env['transport.entry'].search([('picking_id','=',active_id)])
                if transport_entry_record:
                    transport_entry_record.write({'no_of_parcels':self.no_of_parcel})
                current_record.parcel_entry_done = True

class reschedule_entry(models.TransientModel):
    _name = 'reschedule.entry'
    
    reschedule_date = fields.Datetime('Rescheduled Date', required=True)

    @api.constrains('reschedule_date')
    def _onchange_date(self):
        if self.reschedule_date:
            if self.reschedule_date < datetime.now():
                raise Warning(_("Please select a proper date."))
        transport_entry = self.env['transport.entry'].browse(self._context.get('active_id'))
        entry = self.env['transport.entry'].search([('transport_id', '=', transport_entry.transport_id.id),('tag_ids', '=', transport_entry.tag_ids.id),('state', '=', 'in-progress')])           
        date_time = self.reschedule_date
        if entry:
          for transport in entry:
            length = len(transport.transport_rote_ids)-1
            if len(transport.transport_rote_ids) == len(transport.transport_rote_ids):
                if transport.transport_rote_ids[0].start_time <= date_time and transport.transport_rote_ids[length].end_time >= date_time:
                    raise UserError(
                    _(' Fleet is occupied for selected date.'))
            else:
                if transport.transport_rote_ids[0].start_time <= date_time and transport.transport_rote_ids[0].end_time >= date_time:
                    raise UserError(
                    _(' Fleet is occupied for selected date.'))

    def reschedule_transport_entry(self):
        transport_entry = self.env['transport.entry'].browse(self._context.get('active_id'))
        transport_entry.write({
                'date':self.reschedule_date,
                'state' : 'draft' 
            })
        picking_id = self.env['stock.picking'].search([('name', '=', transport_entry.picking_id.name)])
        
        for i in transport_entry.transport_rote_ids:
            i.write({'state':'draft'})

        for picking in picking_id.transport_routes_ids:
            picking.write({'state':'draft'})



                                                
