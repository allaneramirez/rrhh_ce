from odoo import models, fields


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    prestamo_pago_mensual = fields.Boolean(string="Prestamo Pago Mensual",
                                           help="Indica si la estructura es para pago de prestamo mensualmente")
