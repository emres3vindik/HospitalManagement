from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PatientTag(models.Model):
    _name = "patient.tag"
    _description = "Patient Tag"

    name = fields.Char(string='Name', required=True)
    active = fields.Boolean(string="Active", default=True)
    color = fields.Integer(string="Color")

    @api.constrains('name')
    def check_tag(self):
        for rec in self:
            tag = self.env['patient.tag'].search([('name', '=', rec.name), ('id', '!=', rec.id)])
            if tag:
                raise ValidationError("Tag benzersiz olmalıdır")







