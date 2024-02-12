# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.release import version_info
import logging
import datetime
import time
import dateutil.parser
from dateutil.relativedelta import relativedelta
from dateutil import relativedelta as rdelta
from calendar import monthrange
from odoo.fields import Date, Datetime
from odoo.addons.l10n_gt_extra import a_letras
from odoo.exceptions import ValidationError
class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    etiqueta_empleado_ids = fields.Many2many('hr.employee.category', string='Etiqueta empleado',
                                             related='employee_id.category_ids')
    cuenta_analitica_id = fields.Many2one('account.analytic.account', 'Cuenta analítica')
    net_wage = fields.Float(compute='_compute_basic_net', store=True)

    @api.depends('line_ids.total')
    def _compute_basic_net(self):

        for payslip in self:
            for line in payslip.line_ids:
                if line.salary_rule_id.code == "NET":
                    self.net_wage = line.total

    def diasTrabajados12Meses(self, empleado_id):
        structure = self.env['hr.payroll.structure'].search([('name', '=', 'Estructura Base')])
        slips = self.env['hr.payslip'].search(
            ['&', ('employee_id', '=', empleado_id.id), ('state', '=', 'done'), ('struct_id', '=', structure.id)],
            order='date_to DESC',
            limit=12
        )
        days = 0
        for slip in slips:
            worked_day = self.env["hr.payslip.worked_days"].search(
                ['&', ("payslip_id", "=", slip.id), ('name', '=', 'Trabajo 100')])
            days += worked_day.number_of_days
        return days

    def diasTrabajados6Meses(self, empleado_id):
        structure = self.env['hr.payroll.structure'].search([('name', '=', 'Estructura Base')])
        slips = self.env['hr.payslip'].search(
            ['&', ('employee_id', '=', empleado_id.id), ('state', '=', 'done'), ('struct_id', '=', structure.id)],
            order='date_to DESC',
            limit=6
        )
        days = 0
        for slip in slips:
            worked_day = self.env["hr.payslip.worked_days"].search(
                ['&', ("payslip_id", "=", slip.id), ('name', '=', 'Trabajo 100')])
            days += worked_day.number_of_days
        return days


    def load_salaries(self):
        contracts = self.env["hr.contract"].search([("state", "=", "open")])
        for contract in contracts:
            historial_salarios = self.env["rrhh.historial_salario"].search([("contrato_id", "=", contract.id)])
            historial_salarios.unlink()
            slips = self.env["hr.payslip"].search(["&", ("contract_id", "=", contract.id), ("state", "=", "done")],
                                                  order='date_to DESC',
                                                  limit=6)
            for slip in slips:
                slips_line = self.env["hr.payslip.line"].search([("slip_id", "=", slip.id)])
                total = 0
                # POR CADA LINEA DE LA NOMINA
                for line in slips_line:
                    salary_rule = line.salary_rule_id
                    # if salary_rule and salary_rule.sumar_prestaciones:
                    total += line.total

                self.env['rrhh.historial_salario'].create({
                    'salario': total,
                    'fecha': slip.date_to,
                    'contrato_id': contract.id,
                })

    def promedio_salarios_12_meses(self, employee_id):
        contract = self.env["hr.contract"].search([("state", "=", "open"), ('employee_id', '=', employee_id.id)],
                                                  limit=1)
        structure_id = contract.structure_type_id
        slips = self.env["hr.payslip"].search(["&", ("contract_id", "=", contract.id), ("state", "=", "done")],
                                              order='date_to DESC',
                                              limit=12)
        total = 0
        for slip in slips:
            slips_line = self.env["hr.payslip.line"].search([("slip_id", "=", slip.id)])
            for line in slips_line:
                salary_rule = line.salary_rule_id
                if salary_rule and salary_rule.sumar_prestaciones:
                    total += line.total

        return total / len(slips) if len(slips) > 0 and total else 0

    def promedio_salarios_6_meses(self, employee_id):
        contract = self.env["hr.contract"].search([("state", "=", "open"), ('employee_id', '=', employee_id.id)],
                                                  limit=1)
        structure_id = contract.structure_type_id
        slips = self.env["hr.payslip"].search(["&", ("contract_id", "=", contract.id), ("state", "=", "done")],
                                              order='date_to DESC',
                                              limit=6)
        total = 0
        for slip in slips:
            slips_line = self.env["hr.payslip.line"].search([("slip_id", "=", slip.id)])
            for line in slips_line:
                salary_rule = line.salary_rule_id
                if salary_rule and salary_rule.sumar_prestaciones:
                    total += line.total

        return total / len(slips) if len(slips) > 0 and total else 0

    def diasLaboradosPrestaciones(self, contract_id, slip_id):

        dias_laborados = slip_id.date_to - contract_id.date_start
        if int(dias_laborados.days) >= 365:
            return 365
        else:
            return dias_laborados.days

    def diasLaboradosInd(self, contract_id, slip_id):
        dias_laborados = slip_id.date_to - contract_id.date_start
        return dias_laborados.days

    def diasLaboradosVac(self, contract_id, slip_id):
        year_actual = datetime.datetime.now().year
        year_pasado = year_actual - 1
        fecha_inicio_actual = datetime.datetime(year_actual, contract_id.date_start.month, contract_id.date_start.day)
        if slip_id.date_to > fecha_inicio_actual:
            dias_laborados = slip_id.date_to - fecha_inicio_actual
            return dias_laborados.days
        else:
            fecha_inicio_año_pasado = datetime.datetime(year_pasado, contract_id.date_start.month, contract_id.date_start.day)
            dias_laborados = slip_id.date_to - fecha_inicio_año_pasado
            return dias_laborados.days

    def quin_descount(self, employee_id, payslip):
        employee = self.env['hr.employee'].browse(employee_id)
        payslip_obj = self.env['hr.payslip']
        print(payslip)

        # # Busca la nómina de la 1era Quincena del mes de la nomina de la 2Q
        previous_payslip = payslip_obj.search([
            ('employee_id', '=', employee[0].id),
            ('struct_id.name', '=', '1era Quincena'),
            ('date_to', 'like', payslip.strftime('%Y-%m')),
            ('state','in',['done','paid'])
        ], limit=1)
        print(previous_payslip,"previus!~~")
        if previous_payslip:
            result = previous_payslip[0].net_wage
        else:
            result = 0
        return result


    def diasLaboradosAgui(self, contract_id, slip_id):
        year_actual = datetime.datetime.now().year
        year_pasado = year_actual - 1
        fecha_aguinaldo_actual = datetime.datetime(year_actual, 12, 1)
        if slip_id.date_to > fecha_aguinaldo_actual:
            dias_laborados = slip_id.date_to - fecha_aguinaldo_actual
            return dias_laborados.days
        else:
            fecha_inicio_año_pasado = datetime.datetime(year_pasado, 12, 1)
            dias_laborados = slip_id.date_to - fecha_inicio_año_pasado
            return dias_laborados.days

    def diasLaboradosB14(self, contract_id, slip_id):
        year_actual = datetime.datetime.now().year
        year_pasado = year_actual - 1
        fecha_B14_actual = datetime.datetime(year_actual, 7, 1)
        if slip_id.date_to > fecha_B14_actual:
            dias_laborados = slip_id.date_to - fecha_B14_actual
            return dias_laborados.days
        else:
            fecha_inicio_año_pasado = datetime.datetime(year_pasado, 7, 1)
            dias_laborados = slip_id.date_to - fecha_inicio_año_pasado
            return dias_laborados.days
    def calculo_total(self,id):
        payslip = self.env['hr.payslip'].search([('id', '=', id)])
        paylip_lines = payslip.line_ids
        for line in paylip_lines:
            if line.salary_rule_id.general:
                sequence = line.salary_rule_id.sequence
                result = 0
                for l in paylip_lines:
                    if l.salary_rule_id.sequence == sequence-1:
                        result += l.total
                return result
                ###### DIAS LABORADOS #####
            if line.salary_rule_id.code == 'TDL':
                total_input = 0
                for input in payslip.input_line_ids:
                    if input.code.startswith("DL"):
                        total_input += input.amount
                return total_input

    def _get_worked_day_lines(self):
        # regresa una lista de dicionarios que contienen los dias trabajados que deberia aplicarse la nomina dada
        res = super(HrPayslip, self)._get_worked_day_lines()


        ###################### Actualizar Vacaciones para version 14 pendiente ###################
        # iteramos sobre cada nomina
        # current_year = datetime.datetime.now().year
        # for r in res:
        #     work_entry_id = r['work_entry_type_id']
        #
        #     entry = self.env['hr.work.entry.type'].search([('id', '=', work_entry_id)])
        #     if entry.code == 'LEAVE120':
        #         # Si el tipo de entrada tiene color amarillo
        #         leave_type = self.env['hr.leave.type'].search([('color', '=', 3)])
        #         vaction_days = self.env['hr.leave'].search([('employee_id', '=', self.employee_id[0].id),
        #                                                     ('holiday_status_id','=',leave_type[0].id),
        #                                                     ('request_date_from','ilike', str(current_year)),
        #                                                     ('state','=','validate')],limit=1)
        #
        #         total_vacaciones = vaction_days.number_of_days_display
        #         r['number_of_days'] = total_vacaciones

        return res


    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(models.Model, self).fields_view_get(view_id, view_type, toolbar, submenu)
        return res

    @api.model
    def get_views(self, views, options=None):
        res = super(models.Model, self).get_views(views, options)
        return res


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'


    tipo_nomina = fields.Selection([
        ('nomina_base', 'Nomina Base'),
        ('bono_14', 'Bono 14'),
        ('aguinaldo', 'Aguinaldo'),
        ('finiquito', 'Finiquito'),
        ('vacaciones', 'Vacaciones'),
    ], string='Tipo de Préstamo', default='nomina_base')
    recibo_id = fields.Many2one('rrhh.recibo', 'Formato de recibo', groups="hr.group_hr_user")

