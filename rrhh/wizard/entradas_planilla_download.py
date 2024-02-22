# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
import base64
import xlsxwriter
import io

class rrhh_inputs_wizard(models.TransientModel):
    _name = 'rrhh.inputs.download.wizard'
    _description = 'Download payslip inputs Wizard '

    inputs_ids = fields.Many2many('hr.payslip.input.type.2', string='Seleccione las entradas')
    archivo = fields.Binary('Archivo')
    name = fields.Char('File Name', default='entradas_plantilla.xlsx', size=32)
    def download_template(self):
        for w in self:
            f = io.BytesIO()
            libro = xlsxwriter.Workbook(f)
            header_format = libro.add_format(
                {'font_size': 12, 'align': 'center', 'text_wrap': True, 'valign': 'center',
                 'bold': True, 'border': 1
                 })
            hoja = libro.add_worksheet("Entradas")
            hoja.set_column(0, 0, 45)

            hoja.write(0, 0, 'Empleado', header_format)
            i = 1
            # Agregando las entradas seleccionadas al encabezado
            for input in self.inputs_ids:
                hoja.write(0, i, input.code, header_format)
                i += 1

            active_batch_id = self.env.context.get('active_id')
            hr_payslip_run = self.env['hr.payslip.run'].search(
                [('id', '=', active_batch_id)])

            j = 1
            for pay in hr_payslip_run.slip_ids:
                hoja.write(j, 0, pay.employee_id.name)
                j += 1

            libro.close()
            datos = base64.b64encode(f.getvalue())
            self.write({'archivo': datos})
            return {
                'context': self.env.context,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'rrhh.inputs.download.wizard',
                'res_id': self.id,
                'view_id': False,
                'type': 'ir.actions.act_window',
                'target': 'new',
            }