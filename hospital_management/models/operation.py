# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HospitalOperation(models.Model):
    _name = "hospital.operation"
    _description = "Hospital Operation"
    _rec_name = 'operation_name'
    _order = 'sequence,id'

    doctor_id = fields.Many2one('res.users', string='Doctor')
    operation_name = fields.Char(name="Name")
    reference_record = fields.Reference([('hospital.patient', 'Patient'),
                                         ('hospital.appointment', 'Appointment')], name="Record")
    sequence = fields.Integer(string="Sequence", default=10)
