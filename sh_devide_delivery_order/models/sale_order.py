# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from collections import defaultdict
from dateutil.relativedelta import relativedelta
from itertools import groupby
from odoo import api, fields, models, _
from odoo.tools import float_compare
from odoo.exceptions import UserError
from odoo import SUPERUSER_ID, _, api, fields, models, registry



class Picking(models.Model):
    _inherit = 'stock.picking'

    is_separate_do = fields.Boolean("Is Separate DO?")


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    no_of_do = fields.Integer("Number Of DO", default=1)

    def _prepare_procurement_values(self, group_id=False):
        res = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        res['no_of_do'] = self.no_of_do
        return res


class StockRule(models.Model):
    _inherit = 'stock.rule'

    @api.model
    def _run_pull(self, procurements):
        moves_values_by_company = defaultdict(list)
        mtso_products_by_locations = defaultdict(list)
        for procurement, rule in procurements:
            if not rule.location_src_id:
                msg = _('No source location defined on stock rule: %s!') % (
                    rule.name, )
                raise UserError(msg)

            if rule.procure_method == 'mts_else_mto':
                mtso_products_by_locations[rule.location_src_id].append(
                    procurement.product_id.id)

        # Get the forecasted quantity for the `mts_else_mto` procurement.
        forecasted_qties_by_loc = {}
        for location, product_ids in mtso_products_by_locations.items():
            products = self.env['product.product'].browse(
                product_ids).with_context(location=location.id)
            forecasted_qties_by_loc[location] = {
                product.id: product.free_qty for product in products}

        # Prepare the move values, adapt the `procure_method` if needed.

        for procurement, rule in procurements:
            # Added loop for stock move --- softhealer
            if procurement.values and procurement.values.get('no_of_do') > 0:
                for i in range(procurement.values.get('no_of_do')):
                    procure_method = rule.procure_method
                    if rule.procure_method == 'mts_else_mto':
                        qty_needed = procurement.product_uom._compute_quantity(
                            procurement.product_qty, procurement.product_id.uom_id)
                        qty_available = forecasted_qties_by_loc[rule.location_src_id][procurement.product_id.id]
                        if float_compare(qty_needed, qty_available, precision_rounding=procurement.product_id.uom_id.rounding) <= 0:
                            procure_method = 'make_to_stock'
                            forecasted_qties_by_loc[rule.location_src_id][procurement.product_id.id] -= qty_needed
                        else:
                            procure_method = 'make_to_order'

                    move_values = rule._get_stock_move_values(*procurement)
                    move_values['procure_method'] = procure_method
                    moves_values_by_company[procurement.company_id.id].append(
                        move_values)
            else:
                procure_method = rule.procure_method
                if rule.procure_method == 'mts_else_mto':
                    qty_needed = procurement.product_uom._compute_quantity(
                        procurement.product_qty, procurement.product_id.uom_id)
                    qty_available = forecasted_qties_by_loc[rule.location_src_id][procurement.product_id.id]
                    if float_compare(qty_needed, qty_available, precision_rounding=procurement.product_id.uom_id.rounding) <= 0:
                        procure_method = 'make_to_stock'
                        forecasted_qties_by_loc[rule.location_src_id][procurement.product_id.id] -= qty_needed
                    else:
                        procure_method = 'make_to_order'

                move_values = rule._get_stock_move_values(*procurement)
                move_values['procure_method'] = procure_method
                moves_values_by_company[procurement.company_id.id].append(
                    move_values)

        for company_id, moves_values in moves_values_by_company.items():
            # create the move as SUPERUSER because the current user may not have the rights to do it (mto product launched by a sale for example)
            moves = self.env['stock.move'].with_user(SUPERUSER_ID).sudo().with_company(company_id).create(moves_values)
            # Since action_confirm launch following procurement_group we should activate it.
            moves._action_confirm()
        return True

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, company_id, values):
        ''' Returns a dictionary of values that will be used to create a stock move from a procurement.
        This function assumes that the given procurement has a rule (action == 'pull' or 'pull_push') set on it.

        :param procurement: browse record
        :rtype: dictionary
        '''
        group_id = False
        if self.group_propagation_option == 'propagate':
            group_id = values.get('group_id', False) and values['group_id'].id
        elif self.group_propagation_option == 'fixed':
            group_id = self.group_id.id

        date_scheduled = fields.Datetime.to_string(
            fields.Datetime.from_string(
                values['date_planned']) - relativedelta(days=self.delay or 0)
        )
        date_deadline = values.get('date_deadline') and (fields.Datetime.to_datetime(
            values['date_deadline']) - relativedelta(days=self.delay or 0)) or False
        partner = self.partner_address_id or (values.get(
            'group_id', False) and values['group_id'].partner_id)
        if partner:
            product_id = product_id.with_context(
                lang=partner.lang or self.env.user.lang)
        picking_description = product_id._get_description(self.picking_type_id)
        if values.get('product_description_variants'):
            picking_description += values['product_description_variants']
        # it is possible that we've already got some move done, so check for the done qty and create
        # a new move with the correct qty
        qty_left = product_qty

        move_dest_ids = []
        if not self.location_id.should_bypass_reservation():
            move_dest_ids = values.get('move_dest_ids', False) and [
                (4, x.id) for x in values['move_dest_ids']] or []
        # devide qty by number of do -- softhealer
        if values.get('no_of_do') > 0:
            qty_left = product_qty / values.get('no_of_do')

        move_values = {
            'name': name[:2000],
            'company_id': self.company_id.id or self.location_src_id.company_id.id or self.location_id.company_id.id or company_id.id,
            'product_id': product_id.id,
            'product_uom': product_uom.id,
            'product_uom_qty': qty_left,
            'partner_id': self.partner_address_id.id or (values.get('group_id', False) and values['group_id'].partner_id.id) or False,
            'location_id': self.location_src_id.id,
            'location_dest_id': location_id.id,
            'move_dest_ids': values.get('move_dest_ids', False) and [(4, x.id) for x in values['move_dest_ids']] or [],
            'rule_id': self.id,
            'procure_method': self.procure_method,
            'origin': origin,
            'picking_type_id': self.picking_type_id.id,
            'group_id': group_id,
            'route_ids': [(4, route.id) for route in values.get('route_ids', [])],
            'warehouse_id': self.propagate_warehouse_id.id or self.warehouse_id.id,
            'date': date_scheduled,
            'date_deadline': date_deadline,
            'propagate_cancel': self.propagate_cancel,
            'description_picking': product_id._get_description(self.picking_type_id),
            'priority': values.get('priority', "1"),
        }
        for field in self._get_custom_move_fields():
            if field in values:
                move_values[field] = values.get(field)

        return move_values


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _search_picking_for_assignation(self):
        self.ensure_one()
        picking = self.env['stock.picking'].search([
            ('group_id', '=', self.group_id.id),
            ('location_id', '=', self.location_id.id),
            ('location_dest_id', '=', self.location_dest_id.id),
            ('picking_type_id', '=', self.picking_type_id.id),
            ('printed', '=', False),
            ('is_separate_do', '=', False),
            ('immediate_transfer', '=', False),
            ('state', 'in', ['draft', 'confirmed', 'waiting', 'partially_available', 'assigned'])], limit=1)
        return picking

    def _assign_picking(self):
        """ Try to assign the moves to an existing picking that has not been
        reserved yet and has the same procurement group, locations and picking
        type (moves should already have them identical). Otherwise, create a new
        picking to assign them to. """
        Picking = self.env['stock.picking']

        grouped_moves = groupby(sorted(self, key=lambda m: [
                                f.id for f in m._key_assign_picking()]), key=lambda m: [m._key_assign_picking()])

        for group, moves in grouped_moves:
            moves = self.env['stock.move'].concat(*list(moves))
            new_picking = False
            for move in moves:
                if move.sale_line_id.no_of_do > 0:
                    new_picking = True
                    # Split picking -- softhealer
                    picking = Picking.create(move._get_new_picking_values())
                    picking.write({'is_separate_do': True})
                    move.write({'picking_id': picking.id})
                    move._assign_picking_post_process(new=new_picking)

                else:

                    picking = move._search_picking_for_assignation()
                    if picking:
                        if any(picking.partner_id.id != m.partner_id.id or
                                picking.origin != m.origin for m in moves):
                            picking.write({
                                'partner_id': False,
                                'origin': False,
                            })
                    else:
                        new_picking = True
                        picking = Picking.create(
                            moves._get_new_picking_values())

                    move.write({'picking_id': picking.id})
                    move._assign_picking_post_process(new=new_picking)

        return True
