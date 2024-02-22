# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

class Contract(models.Model):
    _inherit = "hr.contract"

    motivo_terminacion = fields.Selection([
        ('reuncia', 'Renuncia'),
        ('despido', 'Despido'),
        ('despido_justificado', 'Despido Justificado'),
        ], 'Motivo de terminacion')
    fecha_firma = fields.Date('Fecha de Firma del contrato')
    base_extra = fields.Monetary('Base Extra', digits=(16,2), track_visibility='onchange')
    wage = fields.Monetary('Wage', digits=(16, 2), required=True, help="Employee's monthly gross wage.",track_visibility='onchange')
    fecha_reinicio_labores = fields.Date('Fecha de reinicio labores')
    horario_contrato = fields.Many2many('resource.calendar',string="Horarios de Contrato")
    temporalidad_contrato = fields.Char('Temporalidad del contrato')
    tipo_contrato = fields.Char('Tipo del contrato')
    calcula_indemnizacion = fields.Boolean('Calcula indemnizacion')
    historial_salario_ids = fields.One2many('rrhh.historial_salario','contrato_id',string='Historial de salario')
    bonificacion = fields.Monetary(string='Bonificación decreto',digits=(16, 2))
    otras_bonificaciones = fields.Monetary(string='Otras Bonificaciones fijas',digits=(16, 2))
    # INGRESOS
    otros_ingresos = fields.Monetary(string='Otros Ingresos', help="Monto anual de otros ingresos que no formen parte del salario mensual (diferidos)",digits=(16, 2),track_visibility='onchange')
    b14_isr = fields.Monetary(string='Bono 14',digits=(16, 2),compute='_compute_exento')
    agui_isr = fields.Monetary(string='Aguinaldo', digits=(16, 2))
    ingreso_base_anual = fields.Monetary(digits=(16, 2), compute='_compute_ingreso_base_anual',                                      )
    ingreso_total_anual = fields.Monetary(digits=(16, 2), compute='_compute_ingreso_total_anual',
                                         )
    # DEDUCCIONES
    deducciones_sin_comprobantes = fields.Monetary(digits=(16, 2), track_visibility='onchange', default=48000)
    deducciones_iggs = fields.Monetary(digits=(16, 2), compute='_compute_deduction_iggs')
    deducciones_total_anual = fields.Monetary(digits=(16, 2), compute='_compute_deductions_total_anual')

    # ISR
    isr_total = fields.Monetary(digits=(16, 2), compute='_compute_total_isr')

    @api.depends('wage', 'otros_ingresos')
    def _compute_ingreso_base_anual(self):
        # sueldo mensual anual mas la bonificaicon anual
        for contract in self:
            contract.ingreso_base_anual = (contract.wage * 12) + (contract.bonificacion * 12)

    @api.depends('wage')
    def _compute_exento(self):
        for contract in self:
            contract.b14_isr = contract.wage - 250
            contract.agui_isr = contract.wage - 250

    @api.depends('ingreso_base_anual', 'otros_ingresos','b14_isr','agui_isr',)
    def _compute_ingreso_total_anual(self):
        for contract in self:
            contract.ingreso_total_anual = (contract.ingreso_base_anual + contract.otros_ingresos + contract.b14_isr +
                                            contract.agui_isr)
    @api.depends('ingreso_base_anual')
    def _compute_deduction_iggs(self):
        # se calcula sobre lo anual pero sin bonificaicon
        for contract in self:
            contract.deducciones_iggs = (contract.wage * 12)*0.0483

    @api.depends('deducciones_sin_comprobantes','deducciones_iggs','b14_isr','b14_isr')
    def _compute_deductions_total_anual(self):
        for contract in self:
            contract.deducciones_total_anual = (contract.deducciones_sin_comprobantes + contract.deducciones_iggs
                                                + contract.b14_isr + contract.agui_isr)
    @api.depends('deducciones_sin_comprobantes', 'deducciones_iggs', 'b14_isr', 'b14_isr')
    def _compute_total_isr(self):

        for contract in self:
            ingresos_netos = contract.ingreso_total_anual - contract.deducciones_total_anual
            if ingresos_netos <= 0:
                contract.isr_total = 0
            else:
                contract.isr_total = ingresos_netos * 0.05 if ingresos_netos < 300000 \
                    else (
                        ((ingresos_netos - 300000)*0.07) + (300000*0.05))