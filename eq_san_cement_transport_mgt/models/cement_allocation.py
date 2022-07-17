# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class cement_allocation(models.Model):
    _name = 'cement.allocation'
    _description = "Cement Allocation"

    name = fields.Char(string="Name",copy=False)
    status = fields.Selection([('Draft','Draft'),('Running','Running'),
        ('Close','Close')],string="Status",copy=False,default="Draft")
    total_allocation = fields.Float(string="Total Allocation",copy=False)
    allocated = fields.Float(string="Total Allocated",copy=False,compute="cal_total_allocated",store=True)
    balance = fields.Float(string="Balance",copy=False,compute="cal_total_balance",store=True)
    user_id = fields.Many2one('res.users',string="Responsible User",default=lambda self: self.env.user)
    line_ids = fields.One2many('cement.allocation.line','cement_allocation_id', string="Allocation Lines",copy=False)
    allocation_line_seq_ids = fields.One2many('cement.allocation.sequence','cement_allocation_id', string="Allocation Lines",copy=False)
    running_date = fields.Date(string="Running Date",copy=False)
    close_date = fields.Date(string="Close Date",copy=False)

    @api.depends('line_ids','line_ids.allocation')
    def cal_total_allocated(self):
        for each in self:
            each.allocated = sum(each.line_ids.mapped('allocation'))

    @api.depends('allocated','total_allocation')
    def cal_total_balance(self):
        for each in self:
            each.balance = (each.total_allocation - each.allocated)

    def running_allocation(self):
        if self.status == 'Draft':
            already_running = self.env['cement.allocation'].search_count([('id','!=',self.id),('status','=','Running')])
            if already_running:
                raise UserError(_("one of the allocation is already running."))

            lst = []
            count = 1
            for line in self.line_ids:
                for picking in line.picking_ids:
                    vals = {'partner_id':line.partner_id.id,'picking_id':picking.id,'token_no':count,
                        'sale_order_id':line.sale_order_id.id,
                        'allocation':sum(picking.move_lines.mapped('product_uom_qty')),
                        'cement_allocation_id':line.cement_allocation_id.id,
                        }
                    count +=1
                    lst.append((0,0,vals))
            
            if lst:
                self.allocation_line_seq_ids.unlink()
                self.allocation_line_seq_ids = lst
            self.status = 'Running'
            self.running_date = datetime.datetime.now().date()

    def close_allocation(self):
        if self.status == 'Running':
            self.status = 'Close'
            self.close_date = datetime.datetime.now().date()

    def unlink(self):
        for each in self:
            if each.status != 'Draft':
                raise UserError(_("You can't delete allocation which are not in draft stage."))
        return super(cement_allocation, self).unlink()


class cement_allocation_line(models.Model):
    _name = 'cement.allocation.line'
    _description = "Cement Allocation Line"

    cement_allocation_id = fields.Many2one('cement.allocation',string="Cement Allocation")
    partner_id = fields.Many2one('res.partner',string="Customer")
    allocation = fields.Float(string="Allocation",copy=False)

    partner_id = fields.Many2one('res.partner',string="Customer")
    # partner_code = fields.Char(string="Customer Code",copy=False)
    # token_no = fields.Integer(string="Token No",copy=False,compute="_sequence_ref")
    sale_order_id = fields.Many2one('sale.order',string="Sale Order")
    picking_ids = fields.Many2many('stock.picking',string="Delivery Orders")
    # total_order_qty = fields.Float(string="Order Qty",compute="cal_order_qty")
    # remaining_order_qty = fields.Float(string="Remaining Order Qty",compute="cal_order_qty")
    show_order_qty = fields.Char(string="Order Allocation",compute="cal_order_qty")
    allocation = fields.Float(string="Allocation",copy=False)

    def cal_order_qty(self):
        for each in self:
            total_order_qty = 0.00
            remaining_order_qty = 0.00
            for picking in each.sale_order_id.picking_ids:
                total_order_qty += sum(picking.move_lines.mapped('product_uom_qty'))
                if picking.state not in ('done','cancel'):
                    remaining_order_qty += sum(picking.move_lines.mapped('product_uom_qty'))
            each.show_order_qty = (str(remaining_order_qty) + '/' + str(total_order_qty))

    @api.constrains('picking_ids')
    def check_allocation_delivery_order(self):
        for line in self:
            counts = self.env['cement.allocation.line'].search_count([('picking_ids','in',line.picking_ids.ids),
                ('id','!=',line.id),('cement_allocation_id','=',line.cement_allocation_id.id)])
            if counts:
                raise UserError(_("delvery order already select on another allocation lines."))

    # @api.onchange('partner_id')
    # def onchange_partner_id(self):
    #     self.partner_code = self.partner_id.ref or ''

    # @api.depends('cement_allocation_id.line_ids', 'cement_allocation_id.line_ids.partner_id')
    # def _sequence_ref(self):
    #     for line in self:
    #         no = 0
    #         for l in line.cement_allocation_id.line_ids:
    #             no += 1
    #             l.token_no = no

    # @api.onchange('sale_order_id','partner_id')
    # def onchange_sale_order_ids(self):
    #     if self.partner_id:
    #         order_ids = self.env['sale.order'].search([('partner_id','=',self.partner_id.id),('state','in',('sale','done')),
    #             ('picking_ids.state','not in',('done','cancel'))])
    #         if order_ids:
    #             domain = {'sale_order_id':[('id','in',order_ids.ids)]}
    #             return {'domain':domain}

    @api.onchange('sale_order_id')
    def onchange_sale_order_id(self):
        self.picking_ids = False
        self.allocation = 0.00

    @api.onchange('picking_ids')
    def onchange_picking_ids(self):
        allocation = 0.00
        for picking in self.picking_ids:
            allocation += sum(picking.move_lines.mapped('product_uom_qty'))
        self.allocation = allocation


class cement_allocation_sequence(models.Model):
    _name = 'cement.allocation.sequence'
    _description = "Cement Allocation Sequence"

    cement_allocation_id = fields.Many2one('cement.allocation',string="Cement Allocation")
    allocation = fields.Float(string="Allocation",copy=False)
    partner_id = fields.Many2one('res.partner',string="Customer")
    token_no = fields.Integer(string="Token No",copy=False)
    sale_order_id = fields.Many2one('sale.order',string="Sale Order")
    picking_id = fields.Many2one('stock.picking',string="Delivery Orders")