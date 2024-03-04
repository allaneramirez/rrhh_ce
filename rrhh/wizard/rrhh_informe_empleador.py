# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import xlsxwriter
import base64
import io
import logging
import time
import datetime
from datetime import date
from datetime import datetime, date, time
from odoo.fields import Date, Datetime
import itertools
from dateutil.relativedelta import relativedelta
from odoo.addons.l10n_gt_extra import a_letras


class rrhh_informe_empleador(models.TransientModel):
    _name = 'rrhh.informe_empleador'

    anio = fields.Integer('Año', required=True)
    name = fields.Char('Nombre archivo', size=32)
    archivo = fields.Binary('Archivo', filters='.xls')

    def _get_empleado(self, id):
        empleado_id = self.env['hr.employee'].search([('id', '=', id)])
        return empleado_id

    def empleados_inicio_anio(self, company_id, anio):
        empleados = 0
        empleado_ids = self.env['hr.employee'].search([['company_id', '=', company_id]])
        for empleado in empleado_ids:
            if empleado.contract_ids:
                for contrato in empleado.contract_ids:
                    if contrato.state == 'open':
                        anio_fin_contrato = 0
                        anio_inicio_contrato = contrato.date_start.year
                        if contrato.date_end:
                            anio_fin_contrato = contrato.date_end.year
                        if anio_inicio_contrato < anio and (contrato.date_end == False or anio_fin_contrato < anio):
                            empleados += 1
        return empleados

    def empleados_fin_anio(self, company_id, anio):
        empleados = 0
        empleado_ids = self.env['hr.employee'].search([['company_id', '=', company_id]])
        for empleado in empleado_ids:
            if empleado.contract_ids:
                for contrato in empleado.contract_ids:
                    if contrato.state == 'open':
                        anio_fin_contrato = 0
                        anio_inicio_contrato = contrato.date_start.year
                        if contrato.date_end:
                            anio_fin_contrato = contrato.date_end.year
                        if anio_inicio_contrato <= anio and (contrato.date_end == False or anio_fin_contrato <= anio):
                            empleados += 1
        return empleados

    def _get_salario_promedio(self, id):
        extra_ordinario_total = 0
        historial_salario = []
        salario_meses = {}
        salario_total = 0
        salarios = {'salario_promedio': 0, 'totales': 0, 'mes': {}}
        empleado_id = self._get_empleado(id)
        if empleado_id.contract_ids[0].historial_salario_ids:
            for linea in empleado_id.contract_ids[0].historial_salario_ids:
                historial_salario.append({'salario': linea.salario, 'fecha': linea.fecha})
            # Todo el historial??
            historial_salario_ordenado = sorted(historial_salario, key=lambda k: k['fecha'], reverse=True)
            meses_laborados = (empleado_id.contract_id.date_end.year - empleado_id.contract_ids[
                0].date_start.year) * 12 + (empleado_id.contract_id.date_end.month - empleado_id.contract_ids[
                0].date_start.month)
            contador_mes = 0
            if meses_laborados >= 6:
                # Crea un diccionario inicial con los ultimos seis meses trabajos, salarios, extras y total
                while contador_mes < 6:
                    mes = relativedelta(months=contador_mes)
                    resta_mes = empleado_id.contract_id.date_end - mes
                    mes_letras = a_letras.mes_a_letras(resta_mes.month - 1)
                    llave = '01-' + str(resta_mes.month) + '-' + str(resta_mes.year)
                    salario_meses[llave] = {'nombre': mes_letras.upper(), 'salario': 0, 'anio': resta_mes.year,
                                            'mes_numero': resta_mes.month - 1, 'extra': 0, 'total': 0}
                    contador_mes += 1
            else:
                while contador_mes <= meses_laborados:
                    mes = relativedelta(months=contador_mes)
                    resta_mes = empleado_id.contract_id.date_end - mes
                    mes_letras = a_letras.mes_a_letras(resta_mes.month - 1)
                    llave = '01-' + str(resta_mes.month) + '-' + str(resta_mes.year)
                    salario_meses[llave] = {'nombre': mes_letras.upper(), 'salario': 0, 'anio': resta_mes.year,
                                            'mes_numero': resta_mes.month - 1, 'extra': 0, 'total': 0}
                    contador_mes += 1

            contador_mes = 0
            # fecha primer salario
            fecha_inicio_diferencia = datetime.strptime(str(historial_salario_ordenado[0]['fecha']), '%Y-%m-%d')
            # total meses trabajaoos
            diferencia_meses = (empleado_id.contract_id.date_end.year - fecha_inicio_diferencia.year) * 12 + (
                        empleado_id.contract_id.date_end.month - fecha_inicio_diferencia.month)

            posicion_siguiente = 0
            for linea in historial_salario_ordenado:
                contador = 0
                condicion = False
                # solo si es el primer loop, aumentamos el numero de meses a uno mas
                if posicion_siguiente == 0:
                    diferencia_meses += 1
                # mientras recorremos el total de meses trabajados
                while contador < (diferencia_meses):

                    mes = relativedelta(months=contador_mes)
                    print(mes,"messs!")
                    # mes anterior al terminar el contrato
                    resta_mes = empleado_id.contract_id.date_end - mes
                    mes_letras = a_letras.mes_a_letras(resta_mes.month - 1)
                    llave = '01-' + str(resta_mes.month) + '-' + str(resta_mes.year)
                    if llave in salario_meses:
                        # adjuntamos el valor del salario y acumulamos todo el total
                        salario_meses[llave]['salario'] = linea['salario']
                        salario_meses[llave]['total'] += linea['salario']
                        salario_total += linea['salario']
                    contador += 1
                    contador_mes += 1

                if len(historial_salario_ordenado) > 1:
                    # fecha del salario
                    fecha_cambio_salario = datetime.strptime(str(linea['fecha']), '%Y-%m-%d')

                    posicion_siguiente = historial_salario_ordenado.index(linea) + 1
                    # si la siguiente posición es menor a la longitud del historial de salario ordenado
                    if posicion_siguiente < len(historial_salario_ordenado):
                        fecha_inicio_diferencia = datetime.strptime(
                            str(historial_salario_ordenado[posicion_siguiente]['fecha']), '%Y-%m-%d')
                        # calcula la posicion siguiente del loop
                        diferencia_meses = (fecha_cambio_salario.year - fecha_inicio_diferencia.year) * 12 + (
                                    fecha_cambio_salario.month - fecha_inicio_diferencia.month)

            nomina_ids = self.env['hr.payslip'].search([('employee_id', '=', empleado_id.id)], order='date_to asc')
            if nomina_ids:
                for nomina in nomina_ids:
                    mes_nomina = nomina.date_to.month
                    anio_nomina = nomina.date_to.year
                    llave = '01-' + str(mes_nomina) + '-' + str(anio_nomina)
                    extra_ordinario_ids = nomina.company_id.extra_ordinario_ids
                    # acumula las horas extras en Q y lo agrega al total de los salarios acumulado
                    if llave in salario_meses:
                        for linea in nomina.line_ids:
                            if linea.salary_rule_id.id in extra_ordinario_ids.ids:
                                salario_meses[llave]['extra'] += linea.total
                                salario_meses[llave]['total'] += linea.total
                                extra_ordinario_total += linea.total

        salario_meses = sorted(salario_meses.items(), key=lambda x: datetime.strptime(x[0], '%d-%m-%Y'))

        salarios['totales'] = salario_total
        salarios['extra_ordinario_total'] = extra_ordinario_total
        salarios['total_total'] = (salario_total + extra_ordinario_total)

        salarios['total_promedio'] = salario_total / len(salario_meses)
        salarios['extra_ordinario_promedio'] = extra_ordinario_total / len(salario_meses)
        salarios['total_salario_promedio'] = salarios['total_total'] / len(salario_meses)
        return {'salarios': salarios, 'meses_salarios': salario_meses}

    def _get_dias_laborados(self, id):
        empleado_id = self._get_empleado(id)
        dias = datetime.strptime(str(empleado_id.contract_ids[0].date_end), "%Y-%m-%d") - datetime.strptime(
            str(empleado_id.contract_ids[0].date_start), "%Y-%m-%d")
        return dias.days + 1

    def _get_indemnizacion(self, id):
        dias_laborados = 0
        salario_promedio = 0
        indemnizacion = 0
        regla_76_78 = 0
        regla_42_92 = 0
        indemnizacion = 0
        empleado_id = self._get_empleado(id)
        if empleado_id.contract_id.calcula_indemnizacion:
            # toma el rango del dia final e inicial del contrato
            dias_laborados = self._get_dias_laborados(id)
            salario_promedio = self._get_salario_promedio(id)
            salario_diario = salario_promedio['salarios']['total_salario_promedio'] / 365
            regla_76_78 = ((salario_promedio['salarios']['total_salario_promedio'] / 12) / 365) * dias_laborados
            regla_42_92 = ((salario_promedio['salarios']['total_salario_promedio'] / 12) / 365) * dias_laborados
            indemnizacion = (salario_diario * dias_laborados) + regla_76_78 + regla_42_92
        return indemnizacion

    def print_report(self):
        datas = {'ids': self.env.context.get('active_ids', [])}
        res = self.read(['anio'])
        res = res and res[0] or {}
        res['anio'] = res['anio']
        datas['form'] = res
        return self.env.ref('rrhh.action_informe_empleador').report_action([], data=datas)

    def dias_trabajados_anual(self, empleado_id, anio, payslips):
        print(payslips,"que pedo")
        dias_laborados = 0
        for pay in payslips:
            for input in pay.input_line_ids:
                if input.code == 'DL':
                    dias_laborados += input.amount

        # anio_inicio_contrato = int(empleado_id.contract_id.date_start.year)
        # # AÑO MES Y DIA DEL PRIMERO DE ENERO
        # anio_inicio = datetime.strptime(str(anio) + '-02' + '-01', '%Y-%m-%d').date().strftime('%Y-%m-%d')
        # # AÑO MES Y DIA DEL 31 DE DICIEMBRE
        # anio_fin = datetime.strptime(str(anio) + '-02' + '-29', '%Y-%m-%d').date().strftime('%Y-%m-%d')
        # dias_laborados = 0
        # empleado = self.env['hr.employee'].browse(empleado_id.id)
        #
        # # SI TENEMOS FINALIZACION DE CONTRATO
        # if empleado_id.contract_id.date_start and empleado_id.contract_id.date_end:
        #     anio_fin_contrato = int(empleado_id.contract_id.date_end.year)
        #     #SI EL INICIO Y FIN DE CONTRATO ES EN EL MISMO AÑO QUE SE REALIZADO EL INFORME
        #     if anio_inicio_contrato == anio and anio_fin_contrato == anio:
        #         dias = empleado._get_work_days_data_batch(Datetime.from_string(empleado_id.contract_id.date_start),
        #                                                   Datetime.from_string(empleado_id.contract_id.date_end),
        #                                                   calendar=empleado_id.contract_id.resource_calendar_id)
        #         if dias:
        #             print(dias,"dias trabajados!!")
        #             for dato in dias:
        #                 print(dato,"datoo")
        #                 if 'days' in dias[dato]:
        #                     dias_laborados = dias[dato]['days']
        #     # SI EL CONTRATO DE INCIO ES DIFERENTE AL AÑO DEL INFORME PERO ES IGUAL AL DEL AÑO DE FIN DEL CONTRATO
        #     if anio_inicio_contrato != anio and anio_fin_contrato == anio:
        #         dias = empleado._get_work_days_data_batch(Datetime.from_string(anio_inicio),
        #                                                   Datetime.from_string(empleado_id.contract_id.date_end),
        #                                                   calendar=empleado_id.contract_id.resource_calendar_id)
        #         if dias:
        #             for dato in dias:
        #                 if 'days' in dias[dato]:
        #                     dias_laborados = dias[dato]['days']
        # # SI TIENE INICIO DE CONTRATO PERO NO TIENE FINALIZACION DE CONTRATO
        # if empleado_id.contract_id.date_start and empleado_id.contract_id.date_end == False:
        #     # SI EL INICIO DE CONTRATO ES EL MISMO QUE EN EL WIZARD
        #     if anio_inicio_contrato == anio:
        #         dias = empleado._get_work_days_data_batch(Datetime.from_string(empleado_id.contract_id.date_start),
        #                                                   Datetime.from_string(anio_fin),
        #                                                   calendar=empleado_id.contract_id.resource_calendar_id)
        #         if dias:
        #             for dato in dias:
        #                 if 'days' in dias[dato]:
        #                     dias_laborados = dias[dato]['days']
        #     #TOMAMOS EL RANGO DE TODOO EL AÑO
        #     else:
        #         print(empleado_id.name,"empleado")
        #         dias = empleado_id._get_work_days_data_batch(Datetime.from_string(anio_inicio),
        #                                                      Datetime.from_string(anio_fin),
        #                                                      calendar=empleado_id.contract_id.resource_calendar_id)
        #         print(dias,"dias")
        #
        #         if dias:
        #             for dato in dias:
        #                 print(dato,"datoo!")
        #                 if 'days' in dias[dato]:
        #                     dias_laborados = dias[dato]['days']
        return dias_laborados

    def print_report_excel(self):
        for w in self:

            dict = {}
            empleados_id = self.env.context.get('active_ids', [])
            f = io.BytesIO()
            libro = xlsxwriter.Workbook(f)
            # año del reporte
            dict['anio'] = w['anio']
            empleados_archivados = self.env['hr.employee'].sudo().search(
                [('active', '=', False), ('id', 'in', empleados_id)])
            empleados_activos = self.env['hr.employee'].sudo().search(
                [('active', '=', True), ('id', 'in', empleados_id)])
            empleados = empleados_archivados + empleados_activos



            hoja_empleado = libro.add_worksheet('Empleado')
            formato_fecha = libro.add_format({'num_format': 'dd/mm/yy'})
            # datos = libro.add_worksheet('Hoja2')

            # Formato para encabezados
            header_format = libro.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'vcenter',
                'align': 'center',
                'fg_color': '#D7E4BC',
                'border': 1
            })
            hoja_empleado.set_column('A:AT', 20)
            hoja_empleado.set_row(0, 40)


            hoja_empleado.write(0, 0, 'Numero de empleado',header_format)
            hoja_empleado.write(0, 1, 'Primer Nombre',header_format)
            hoja_empleado.write(0, 2, 'Segundo Nombre',header_format)
            hoja_empleado.write(0, 3, 'Primer Apellido',header_format)
            hoja_empleado.write(0, 4, 'Segundo Apellido',header_format)
            hoja_empleado.write(0, 5, 'Apellido de casada',header_format)
            hoja_empleado.write(0, 6, 'Nacionalidad',header_format)
            hoja_empleado.write(0, 7, 'Tipo de discapacidad', header_format)
            hoja_empleado.write(0, 8, 'Estado Civil',header_format)
            hoja_empleado.write(0, 9, 'Documento Identificación',header_format)
            hoja_empleado.write(0, 10, 'Número de Documento',header_format)
            hoja_empleado.write(0, 11, 'Pais Origen',header_format)
            hoja_empleado.write(0, 12, 'Número de expediente del permiso de extranjero',header_format)
            hoja_empleado.write(0, 13, 'Lugar Nacimiento',header_format)
            hoja_empleado.write(0, 14, 'Número de Identificación Tributaria NIT',header_format)
            hoja_empleado.write(0, 15, 'Número de Afiliación IGSS',header_format)
            hoja_empleado.write(0, 16, 'Sexo',header_format)
            hoja_empleado.write(0, 17, 'Fecha Nacimiento',header_format)
            hoja_empleado.write(0, 18, 'Nivel Académico',header_format)
            hoja_empleado.write(0, 19, 'Título o diploma',header_format)
            hoja_empleado.write(0, 20, 'Pueblo de pertenencia',header_format)
            hoja_empleado.write(0, 21, 'Comunidad Linguistica',header_format)
            hoja_empleado.write(0, 22, 'Cantidad de Hijos',header_format)

            hoja_empleado.write(0, 23, 'Temporalidad del contrato',header_format)
            hoja_empleado.write(0, 24, 'Tipo Contrato',header_format)
            hoja_empleado.write(0, 25, 'Fecha Inicio Labores',header_format)
            hoja_empleado.write(0, 26, 'Fecha Reinicio-laboreso',header_format)
            hoja_empleado.write(0, 27, 'Fecha Retiro Labores',header_format)
            hoja_empleado.write(0, 28, 'Ocupación',header_format)
            hoja_empleado.write(0, 29, 'Jornada de Trabajo',header_format)
            hoja_empleado.write(0, 30, 'Dias Laborados en el Año',header_format)

            hoja_empleado.write(0, 31, 'Salario Mensual Nominal',header_format)
            hoja_empleado.write(0, 32, 'Salario Anual Nominal',header_format)
            hoja_empleado.write(0, 33, 'Bonificación Decreto 78-89  (Q.250.00)',header_format)
            hoja_empleado.write(0, 34, 'Total Horas Extras Anuales',header_format)
            hoja_empleado.write(0, 35, 'Valor de Hora Extra',header_format)
            hoja_empleado.write(0, 36, 'Monto Aguinaldo Decreto 76-78',header_format)
            hoja_empleado.write(0, 37, 'Monto Bono 14  Decreto 42-92',header_format)
            hoja_empleado.write(0, 38, 'Retribución por Comisiones',header_format)
            hoja_empleado.write(0, 39, 'Viaticos',header_format)
            hoja_empleado.write(0, 40, 'Bonificaciones Adicionales',header_format)
            hoja_empleado.write(0, 41, 'Retribución por vacaciones',header_format)
            hoja_empleado.write(0, 42, 'Retribución por Indemnización (Articulo 82)',header_format)
            hoja_empleado.write(0, 43, 'Sucursal',header_format)
            # hoja_empleado.write(0, 45, 'Nombre, Denominación  o Razón Social del Patrono')

            fila = 1
            empleado_numero = 1
            numero = 1
            for empleado in empleados:
                nombre_empleado = empleado.name.split()
                """
                Muestra datoso si tiene primer nombre en el campo 
                """
                if empleado.primer_nombre:
                    nominas_lista = []
                    contrato = self.env['hr.contract'].search(
                        [('employee_id', '=', empleado.id), ('state', '=', 'open')])
                    nomina_id = self.env['hr.payslip'].search([['employee_id', '=', empleado.id],['struct_id.name',"=","2da Quincena"],['state','=','done']])
                    dias_trabajados = 0
                    salario_anual_nominal = 0
                    bonificacion = 0
                    estado_civil = 0
                    horas_extras = 0
                    aguinaldo = 0
                    bono = 0
                    bonificaciones_adicionales = 0
                    indemnizacion = 0

                    valor_horas_extras = 0
                    retribucion_comisiones = 0
                    viaticos = 0
                    retribucion_vacaciones = 0
                    bonificacion_decreto = 0
                    precision_currency = empleado.company_id.currency_id
                    # calcula indemnizacion si el contrato tiene fecha de finalización
                    # indemnizacion = precision_currency.round(self._get_indemnizacion(empleado.id)) if \
                    # empleado.contract_ids[0].date_end else 0
                    salario_anual_nominal_promedio = 0
                    nominas = {}
                    numero_horas_extra = 0
                    numero_nominas_salario = 0
                    genero = ''
                    dias_trabajados_anual = self.dias_trabajados_anual(empleado, w['anio'], nomina_id)
                    for nomina in nomina_id:
                        nomina_anio = nomina.date_from.year
                        nomina_mes = nomina.date_from.month

                        # w as wizard
                        if w['anio'] == nomina_anio:
                            # SI TIENE OTRAS ENTRADAS COMO HE
                            if nomina.input_line_ids:
                                for entrada in nomina.input_line_ids:
                                    for horas_entrada in nomina.company_id.numero_horas_extras_ids:
                                        # SI LA ENTRADA DE HE ES IGUAL A LA CONFIGURADA EN LA COMPANIA
                                        if entrada.code == horas_entrada.code:
                                            numero_horas_extra += entrada.amount
                            # ITERA SOBRE CADA ENTRADA DE TRABAJO, OJO QUE ESTA VARIABLE NO SE ESTA USANDO
                            for linea in nomina.worked_days_line_ids:
                                dias_trabajados += linea.number_of_days
                            # ITERA SOBRE CADA LINEA DE LA NOMINA, ES DECIR SOBRE CADA REGLA SALARIAL
                            for linea in nomina.line_ids:
                                # Investigar que tipos de salarios o relgas salariales deben de considerarse para el calculo anual
                                # SEGUN LAS REGLAS SALARIALES PARA EL CALCULO DEL SALARIO ANUAL
                                if linea.salary_rule_id.id in nomina.company_id.salario_ids.ids:
                                    salario_anual_nominal += linea.total
                                    # SI LA NOMINA MES DE INICIO NO ESTA EN EL DICT LO ADJUNTAMOS
                                    if nomina_mes not in nominas:
                                        nominas[nomina_mes] = {'salario': 0, 'bonificacion': 0}
                                    # OJO AQUI SUMAMOS EL ACUMULADO SALARIO POR MES
                                    nominas[nomina_mes]['salario'] += salario_anual_nominal
                                    # ESTE CAMPO NO SE ESSTA USANDO, SOLO CUENTA EL NUMERO DE RS POR NOMINA
                                    numero_nominas_salario += 1
                                if linea.salary_rule_id.id in nomina.company_id.bonificacion_ids.ids:
                                    bonificacion += linea.total
                                if linea.salary_rule_id.id in nomina.company_id.aguinaldo_ids.ids:
                                    aguinaldo += linea.total
                                if linea.salary_rule_id.id in nomina.company_id.bono_ids.ids:
                                    bono += linea.total
                                if linea.salary_rule_id.id in nomina.company_id.horas_extras_ids.ids:
                                    horas_extras += linea.total
                                if linea.salary_rule_id.id in nomina.company_id.retribucion_comisiones_ids.ids:
                                    retribucion_comisiones += linea.total
                                if linea.salary_rule_id.id in nomina.company_id.viaticos_ids.ids:
                                    viaticos += linea.total
                                if linea.salary_rule_id.id in nomina.company_id.retribucion_vacaciones_ids.ids:
                                    retribucion_vacaciones += linea.total
                                if linea.salary_rule_id.id in nomina.company_id.bonificaciones_adicionales_ids.ids:
                                    bonificaciones_adicionales += linea.total
                                if linea.salary_rule_id.id in nomina.company_id.indemnizacion_ids.ids:
                                    indemnizacion += linea.total

                                    # SUMA LA BONIFICACION DECRETO EN EL SALARIO DEL MES PERO UNICAMENTE HAY QUE PONER 250
                                if linea.salary_rule_id.id in nomina.company_id.decreto_ids.ids:
                                    bonificacion_decreto += linea.total
                                    if nomina_mes not in nominas:
                                        nominas[nomina_mes] = {'salario': 0, 'bonificacion': 0}
                                    nominas[nomina_mes]['bonificacion'] += bonificacion_decreto
                    # BONIFICACION DECRETO
                    otras_boni = 0
                    if empleado.contract_id.bonificacion == 250:
                        boni = 250
                    elif empleado.contract_id.bonificacion > 250:
                        boni = 250
                        otras_boni = empleado.contract_id.bonificacion-250
                    else:
                        boni = ''

                    salario_anual_nominal_promedio = salario_anual_nominal / len(
                        nominas) if salario_anual_nominal > 0 else 0
                    if empleado.gender == 'male':
                        genero = 1
                    if empleado.gender == 'female':
                        genero = 2
                    if empleado.marital == 'single':
                        estado_civil = 1
                    if empleado.marital == 'married':
                        estado_civil = 2
                    if empleado.marital == 'widower':
                        estado_civil = 3
                    if empleado.marital == 'divorced':
                        estado_civil = 4
                    if empleado.marital == 'separado':
                        estado_civil = 5
                    if empleado.marital == 'unido':
                        estado_civil = 6

                    hoja_empleado.write(fila, 0, empleado_numero)
                    hoja_empleado.write(fila, 1, empleado.primer_nombre if empleado.primer_nombre else '')
                    hoja_empleado.write(fila, 2, empleado.segundo_nombre if empleado.segundo_nombre else '')
                    hoja_empleado.write(fila, 3, empleado.primer_apellido if empleado.primer_apellido else '')
                    hoja_empleado.write(fila, 4, empleado.segundo_apellido if empleado.segundo_apellido else '')
                    hoja_empleado.write(fila, 5, empleado.apellido_casada if empleado.apellido_casada else '')
                    hoja_empleado.write(fila, 6,  'GTM')
                    hoja_empleado.write(fila, 7,  empleado.tipo_discapacidad if empleado.tipo_discapacidad else '')
                    hoja_empleado.write(fila, 8, estado_civil)
                    hoja_empleado.write(fila, 9, empleado.documento_identificacion)
                    hoja_empleado.write(fila, 10, empleado.numero_doc)
                    #pAIS DE ORIGEN
                    hoja_empleado.write(fila, 11, 'GTM')
                    hoja_empleado.write(fila, 12, empleado.numero_permiso_extranjero if empleado.numero_permiso_extranjero  else '')
                    hoja_empleado.write(fila, 13, empleado.lugar_nacimiento)
                    hoja_empleado.write(fila, 14, empleado.nit)
                    hoja_empleado.write(fila, 15, empleado.igss)
                    hoja_empleado.write(fila, 16, genero)

                    hoja_empleado.write(fila, 17, empleado.birthday, formato_fecha)
                    hoja_empleado.write(fila, 18, empleado.nivel_academico if empleado.nivel_academico else '')
                    hoja_empleado.write(fila, 19, empleado.profesion if empleado.profesion else '')
                    hoja_empleado.write(fila, 20, empleado.pueblo_pertenencia)
                    hoja_empleado.write(fila, 21, empleado.comunidad_ling if empleado.comunidad_ling else '')

                    hoja_empleado.write(fila, 22, empleado.hijos)
                    hoja_empleado.write(fila, 23, contrato.temporalidad_contrato if contrato.temporalidad_contrato  else '')
                    hoja_empleado.write(fila, 24, contrato.tipo_contrato if contrato.tipo_contrato  else '')
                    # hoja_empleado.write(fila, 16, empleado.trabajado_extranjero)
                    # hoja_empleado.write(fila, 17, empleado.forma_trabajo_extranjero)
                    # hoja_empleado.write(fila, 18, empleado.pais_trabajo_extranjero_id.name)
                    # hoja_empleado.write(fila, 19, empleado.finalizacion_laboral_extranjero)
                    hoja_empleado.write(fila, 25, contrato.date_start if contrato.date_start  else '', formato_fecha)
                    hoja_empleado.write(fila, 26, contrato.fecha_reinicio_labores if contrato.fecha_reinicio_labores  else '',formato_fecha)
                    hoja_empleado.write(fila, 27, contrato.date_end if contrato.date_end else '',formato_fecha)
                    hoja_empleado.write(fila, 28, empleado.puesto if empleado.puesto else '')
                    hoja_empleado.write(fila, 29, empleado.jornada_trabajo)

                    # hoja_empleado.write(fila, 25, contrato.structure_type_id.default_struct_id.name)

                    hoja_empleado.write(fila, 30, dias_trabajados_anual)
                    # hoja_empleado.write(fila, 32, empleado.permiso_trabajo)
                    # salario mensual nominal ###########
                    hoja_empleado.write(fila, 31, contrato.wage)
                    # hoja_empleado.write(fila, 33, salario_anual_nominal_promedio)
                    # acumulado#############
                    hoja_empleado.write(fila, 32, salario_anual_nominal)
                    hoja_empleado.write(fila, 33, boni)
                    hoja_empleado.write(fila, 34, numero_horas_extra)
                    hoja_empleado.write(fila, 35, (
                        (horas_extras / numero_horas_extra) if numero_horas_extra > 0 else horas_extras))
                    hoja_empleado.write(fila, 36, aguinaldo)
                    hoja_empleado.write(fila, 37, bono)
                    hoja_empleado.write(fila, 38, retribucion_comisiones)
                    hoja_empleado.write(fila, 39, viaticos)
                    hoja_empleado.write(fila, 40, bonificaciones_adicionales+otras_boni)
                    hoja_empleado.write(fila, 41, retribucion_vacaciones)
                    hoja_empleado.write(fila, 42, indemnizacion)
                    hoja_empleado.write(fila, 43, empleado.codigo_centro_trabajo)
                    empleado_numero += 1

                    fila += 1
                    numero += 1

            libro.close()
            datos = base64.b64encode(f.getvalue())
            self.write({'archivo': datos, 'name': 'informe_del_empleador.xlsx'})

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'rrhh.informe_empleador',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
