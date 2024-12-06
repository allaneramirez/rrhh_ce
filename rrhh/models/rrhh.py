# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from dateutil.relativedelta import *
class rrhh_historial_salario(models.Model):
    _name = "rrhh.historial_salario"
    _description = 'Historial de Salarios'

    salario = fields.Float('Salario', required=True)
    fecha = fields.Date('Fecha', required=True)
    contrato_id = fields.Many2one('hr.contract','Contato')
    employee_id = fields.Many2one('hr.employee', 'Empleado')
