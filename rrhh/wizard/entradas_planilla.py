# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
import xlrd
import base64
from odoo.exceptions import ValidationError

class rrhh_inputs_wizard(models.TransientModel):
    _name = 'rrhh.inputs.wizard'
    _description = 'payslip inputs Wizard '

    files = fields.Binary(string="Importar Archivo Excel", required = True)

    def create_inputs(self):
        active_batch_id = self.env.context.get('active_id')

        print(active_batch_id,"barch")
        # Read the Excel file
        try:
            workbook = xlrd.open_workbook(file_contents=base64.b64decode(self.files))
        except:
            raise ValidationError("Por favor selecciona un archivo .xls/xlsx ...")
        Sheet_name = workbook.sheet_names()
        sheet = workbook.sheet_by_name(Sheet_name[0])

        # Iterate over each row in the Excel file and create hr.payslip.input records
        for row_index in range(1, sheet.nrows):  # Assuming the first row contains headers
            employee_name = sheet.cell_value(row_index, 0)
            entry_name = sheet.cell_value(row_index, 1)
            amount = sheet.cell_value(row_index, 2)
            hr_payslip_input_type = self.env['hr.payslip.input.type.2'].search([('code','=',sheet.cell(row_index, 1).value)])

            if not employee_name:
                raise ValidationError(_(
                    "Empleado no encontrado: %s" % (sheet.cell(row_index, 0).value)
                ))

            if not hr_payslip_input_type:
                raise ValidationError(_(
                    "Nombre no encontrado para %s" % (sheet.cell(row_index, 1).value)
                ))

            # if not amount:
            #     raise ValidationError(_(
            #         "Amount value is require %s" % (sheet.cell(row_index, 2).value)
            #     ))

            # Find the payslip for the employee (customize this query based on your actual model structure)
            payslip = self.env['hr.payslip'].search(
                [('employee_id.name', '=', employee_name), ('payslip_run_id', '=', active_batch_id)], limit=1)
            print(payslip.contract_id,"contract!!")
            if payslip:
                # Create hr.payslip.input record
                input_vals = {
                    'payslip_id': payslip.id,
                    'input_type_id': hr_payslip_input_type.id,
                    'amount': amount,
                    'name': entry_name,
                    'code': hr_payslip_input_type.code,
                    'contract_id': payslip.contract_id[0].id
                }
                self.env['hr.payslip.input'].create(input_vals)
        return {'type': 'ir.actions.act_window_close'}

