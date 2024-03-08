from odoo import models

class VacationXls(models.AbstractModel):
    _name = "report.rrhh.vacation_report_control"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, lines):
        # Importar el modelo de los tipos de ausencias
        leaves_type = self.env['hr.leave.type'].search([('name','ilike','vacaciones')])

        # Agregar hoja de trabajo
        worksheet = workbook.add_worksheet('Reporte Vacaciones')

        # Definir el encabezado
        header_format_main_1 = workbook.add_format({'bold': True, 'align': 'center','bg_color': '#d3d0f5'})
        header_format_main_2 = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#f5e3d0'})
        header_format = workbook.add_format({'bold': True, 'align': 'center'})
        formato_fecha = workbook.add_format({'num_format': 'dd/mm/yy'})
        i = 3
        c = 0
        # # Escribiendo encabezado
        worksheet.write(i, 0, 'Empleado', header_format)
        worksheet.write(i, 1, 'Fecha de Ingreso', header_format)
        worksheet.set_column(0,0, 30)
        worksheet.set_column(1, 1, 18)
        c = c+2
        alternate_format = False
        leaves_name = {}
        for leave in leaves_type:

            if alternate_format:
                header_format_current = header_format_main_2
            else:
                header_format_current = header_format_main_1
            worksheet.merge_range(i-1, c,i-1,c+2, leave.name, header_format_current)
            leaves_name[leave.name] = c
            worksheet.write(i, c, 'Dias Asignados', header_format)
            worksheet.set_column(c, c, 15)
            c+=1
            worksheet.write(i, c, 'Dias Gozados', header_format)
            worksheet.set_column(c, c, 15)
            c+=1
            worksheet.write(i, c, 'Dias Pendientes', header_format)
            worksheet.set_column(c, c, 15)
            c += 1
            alternate_format = not alternate_format
        i += 1
        for employee in lines:
            worksheet.write(i, 0, employee.name)
            worksheet.write(i, 1, employee.contract_id.date_start,formato_fecha)

            allocations = self.env['hr.leave.allocation'].search([('employee_id','=',employee.id)])
            for a in allocations:
                c = leaves_name.get(a.holiday_status_id.name)
                if c is not None:
                    # Dias ASIGNADOS
                    asign = a.number_of_days_display
                    worksheet.write(i, c, asign)
                    leaves = self.env['hr.leave'].search([('employee_id','=',employee.id),
                                                          ('holiday_status_id','=',a.holiday_status_id.id),
                                                          ('state','=','validate')])
                    total_taken = 0
                    for l in leaves:
                        total_taken += l.number_of_days
                    # DIAS GOZADOS
                    worksheet.write(i, c+1, total_taken)
                    # DIAS PENDIENTES
                    diff = asign - total_taken
                    worksheet.write(i, c + 2, diff)
                else:
                    raise ValueError("El nombre del tipo de ausencia '{}' de la asignacion, no está en las ausencias de vacaciones".format(
                        a.holiday_status_id.name))
            i += 1




