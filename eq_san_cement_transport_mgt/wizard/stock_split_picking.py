# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

from odoo import fields, models
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError


class StockSplitPicking(models.TransientModel):
    _name = "stock.split.picking"
    _description = "Split a picking"

    total_delivered_qty = fields.Float("Total Delivered Qty")
    divide_number = fields.Float(string="Divide Number")

    picking_ids = fields.Many2many(
        "stock.picking",
        default=lambda self: self._default_picking_ids(),
    )
    move_ids = fields.Many2many("stock.move")

    def _default_picking_ids(self):
        return self.env["stock.picking"].browse(self.env.context.get("active_ids", []))

    def action_apply(self):
        return self.split_process()

    def _apply_done(self):
        return self.mapped("picking_ids").split_process()

    def _picking_action(self, pickings):
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "stock.action_picking_tree_all",
        )
        action["domain"] = [("id", "in", pickings.ids)]
        return action


    def split_process(self):
        """Use to trigger the wizard from button with correct context"""

        qty_split = int(self.total_delivered_qty / (self.divide_number or 1))
        new_moves = self.env["stock.move"]
        for i in range(qty_split):
            for picking in self.picking_ids:
                # Check the picking state and condition before split
                if picking.state == "draft":
                    raise UserError(_("Mark as todo this picking please."))

                # Split moves considering the qty_done on moves
                
                for move in picking.move_lines:
                    rounding = move.product_uom.rounding
                    qty_done = move.quantity_done
                    qty_initial = move.product_uom_qty
                    qty_diff_compare = float_compare(
                        qty_done, qty_initial, precision_rounding=rounding
                    )
                    qty_uom_split = move.product_uom._compute_quantity(
                        self.divide_number, move.product_id.uom_id, rounding_method="HALF-UP"
                    )
                    new_move_vals = move._split(qty_uom_split)
                    for move_line in move.move_line_ids:
                        if move_line.product_qty and move_line.qty_done:
                            # To avoid an error
                            # when picking is partially available
                            try:
                                move_line.write({"product_uom_qty": move_line.qty_done})
                            except UserError as e:
                                raise UserError(_(e))
                                # continue
                    new_move = self.env["stock.move"].create(new_move_vals)
                    new_move._action_confirm(merge=False)
                    new_moves |= new_move
                    if new_move:
                        backorder_picking = picking._create_split_backorder()
                        new_move.write({"picking_id": backorder_picking.id})
                        new_move.mapped("move_line_ids").write(
                            {"picking_id": backorder_picking.id}
                            )

                if new_moves:
                    new_moves._action_assign()

            picking.do_unreserve()
            picking.action_assign()

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
                },
                **(default or {})
            )
        )
        return backorder_picking