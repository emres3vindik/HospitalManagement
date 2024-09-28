# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HospitalPharmacy(models.Model):
    _name = "hospital.pharmacy"
    _description = "Hospital Pharmacy"
    _rec_name = 'medicine'

    medicine = fields.Char(string='Medicine', required=True)
    price = fields.Float(string='Price', required=True)
    barcode = fields.Char(string='Barcode Number', size=11, required=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id.id)
    manufacturer = fields.Char(string="Manufacturer")
    category = fields.Char(string="Category")
    description = fields.Text(string="Description")
    image = fields.Image(string="Image")
    stock_quantity = fields.Integer("Stock Quantity")
    stock_value = fields.Float("Stock Value", compute="_compute_stock_value")

    @api.depends('price', 'stock_quantity')
    def _compute_stock_value(self):
        for record in self:
            record.stock_value = record.price * record.stock_quantity
