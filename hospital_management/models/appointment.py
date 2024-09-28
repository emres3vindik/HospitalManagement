from odoo import api, fields, models
from odoo.exceptions import ValidationError
from datetime import timedelta


class HospitalAppointment(models.Model):
    _name = "hospital.appointment"
    _description = "Hospital Appointment"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'patient_id'
    _order = 'appointment_time asc'

    name = fields.Char(string='Sequence', default='New')
    patient_id = fields.Many2one('hospital.patient', string="Patient", ondelete='cascade', tracking=1)
    appointment_time = fields.Datetime(string='Appointment Time', default=fields.Datetime.now)
    end_time = fields.Datetime(string='End Time', compute='_compute_end_time', store=True)
    gender = fields.Selection(related='patient_id.gender', readonly=False)
    booking_date = fields.Date(string='Booking Date', default=fields.Date.context_today, tracking=3)
    ref = fields.Char(related='patient_id.ref', string='Reference', help="Reference from patient record")
    prescription = fields.Html(string='Prescription')
    pharmacy = fields.Html(string='Pharmacy')
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Low'),
        ('2', 'High'),
        ('3', 'Very High')], string="Priority",
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_consultation', 'In Consultation'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], default='draft', string="Status", required=True, tracking=True,
    )
    doctor_id = fields.Many2one('res.users', string='Doctor', tracking=2)
    pharmacy_line_ids = fields.One2many('appointment.pharmacy.lines', 'appointment_id', string='Pharmacy Lines')
    hide_sales_price = fields.Boolean(string='Hide Sales Price')
    operations = fields.Many2one('hospital.operation', string='Operations')
    progress = fields.Integer(string='Progress', compute='_compute_progress')
    duration = fields.Float(string='Duration (hours)', tracking=4)
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    total_price = fields.Monetary(string='Total Price', compute='_compute_total_price', store=True)
    medicine_ids = fields.Many2many('hospital.pharmacy', string="Medicines")

    @api.depends('appointment_time', 'duration')
    def _compute_end_time(self):
        for appointment in self:
            if appointment.appointment_time and appointment.duration:
                appointment.end_time = appointment.appointment_time + timedelta(hours=appointment.duration)
            else:
                appointment.end_time = appointment.appointment_time

    def _check_appointment_overlap(self, appointment_time, end_time, doctor_id):
        overlapping_appointments = self.env['hospital.appointment'].search([
            ('appointment_time', '<', end_time),
            ('end_time', '>', appointment_time),
            ('doctor_id', '=', doctor_id),
            ('id', '!=', self.id)
        ])
        if overlapping_appointments:
            raise ValidationError('Seçilen zaman diliminde zaten başka bir randevu bulunmaktadır.')

    @api.model
    def create(self, vals):
        if 'appointment_time' in vals and 'duration' in vals and 'doctor_id' in vals:
            appointment_time = fields.Datetime.from_string(vals['appointment_time'])
            end_time = appointment_time + timedelta(hours=vals['duration'])
            self._check_appointment_overlap(appointment_time, end_time, vals['doctor_id'])
        res = super(HospitalAppointment, self).create(vals)
        res.update_medicine_stock()
        res.set_line_number()
        return res

    def write(self, vals):
        if 'appointment_time' in vals or 'duration' in vals or 'doctor_id' in vals:
            appointment_time = vals.get('appointment_time', self.appointment_time)
            duration = vals.get('duration', self.duration)
            doctor_id = vals.get('doctor_id', self.doctor_id.id)
            end_time = fields.Datetime.from_string(appointment_time) + timedelta(hours=duration)
            self._check_appointment_overlap(appointment_time, end_time, doctor_id)
        res = super(HospitalAppointment, self).write(vals)
        self.update_medicine_stock()
        self.set_line_number()
        return res

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise ValidationError("Sadece taslak halindeki randevuyu silebilirsiniz")
        return super(HospitalAppointment, self).unlink()

    @api.onchange('patient_id')
    def onchange_patient_id(self):
        self.ref = self.patient_id.ref

    def action_in_consultation(self):
        for rec in self:
            if rec.state == "draft":
                rec.state = 'in_consultation'

    def action_done(self):
        for rec in self:
            rec.state = 'done'

    def action_cancel(self):
        action = self.env.ref('hospital_management.action_cancel_appointment').read()[0]
        return action

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    @api.depends('state')
    def _compute_progress(self):
        for rec in self:
            if rec.state == 'draft':
                progress = 25
            elif rec.state == 'in_consultation':
                progress = 50
            elif rec.state == 'done':
                progress = 100
            else:
                progress = 0
            rec.progress = progress

    @api.depends('pharmacy_line_ids.price_subtotal')
    def _compute_total_price(self):
        for appointment in self:
            total = sum(line.price_subtotal for line in appointment.pharmacy_line_ids)
            appointment.total_price = total

    def action_share_whatsapp(self):
        if not self.patient_id.phone:
            raise ValidationError("Hastanın kayıtlı telefon numarası bulunmamaktadır")
        msg = 'Merhaba %s Randevu tarihiniz: %s, İyi Günler Dileriz' % (self.patient_id.name, self.appointment_time)
        whatsapp_api_url = 'https://api.whatsapp.com/send?phone=%s&text=%s' % (self.patient_id.phone, msg)
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': whatsapp_api_url
        }

    def update_medicine_stock(self):
        for appointment in self:
            for medicine in appointment.medicine_ids:
                if medicine.stock_quantity > 0:
                    medicine.stock_quantity -= 1
                else:
                    raise ValidationError('Seçilen ilaç (%s) stokta bulunmamaktadır.' % medicine.medicine)

    def set_line_number(self):
        serial_number = 0
        for line in self.pharmacy_line_ids:
            serial_number += 1
            line.serial_number = serial_number
        return


class AppointmentPharmacyLines(models.Model):
    _name = "appointment.pharmacy.lines"
    _description = "Appointment Pharmacy Lines"

    product_id = fields.Many2one('product.product', required=True)
    qty = fields.Integer(string='Quantity', default="1")
    price_unit = fields.Float(string='Price', related='product_id.list_price')
    appointment_id = fields.Many2one('hospital.appointment', string='Appointment')
    currency_id = fields.Many2one('res.currency', related='appointment_id.currency_id')
    price_subtotal = fields.Monetary(string='Subtotal', compute='_compute_price_subtotal')
    serial_number = fields.Integer(string="No")

    @api.depends('qty', 'price_unit')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.price_unit * line.qty
