# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from collections import defaultdict
from datetime import datetime
import base64
import xlsxwriter
from io import BytesIO


class rrhh_historial_salarios(models.TransientModel):
    _name = 'rrhh.historial_salarios_wizard'

    salario_promedio = fields.Selection([("6","6 Meses"),("12","12 Meses")],string="Salario Promedio Ultimos", required=True)
    name = fields.Char('Nombre archivo')
    archivo = fields.Binary('Archivo')

    def update(self):
        for w in self:
            ids = self.env.context.get('active_ids', [])

            contracts = self.env["hr.contract"].search([("state", "=", "open"),("employee_id","in",ids)])
            salary_months_by_department = defaultdict(lambda: {'empleados':{}})
            for contract in contracts:
                departamento = contract.employee_id.department_id.name
                ########## CALCULO DE DIAS LABORADOS PARA EL AGUINALDO
                """
                FORMULA: 365 DIAS -----> SALARIO PROMEDIO
                         DIAS LAB -----> X
                Sueldo ordinario mensual x días laborados ÷ 365 días.         
                """
                anio_actual = datetime.now().year
                anio_anterior = anio_actual - 1

                #FECHAS AGUINALDO 30 NOV AL 1 DE DIC
                fecha_aguinaldo_actual = datetime(anio_actual, 12, 1)
                fecha_aguinaldo_pasado = datetime(anio_anterior, 12, 1)

                #FECHAS BONO14 1 de JULIO AL 30 JUNIO
                fecha_bono14_actual = datetime(anio_actual, 7, 1)
                fecha_bono14_pasado = datetime(anio_anterior, 7, 1)
                anio_contrato = contract.date_start.year
                ###### DIAS AGUINALDO
                # SI EL INICIO DEL CONTRATO ES MENOR O IGUAL AL FECHA  DEL ANIO PASADO
                "QUIERE DECIR QUE EL EMPPLEADO HA TRABAJADO MAS DE UN AÑO EN LA EMPRESA POR LO TANTO LE CORRESPONDE 365/360 TOTAL LABORADOS"
                if contract.date_start <= fecha_aguinaldo_pasado.date():
                    dias = 365
                    contract.employee_id.write({'dias_laborados_aguinaldo': dias})
                # DE LO CONTRARIO LO PRORRATEAMOS
                elif contract.date_start > fecha_aguinaldo_pasado.date():
                    dias = (fecha_aguinaldo_actual.date() - contract.date_start).days
                    contract.employee_id.write({'dias_laborados_aguinaldo': dias})

                ##### DIAS BONO 14
                if contract.date_start <= fecha_bono14_pasado.date():
                    dias = 365
                    contract.employee_id.write({'dias_laborados_bono14': dias})
                elif contract.date_start > fecha_bono14_pasado.date():
                    dias = (fecha_bono14_actual.date() - contract.date_start).days
                    contract.employee_id.write({'dias_laborados_bono14': dias})

                ######################################################
                historial_salarios = self.env["rrhh.historial_salario"].search([("contrato_id", "=", contract.id)])
                historial_salarios.unlink()
                limit = 6
                if w.salario_promedio == '12':
                    # PARA ASFALGUA TRAEMOS LAS PLANILLAS POR MES YA QUE ES QUINCENAL
                    limit = 12
                slips = self.env["hr.payslip"].search([
                    "&",
                    ("contract_id", "=", contract.id),
                    ("state", "=", "done"),
                    ("struct_id.name", "like", "2da"),
                ], order='date_to ASC', limit=limit)
                total_salarios = 0
                contador_salarios = 0

                salarios_mensuales = []
                # SUMAMOS EL TOTAL DEL  EL MES (SEGURAMENTE HAY QUE DESCONTAR LO DEL INCENTIVO)
                for slip in slips:

                    #### CALCULAMOS PROMEDIO SEGUN LAS REGLAS DE COMPANIA
                    sal_prom = 0
                    for line in slip.line_ids:
                        if line.salary_rule_id.id in slip.company_id.salario_promedio_ids.ids:
                            sal_prom += line.total
                            if contract.employee_id.department_id.name == "ADMINISTRACION" and line.salary_rule_id.name == "Otros Ingresos V/A":
                                sal_prom -= line.total

                    self.env['rrhh.historial_salario'].create({
                        'salario': sal_prom,
                        'fecha': slip.date_from,
                        'contrato_id': contract.id,
                        'employee_id': contract.employee_id.id
                    })
                    total_salarios += slip.net_wage
                    contador_salarios += 1

                    mes = slip.date_to.strftime('%m')  # Ejemplo: '2024-12'
                    salarios_mensuales.append({mes: slip.net_wage})

                    # Calcular el promedio

                    # Calcula el promedio solo si hay salarios
                    promedio_salario = total_salarios / contador_salarios if contador_salarios > 0 else 0
                    contract.employee_id.write({'salario_promedio': promedio_salario})

                    # Agrupar los salarios por departamento y empleado
                    salary_months_by_department[departamento]["empleados"].setdefault(contract.employee_id.name, {
                        'salarios': [],
                        'fecha_ingreso': contract.date_start,
                        'codigo': contract.employee_id.codigo_empleado,
                        'dlab':contract.employee_id.dias_laborados_aguinaldo,
                        'dlabb14':contract.employee_id.dias_laborados_bono14
                    })
                    mes = slip.date_to.strftime('%m')  # Formato único para mes y año
                    salarios_empleado = \
                    salary_months_by_department[departamento]["empleados"][contract.employee_id.name]['salarios']

                    # Comprobar si ya existe un salario para este mes
                    if not any(salary['mes'] == f"Mes {mes}" for salary in salarios_empleado):
                        salarios_empleado.append({
                            "mes": f"Mes {mes}",
                            "salario": sal_prom
                        })

                        # Calcular el promedio
                print(salary_months_by_department,"david!!!")
                # Calcula el promedio solo si hay salarios
                promedio_salario = total_salarios / contador_salarios if contador_salarios > 0 else 0
                contract.employee_id.write({'salario_promedio': promedio_salario})





    ######################################             ARCHIOV EXCEL   ######################################
                ###################################### ARCHIVO EXCEL ######################################
                # Crear archivo Excel
                print(salary_months_by_department, "salary!!!")
                output = BytesIO()
                workbook = xlsxwriter.Workbook(output, {'in_memory': True})

                # Extraer los meses y años únicos
                all_months_years = set()
                for dept_data in salary_months_by_department.values():
                    for employee_data in dept_data["empleados"].values():
                        for salary in employee_data['salarios']:
                            all_months_years.add(salary["mes"])
                all_months_years = sorted(all_months_years)

                # Recorrer cada departamento y crear una hoja por departamento
                for department, dept_data in salary_months_by_department.items():
                    sheet = workbook.add_worksheet(department)  # Crear hoja por departamento

                    # Definir formatos
                    bold_format = workbook.add_format({'bold': True, 'align': 'center'})
                    headerformat = workbook.add_format({'bold': True})
                    currency_format = workbook.add_format({'num_format': '#,##0.00', 'align': 'center'})

                    # Escribir encabezados generales
                    sheet.write(0, 2, "ABSORBENTES, S.A.", headerformat)
                    sheet.write(1, 2, "Historial de Salario para el cálculo de prestaciones", headerformat)
                    sheet.write(2, 2, f"{department} {anio_actual}", headerformat)
                    sheet.set_column(5, 2, 25)
                    sheet.set_column(5, 3, 25)
                    sheet.set_column(5, 4, 25)
                    # Escribir los encabezados de las columnas
                    sheet.write(5, 2, "NO.", bold_format)
                    sheet.write(5, 3, "Codigo de Empleado", bold_format)
                    sheet.write(5, 4, "Nombre del Empleado", bold_format)
                    sheet.write(5, 5, "Fecha de Ingreso", bold_format)

                    # Escribir los encabezados de los meses
                    j=6
                    for col_index, month in enumerate(all_months_years, start=6):
                        sheet.write(5, col_index, f"{month}", bold_format)
                        j += 1

                    sheet.write(5, j , "Salario Promedio", bold_format)
                    sheet.write(5, j+1 , "Dias Laborados Aguinaldo", bold_format)
                    sheet.write(5, j+2 , "Dias Laborados Bono 14", bold_format)
                    # Escribir los datos de los empleados
                    row = 6  # Iniciar fila de empleados
                    i = 1  # Contador de empleados
                    for employee, data in dept_data["empleados"].items():
                        # Escribir los datos generales del empleado
                        sheet.write(row, 2, i)  # Número del empleado
                        sheet.write(row, 3, data['codigo'])  # Código del empleado
                        sheet.write(row, 4, employee)  # Nombre del empleado
                        sheet.write(row, 5, data['fecha_ingreso'].strftime('%Y-%m-%d'))  # Fecha de ingreso

                        col_index = 6  # Comenzar en la columna 6 para los salarios


                        salario = 0
                        cantidad = 0

                        # Iterar por cada mes/año en el conjunto completo
                        for month in all_months_years:
                            # Buscar si existe un salario para este mes
                            salario_mes = next((sal["salario"] for sal in data["salarios"] if sal["mes"] == month), 0)
                            sheet.write(row, col_index, salario_mes, currency_format)
                            col_index += 1
                            salario += salario_mes
                            cantidad += 1 if salario_mes > 0 else 0

                        # Escribir el salario promedio calculado
                        promedio_salario = round(float(salario / cantidad), 2) if cantidad > 0 else 0
                        sheet.write(row, col_index, promedio_salario, currency_format)
                        sheet.write(row, col_index + 1, data['dlab'])
                        sheet.write(row, col_index + 2, data['dlabb14'])

                        row += 1  # Avanzar a la siguiente fila
                        i += 1  # Incrementar el contador de empleados

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
