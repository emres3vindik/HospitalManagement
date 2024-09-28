import datetime
from odoo import api, fields, models


class CancelAppointmentWizard(models.TransientModel):
    _name = "cancel.appointment.wizard"
    _description = "Cancel Appointment Wizard"

    @api.model
    def default_get(self, fields):
        res = super(CancelAppointmentWizard, self).default_get(fields)
        res['date_cancel'] = datetime.date.today()
        if self.env.context.get('active_id'):
            res['appointment_id'] = self.env.context.get('active_id')
        return res

    appointment_id = fields.Many2one('hospital.appointment', string="Appointment")
    reason = fields.Text(string="Reason")
    date_cancel = fields.Date(string="Cancellation Date")

    def action_cancel(self):
        if self.appointment_id.booking_date == fields.Date.today():
            message = 'Rezervasyon yapılan günde iptal edilemez'
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Notification',
                    'message': message,
                    'type': 'danger',
                    'sticky': False,
                }
            }
        self.appointment_id.state = 'cancel'
        message = 'Rezervasyon iptal edildi'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Notification',
                'message': message,
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }
