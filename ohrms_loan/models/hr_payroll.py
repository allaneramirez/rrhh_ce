# -*- coding: utf-8 -*-
import time
import babel
from odoo import models, fields, api, tools, _
from datetime import datetime
from odoo.exceptions import ValidationError


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    loan_line_id = fields.Many2one('hr.loan.line', string="Loan Installment", help="Loan installment")


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def compute_sheet(self):
        """Update the computing sheet of a payslip by adding loan details
        to the 'Other Inputs' section."""
        for data in self:
            if (not data.employee_id) or (not data.date_from) or (
                    not data.date_to):
                return
            # Regla salarial con Codigo LO dentro de la estructura

            # Get Prestamo
            loans = self.env['hr.loan'].search([
                ('employee_id', '=', data.employee_id.id),
                ('state', '=', 'approve')
            ])
            loans_type = self.env['hr.loan.type'].search([])

            for loan_type in loans_type:
                data.input_line_ids.filtered(lambda inp: inp.code == loan_type.code).unlink()

            # Todos los prestamos
            if loans:
                # por cada prestamo
                for loan in loans:
                    loan_line = data.struct_id.rule_ids.filtered(
                        lambda x: x.code == loan.loan_type_id.code)

                    if loan_line:
                        for line in loan.loan_lines:
                            # if data.date_from <= line.date <= data.date_to:
                            # Si el pago no esta pagado
                            if not line.paid:
                                line.payslip_id = data.id
                                code = loan.loan_type_id.code
                                pay_id = data.id
                                amount = line.amount
                                name = loan_line.id
                                # Si es quincenal agregamos la entrada a cualquier estructura que tenga la regla LO
                                if loan.payment_frequency == 'quincenal':
                                    data.input_data_line(name, amount, line, pay_id,code)

                                elif loan.payment_frequency == 'mensual' and data.struct_id.prestamo_pago_mensual:
                                    data.input_data_line(name, amount, line,pay_id,code)
                                break

        return super(HrPayslip, self).compute_sheet()

    def input_data_line(self, name, amount, loan, pay_id, code):
        """Add loan details to payslip as other input"""
        input_type = self.env['hr.payslip.input.type.2'].search([
            ('code', '=', code)])
        input_vals = {
            'payslip_id': pay_id or self.id,
            'input_type_id': input_type.id,
            'amount': amount,
            'name': code,
            'code': code,
            'contract_id': self.contract_id[0].id,
            'loan_line_id': loan.id
        }
        self.env['hr.payslip.input'].create(input_vals)


    def action_payslip_done(self):
        for line in self.input_line_ids:
            if line.loan_line_id and line.loan_line_id.amount != 0:
                line.loan_line_id.paid = True
                line.loan_line_id.loan_id._compute_loan_amount()
        return super(HrPayslip, self).action_payslip_done()


    def action_payslip_draft(self):
        loan_lines = self.env['hr.loan.line'].search([
            ('payslip_id', 'in', self.ids),
            ('amount', '!=', 0.0)
        ])

        if loan_lines:
            loan_lines.write({'paid': False})
        return super(HrPayslip, self).action_payslip_draft()
