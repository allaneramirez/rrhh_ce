from odoo import models, fields, api, _

class HrPayslip(models.Model):
    _inherit = 'hr.leave'

    period_from = fields.Char(string='Perido del (año)')
    period_to = fields.Char(string='Perido al (año)')