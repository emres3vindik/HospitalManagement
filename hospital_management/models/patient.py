# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import date
from odoo.exceptions import ValidationError
from dateutil import relativedelta


class HospitalPatient(models.Model):
    _name = "hospital.patient"
    _description = "Hospital Patient"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Name', tracking=True)
    ref = fields.Char(string='Reference', tracking=True)
    age = fields.Integer(string='Age', compute='_compute_age', inverse='inverse_compute_age', tracking=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string="Gender", tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    date_of_birth = fields.Date(string='Date Of Birth')
    image = fields.Image(string="Image")
    tag_ids = fields.Many2many('patient.tag', string="Tags")
    appointment_count = fields.Integer(string="Appointment Count", compute='_compute_appointment_count')
    parent = fields.Char(string="Parent")
    marital_status = fields.Selection([('married', 'Married'), ('single', 'Single')], string="Marital Status",
                                      tracking=True)
    partner_name = fields.Char(string="Partner Name")
    is_birthday = fields.Boolean(string="Birthday ? ", compute='_compute_is_birthday')
    phone = fields.Char(string="Phone")
    email = fields.Char(string="Email")
    social_media = fields.Char(string="Social Media")

    @api.ondelete(at_uninstall=False)
    def check_appointments(self):
        for rec in self:
            if rec.appointment_count != 0:
                raise ValidationError("Randevusu olan hasta silinemez")

    def _compute_appointment_count(self):
        for rec in self:
            rec.appointment_count = self.env['hospital.appointment'].search_count([('patient_id', '=', rec.id)])

    @api.model
    def create(self, vals):
        vals['ref'] = self.env['ir.sequence'].next_by_code('hospital.patient')
        return super(HospitalPatient, self).create(vals)

    def write(self, vals):
        if not self.ref and not vals.get('ref'):
            vals['ref'] = self.env['ir.sequence'].next_by_code('hospital.patient')
        return super(HospitalPatient, self).write(vals)

    @api.depends('date_of_birth')
    def _compute_age(self):
        for rec in self:
            today = date.today()
            if rec.date_of_birth:
                rec.age = today.year - rec.date_of_birth.year
            else:
                rec.age = 0

    @api.depends('age')
    def inverse_compute_age(self):
        today = date.today()
        for rec in self:
            rec.date_of_birth = today - relativedelta.relativedelta(years=rec.age)

    def name_get(self):
        patient_list = []
        for record in self:
            name = record.ref + ' ' + record.name
            patient_list.append((record.id, name))

        return patient_list

    @api.constrains('date_of_birth')
    def check_date(self):
        for rec in self:
            if rec.date_of_birth and rec.date_of_birth > fields.Date.today():
                raise ValidationError("Doğum günü bulundugun tarihten ileri tarihte olamaz")

    @api.depends('date_of_birth')
    def _compute_is_birthday(self):
        for rec in self:
            is_birthday = False
            if rec.date_of_birth:
                today = date.today()
                if today.day == rec.date_of_birth.day and today.month == rec.date_of_birth.month:
                    is_birthday = True
            rec.is_birthday = is_birthday

    def action_view_appointments(self):
        return
