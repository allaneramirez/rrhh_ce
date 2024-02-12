# -*- coding:utf-8 -*-

from odoo import fields, models, api, _

class HrPayslipInputType2(models.Model):
    _name = 'hr.payslip.input.type.2'
    _description = 'Input Types'

    name = fields.Char(string='Description', required=True)
    code = fields.Char(required=True)

