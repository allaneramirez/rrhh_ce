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

        hr_payslip_run = self.env['hr.payslip.run'].search(
            [('id', '=', active_batch_id)])
        # Read the Excel file
        try:
            workbook = xlrd.open_workbook(file_contents=base64.b64decode(self.files))
        except:
            raise ValidationError("Por favor selecciona un archivo .xls/xlsx ...")
        Sheet_name = workbook.sheet_names()
        sheet = workbook.sheet_by_name(Sheet_name[0])

        # Eliminando previos inputs
        for pay in hr_payslip_run.slip_ids:
            pay.input_line_ids.unlink()
        # Iterate over each row in the Excel file and create hr.payslip.input records
        for row_index in range(1, sheet.nrows):  # Assuming the first row contains headers
            for col_index in range(1, sheet.ncols):
                employee_name = sheet.cell_value(row_index, 0)
                entry_code = sheet.cell_value(0, col_index)
                amount = sheet.cell_value(row_index, col_index)

                hr_payslip_input_type = self.env['hr.payslip.input.type.2'].search([('code','=',entry_code)])
                employee = self.env['hr.employee'].search([('name','=',employee_name)])

                if not hr_payslip_input_type:
                    raise ValidationError(_(
                        "Codigo de entrada no encontrado: %s" % (sheet.cell(0, col_index).value)
                    ))

                if not employee:
                    raise ValidationError(_(
                        "Empleado no encontrado: %s" % (sheet.cell(row_index, 0).value)
                    ))


                # Find the payslip for the employee (customize this query based on your actual model structure)
                payslip = self.env['hr.payslip'].search(
                    [('employee_id.name', '=', employee_name), ('payslip_run_id', '=', active_batch_id)], limit=1)

                if payslip:
                    # Create hr.payslip.input record
                    input_vals = {
                        'payslip_id': payslip.id,
                        'input_type_id': hr_payslip_input_type.id,
                        'amount': amount,
                        'name': entry_code,
                        'code': entry_code,
                        'contract_id': payslip.contract_id[0].id
                    }
                    self.env['hr.payslip.input'].create(input_vals)
        return {'type': 'ir.actions.act_window_close'}

