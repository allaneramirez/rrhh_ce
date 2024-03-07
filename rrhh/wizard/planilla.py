# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import time
import base64
import xlsxwriter
import io
import logging


class rrhh_planilla_wizard(models.TransientModel):
    _name = 'rrhh.planilla.wizard'
    _description = 'Wizard de planilla'

    nomina_id = fields.Many2one('hr.payslip.run', 'Nomina',
                                default=lambda self: self.env['hr.payslip.run'].browse(self._context.get('active_id')),
                                required=True)
    planilla_id = fields.Many2one('rrhh.planilla', 'Planilla', required=True)
    archivo = fields.Binary('Archivo')
    name = fields.Char('File Name', default='planilla.xlsx', size=32)
    agrupado = fields.Boolean('Agrupado por cuenta analítica')

    def generar(self):
        for w in self:
            f = io.BytesIO()
            libro = xlsxwriter.Workbook(f)

            header_format = libro.add_format(
                {'font_size': 12, 'align': 'center', 'text_wrap': True, 'valign': 'center',
                 'bold': True, 'border': 1
                 })
            header_format_total = libro.add_format(
                {'font_size': 12, 'align': 'center', 'text_wrap': True, 'valign': 'center',
                 'bold': True, 'top': 2
                 })
            title_format = libro.add_format({
                'bold': True,
                'font_size': 16,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#D3D3D3',
                'color': '#36454F',
            })

            title_format2 = libro.add_format({
                'bold': True,
                'font_size': 16,
                'align': 'center',
                'valign': 'vcenter',
                'color': '#36454F'

            })
            formato_fecha = libro.add_format({'num_format': 'dd/mm/yy'})
            total_formato = libro.add_format({'top': 2})
            fecha_inicio = w.nomina_id.date_start.strftime('%d/%m/%Y')

            fecha_fin = w.nomina_id.date_end.strftime('%d/%m/%Y')

            hoja = libro.add_worksheet(str(w.nomina_id.name))
            hoja.merge_range('B2:G2', w.nomina_id.company_id.name, title_format)
            hoja.merge_range('B3:G3', f'Planilla: {w.nomina_id.name} del {fecha_inicio} al '
                                      f'{fecha_fin} ', title_format)
            linea = 4
            # Ancho de columnas y filas
            j = 1
            while j < len(w.planilla_id.columna_id) + 4:
                hoja.set_column(0, j, 15)
                j += 1
            departamentos_empleados = set()
            final_cuentas_dict = {}
            employees = self.env['hr.employee'].search([])

            for e in employees:
                departamento = e.department_id.name
                if departamento:
                    departamentos_empleados.add(departamento)
                for depa in departamentos_empleados:
                    if depa not in final_cuentas_dict:
                        final_cuentas_dict[depa] = []

            # Por cada nomina del lote
            for l in w.nomina_id.slip_ids:
                cuentas_dict = {}
                departamento = l.employee_id.department_id.name
                # Agregamos las cuentas unicas a las cuentas_dict
                cuentas_dict[departamento] = [{'Liquido a recibir': 0}]

                columnas = {}
                dict_fields = {"Cod. de Empleado": l.employee_id.codigo_empleado,
                               "Empleado": l.employee_id.name,
                               "Puesto": l.employee_id.job_id.name,
                               "Fecha de ingreso": l.contract_id.date_start}
                # Almacenamos las primeras columnas
                index = 1
                for k, v in dict_fields.items():
                    columnas[k] = index
                    index += 1

                columna = 5
                for c in w.planilla_id.columna_id:
                    # agregamos el index a la columna para luego saber en que columnas desplegarlo
                    columnas[c.name] = columna
                    # Por cada columna de la planilla configurada, traemos las reglas o entradas asociadas a la c
                    reglas = [x.name for x in c.regla_id]
                    entradas = [x.code for x in c.entrada_id]
                    columna += 1
                    if len(reglas) != 0:
                        ############# Reglas Salariales #############
                        for r in l.line_ids:
                            # Verificar que cuenta_nombre no sea 'False' antes de acceder al diccionario
                            if r.salary_rule_id.name in reglas:

                                cuentas_dict[departamento][0][c.name] = r.total
                                if c.sumar:
                                    cuentas_dict[departamento][0]['Liquido a recibir'] += r.total
                                # # También, verifica si la sucursal no es 'False' antes de intentar acceder a la clave 'Sueldo Base' para agregar sueldo base
                                if 'Sueldo Base' not in cuentas_dict.get(str(departamento), [])[0]:
                                    cuentas_dict[departamento][0]['Sueldo Base'] = l.contract_id.wage

                            ######## Entradas ############
                    elif len(entradas) !=0:
                        for r in l.input_line_ids:
                            print(r.code,"codeeeee")
                            if r.code in entradas:
                                cuentas_dict[departamento][0][str(c.name)] = r.amount

                    for campo, texto in dict_fields.items():
                        if campo not in cuentas_dict[departamento][0]:
                            cuentas_dict[departamento][0][campo] = texto

                for k, value in cuentas_dict.items():
                    final_cuentas_dict[k].extend(value)

                columnas['Liquido a recibir'] = columna
            # fuera de la planilla
        totales_acumulados = {columna: 0 for columna in columnas}
        # print(totales_acumulados,"totales")
        for cuenta_analitica, lineas in final_cuentas_dict.items():
            if lineas:
                # Escribir el nombre de la cuenta analítica resaltado
                hoja.write(linea, 1, cuenta_analitica, title_format2)
                linea += 1

                # Escribir encabezados de columnas
                hoja.write(linea, 1, 'Cod. de empleado', header_format)
                hoja.write(linea, 2, 'Empleado', header_format)
                hoja.write(linea, 3, 'Puesto', header_format)
                hoja.write(linea, 4, 'Fecha de ingreso', header_format)

                for columna_name, columna_index in columnas.items():
                    hoja.write(linea, columna_index, columna_name, header_format)
                    hoja.set_column(linea, columna_index, 20)
                hoja.set_row(linea, 30)

                linea += 1

            # Iterar sobre las líneas y escribir datos
            for linea_datos in filter(None, lineas):
                if linea_datos.get('Empleado'):
                    # Iterar sobre columnas y escribir datos

                    for columna_name, columna_index in columnas.items():
                        valor = linea_datos.get(columna_name, 0)
                        if columna_name == "Fecha de ingreso":
                            hoja.write(linea, columna_index, valor, formato_fecha)
                        else:
                            if columna_name != "Cod. de Empleado" and columna_name != "Empleado" and columna_name != "Puesto" and valor:
                                hoja.write(linea, columna_index, float(valor))
                            else:
                                hoja.write(linea, columna_index, valor)
                    linea += 1

            for columna_name, columna_index in columnas.items():
                if columna_name != "Cod. de Empleado" and columna_name != "Empleado" and columna_name != "Puesto" and columna_name != "Fecha de ingreso" and len(lineas) != 0:
                    suma_columna = sum(
                        linea_datos.get(columna_name, 0) if 'Empleado' in linea_datos else 0 for linea_datos in
                        filter(None, lineas))
                    hoja.write(linea, columna_index, suma_columna, total_formato)
                    totales_acumulados[columna_name] += suma_columna

            linea += 1

        hoja.merge_range(linea + 3, 1, linea + 3, 4, 'Total', header_format_total)
        for columna_name, columna_index in columnas.items():
            if columna_name != "Cod. de Empleado" and columna_name != "Empleado" and columna_name != "Puesto" and columna_name != "Fecha de ingreso":
                hoja.write(linea + 3, columna_index, totales_acumulados[columna_name], total_formato)
        linea += 1

        libro.close()
        datos = base64.b64encode(f.getvalue())
        self.write({'archivo': datos})
        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'rrhh.planilla.wizard',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
