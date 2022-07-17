# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    vehicle_number = fields.Char(string="Vehicle Number",copy=False)
    driver_name = fields.Char(string="Driver Name",copy=False)
    empty_truck_weight = fields.Float(string="Empty Truck Weight",copy=False)
    loaded_truck_weight = fields.Float(string="Loaded Truck Weight",copy=False)
    difference_weight = fields.Float(string="Difference Weight",copy=False)
    transport_status = fields.Selection([('EntryPass','Entry Pass'),('WeightBridgein','Weight Bridg IN'),
    ('CementDeliveryPoint','Delivery Point'),('WeightBridgeout','Weight Bridge Out'),
    ('ExitPoint','Exit Point'),('Done','Done')]
    ,string="Delivery Status",copy=False)
    cement_allocation_id = fields.Many2one('cement.allocation',string="Allocation")

    def confirm_entry_pass(self):
        if self.transport_status == 'EntryPass':
            self.transport_status = 'WeightBridgein'
    
    def confirm_weight_bridge(self):
        if not self.empty_truck_weight:
            raise UserError(_("Please enter Empty Truck Weight."))
        
        if self.transport_status == 'WeightBridgein':
            self.transport_status = 'CementDeliveryPoint'
    
    def confirm_deliver_point(self):
        if self.transport_status == 'CementDeliveryPoint':
            self.transport_status = 'WeightBridgeout'

    def confirm_weight_bridge_out(self):
        if not self.loaded_truck_weight:
            raise UserError(_("Please enter Loaded Truck Weight."))
        if self.transport_status == 'WeightBridgeout':
            loaded_truck_weight = self.empty_truck_weight + sum(self.move_lines.mapped('product_uom_qty'))
            difference_weight = (self.loaded_truck_weight - self.empty_truck_weight)
            allowed_diff_weight = float(self.env['ir.config_parameter'].sudo().get_param('eq_san_cement_transport_mgt.diff_weight_allowed'))
            max_allowed_diff_weight = (loaded_truck_weight * allowed_diff_weight) / 100
            if self.loaded_truck_weight > (loaded_truck_weight + max_allowed_diff_weight):
                raise UserError(_("Empty and loded truck have difference. please enter correct loaded truck weight."))
            self.transport_status = 'ExitPoint'
            self.difference_weight = (self.loaded_truck_weight - self.empty_truck_weight)

    def confirm_exit_point(self):
        if self.transport_status == 'ExitPoint':
            if self.state not in ('cancel','done'):
                self.set_delivery_quantities()
            self.transport_status = 'Done'

    def set_delivery_quantities(self):
        for move in self.move_lines:
            if move.state not in ('partially_available', 'assigned'):
                continue
            for move_line in move.move_line_ids:
                if move.has_tracking != 'none' and not (move_line.lot_id or move_line.lot_name):
                    continue
                move_line.qty_done = move_line.product_uom_qty
        self.button_validate()

    def _create_split_backorder(self, default=None):
        """Copy current picking with defaults passed, post message about
        backorder"""
        self.ensure_one()
        backorder_picking = self.copy(
            dict(
                {
                    "name": "/",
                    "move_lines": [],
                    "move_line_ids": [],
                    "backorder_id": self.id,
                    "transport_status":"EntryPass",
                },
                **(default or {})
            )
        )
        return backorder_picking


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    diff_weight_allowed = fields.Float(config_parameter='eq_san_cement_transport_mgt.diff_weight_allowed',string="Allowed Weight (%)")


class stock_move(models.Model):
    _inherit = 'stock.move'

    def _get_new_picking_values(self):
        res = super(stock_move,self)._get_new_picking_values()
        for move in self:
            if move.sale_line_id:
                res['transport_status'] = 'EntryPass'
        return res