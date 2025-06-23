# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from collections import defaultdict
from datetime import datetime
import base64
import xlsxwriter
from io import BytesIO
from odoo.exceptions import ValidationError


class rrhh_historial_salarios(models.TransientModel):
    _name = 'rrhh.historial_salarios_wizard'

    salario_promedio = fields.Selection([("6","6 Meses"),("12","12 Meses")],string="Salario Promedio Ultimos", required=True, default="12")
    name = fields.Char('Nombre archivo')
    archivo = fields.Binary('Archivo')

    def update(self):
        for w in self:
            ids = self.env.context.get('active_ids', [])

            contracts = self.env["hr.contract"].search([("state", "=", "open"),("employee_id","in",ids)])
            salary_months_by_department = defaultdict(lambda: defaultdict(lambda: {'empleados': {}}))
            anio_actual = datetime.now().year
            anio_anterior = anio_actual - 1

            # FECHAS AGUINALDO 30 NOV AL 1 DE DIC
            fecha_aguinaldo_actual = datetime(anio_actual, 11, 30)
            fecha_aguinaldo_pasado = datetime(anio_anterior, 12, 1)

            # FECHAS BONO14 1 de JULIO AL 30 JUNIO
            fecha_bono14_actual = datetime(anio_actual, 7, 1)
            fecha_bono14_pasado = datetime(anio_anterior, 6, 1)
            for contract in contracts:
                departamento = contract.employee_id.department_id.name



                ######## CALCULO PARA EL EXCEL DE LIBNY

                for fecha_prestacion in [fecha_aguinaldo_actual, fecha_bono14_actual]:
                    tipo_prestacion = 'AGUINALDO' if fecha_prestacion == fecha_aguinaldo_actual else 'BONO 14'
                    if tipo_prestacion == "AGUINALDO":
                        fecha_inicial = fecha_aguinaldo_pasado
                    else:
                        fecha_inicial = fecha_bono14_pasado

                    slips = self.env["hr.payslip"].search([
                        "&",
                        ("contract_id", "=", contract.id),
                        ("state", "=", "done"),
                        ("struct_id.name", "like", "2da"),
                        ("date_from", ">=",fecha_inicial),
                        ("date_to", "<=",fecha_prestacion),
                        ("net_wage","!=", 0)
                    ], order='date_to DESC', limit=12)
                    # para segurarmos que el slip pertence al anio correcto
                    slips_filtrados = []
                    for slip in slips:
                        mes = int(slip.date_to.strftime('%m'))
                        anio = int(slip.date_to.strftime('%Y'))

                        if tipo_prestacion == "BONO 14":
                            if (mes >= 7 and anio == anio_anterior) or (mes <= 6 and anio == anio_actual):
                                slips_filtrados.append(slip)
                        else:  # AGUINALDO
                            if (mes == 12 and anio == anio_anterior) or (mes <= 11 and anio == anio_actual):
                                slips_filtrados.append(slip)
                    # fin filtro

                    total_salarios = 0
                    salarios_empleado  = []
                    total_dias = 0

                    # SUMAMOS EL TOTAL DEL  EL MES (SEGURAMENTE HAY QUE DESCONTAR LO DEL INCENTIVO)
                    for slip in slips_filtrados:
                        #### CALCULAMOS PROMEDIO SEGUN LAS REGLAS DE COMPANIA
                        sal_base = 0

                        for line in slip.line_ids:
                            if line.salary_rule_id.id in slip.company_id.salario_promedio_ids.ids:
                                sal_base += line.total
                        dias_lab = sum(
                            input.amount for input in slip.input_line_ids
                            if input.code == 'DL'
                        )

                        total_salarios += sal_base
                        total_dias += dias_lab

                        mes = slip.date_to.strftime('%m')  # Formato único para mes y año
                        if not any(mes in salario for salario in salarios_empleado):
                            salarios_empleado.append({mes:sal_base})

                        # Ahora que terminamos todos los slips, calculamos los valores agregados
                    promedio_salario = total_salarios / len(slips) if slips else 0
                    dlab = (total_dias * 30) / 360
                    salary_months_by_department[tipo_prestacion][departamento]["empleados"].setdefault(
                        contract.employee_id.name,
                        {
                            'salarios': salarios_empleado,
                            'fecha_ingreso': contract.date_start,
                            'codigo': contract.employee_id.codigo_empleado,
                            'total_devengado': total_salarios,
                            'sal_promedio': promedio_salario/30,
                            'dlab': dlab,
                            "total_prestacion": dlab*promedio_salario
                        }
                    )
    ######################################             ARCHIOV EXCEL   ######################################
                # Crear archivo Excel
            output = BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})

                # Extraer los meses y años únicos
                # Recorrer cada departamento y crear una hoja por departamento

            for tipo_prestacion, departamentos in salary_months_by_department.items():
                if tipo_prestacion == "AGUINALDO":
                    meses = ["12", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11"]
                else:
                    meses = ["07", "08", "09", "10", "11", "12", "01", "02", "03", "04", "05", "06"]

                sheet = workbook.add_worksheet(tipo_prestacion)  # Crear hoja por departamento

                # Definir formatos
                bold_format = workbook.add_format({'bold': True, 'align': 'center','valign': 'vcenter','top': 1, 'bottom': 1})
                bold_format_leftalign = workbook.add_format({'bold': True, 'align': 'left'})
                headerformat = workbook.add_format({'bold': True, })
                currency_format = workbook.add_format({'num_format': '#,##0.00', })

                # Escribir encabezados generales
                sheet.write(0, 1, "ABSORBENTES, S.A.", headerformat)
                if tipo_prestacion == "AGUINALDO":
                    sheet.write(1, 1, f"COMPRENDIDA DE DICIEMBRE {anio_anterior} A NOVIEMBRE {anio_actual}", headerformat)
                else:
                    sheet.write(1, 1, f"COMPRENDIDA DE JUlIO {anio_anterior} A JUNIO {anio_actual}", headerformat)

                sheet.set_column(0, 0, 5)
                sheet.set_column(1, 1, 20)
                sheet.set_column(2, 2, 35)
                sheet.set_column(3, 3, 20)
                sheet.set_row(3, 30)
                # ENCABEZADOS
                sheet.write(3, 0, "NO.", bold_format)
                sheet.write(3, 1, "CODIGO", bold_format)
                sheet.write(3, 2, "NOMBRE DEL EMPLEADO", bold_format)
                sheet.write(3, 3, "FECHA DE INGRESO", bold_format)

                # ENCAVBEZADOS MESES
                j=4
                for col_index, month in enumerate(meses, start=4):
                    sheet.write(3, col_index, f"{month}", bold_format)
                    j += 1
                sheet.set_column( j,j+3, 20)

                sheet.write(3, j , "TOTAL DEVENGADO", bold_format)
                sheet.write(3, j+1 , "S/DIARIO PROEMDIO", bold_format)
                sheet.write(3, j+2 , "DIAS A PAGAR", bold_format)
                sheet.write(3, j+3 , tipo_prestacion, bold_format)

                row = 4
                  # Contador de empleados
                for depa, data in departamentos.items():
                    sheet.merge_range(row,0, row,3, depa.capitalize(), bold_format_leftalign)
                    # DATIS EMPLEADOS
                    i = 1
                    for empleado, data in data["empleados"].items():
                        row += 1
                        sheet.write(row, 0, i)  # Número del empleado
                        sheet.write(row, 1, data['codigo'])  # Código del empleado
                        sheet.write(row, 2, empleado)  # Nombre del empleado
                        sheet.write(row, 3, data['fecha_ingreso'].strftime('%d/%m/%Y'))  # Fecha de ingreso
                        # SALARIOS
                        col = 4  # Comienza en la columna después de Fecha de Ingreso
                        for mes in meses:
                            salario_mes = next((s[mes] for s in data['salarios'] if mes in s), "-")
                            sheet.write(row, col, salario_mes,currency_format)
                            col += 1
                        sheet.write(row, col, data["total_devengado"],currency_format)  # Número del empleado
                        sheet.write(row, col+1, data['sal_promedio'],currency_format)  # Código del empleado
                        sheet.write(row, col+2, round(data["dlab"],2),)  # Nombre del empleado
                        sheet.write(row, col+3, data['total_prestacion'],currency_format)  # Fecha de ingreso
                        # SALARIOS

                        i += 1
                    row += 1



            # Guardar el archivo Excel
            workbook.close()
            output.seek(0)

            # Convertir a base64 y asignar el archivo al modelo
            self.write({
                'archivo': base64.b64encode(output.read()),
                'name': 'Historial_Salarios.xlsx',
            })
            output.close()

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'rrhh.historial_salarios_wizard',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
