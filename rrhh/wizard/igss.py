# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
import time
import base64
import io
import logging
import datetime
from datetime import datetime


class liquidacion(models.TransientModel):
    _name = 'rrhh.igss.liquidacion'
    _description = 'Tipo de Liquidacion'

    numero_liquidacion = fields.Char('Numero de liquidacion')
    tipo_planilla_id = fields.Many2one('res.company.tipo_planilla', string='Tipo de Planilla')
    fecha_inicial = fields.Date('Fecha inicial liquidación', readonly=False)
    fecha_final = fields.Date('Fecha final de liquidación')
    planilla_c_o = fields.Selection([('C', 'Complementaria'),
                                     ('O', 'Original')], 'Tipo de Liquidación', default='0')
    numero_nota_recargo = fields.Char('Numero nota de Recargo')
    wizard_id = fields.Many2one('rrhh.igss.wizard', string='Asistente de IGSS')


class rrhh_igss_wizard(models.TransientModel):
    _name = 'rrhh.igss.wizard'
    _description = 'Asistente para Generación planilla IGSS'

    def _default_payslip_run(self):
        if len(self.env.context.get('active_ids', [])) > 0:
            nominas = self.env['hr.payslip.run'].search([('id', 'in', self.env.context.get('active_ids'))])
            return nominas
        else:
            return None

    payslip_run_id = fields.Many2many('hr.payslip.run', string='Payslip run', default=_default_payslip_run)
    archivo = fields.Binary('Archivo')
    name = fields.Char('File Name', size=32)
    tipo_planilla = fields.Selection([('0', 'Produccion'),
                                      ('1', 'Pruebas')], 'Produccion/Pruebas', default='0')
    relacion_ids = fields.One2many('rrhh.igss.liquidacion', 'wizard_id', string='Liquidaciones')

    def generar(self):
        datos = ''
        for w in self:
            # PATRONO
            datos += str(w.payslip_run_id[0].slip_ids[0].company_id.version_mensaje) + '|' + str(
                datetime.today().strftime('%d/%m/%Y')) + '|' + str(
                w.payslip_run_id[0].slip_ids[0].company_id.numero_patronal) + '|' + str(
                datetime.strptime(str(w.payslip_run_id[0].date_start), '%Y-%m-%d').date().strftime('%m')).lstrip(
                '0') + '|' + str(
                datetime.strptime(str(w.payslip_run_id[0].date_start), '%Y-%m-%d').date().strftime('%Y')).lstrip(
                '0') + '|' + str(w.payslip_run_id[0].slip_ids[0].company_id.name) + '|' + str(
                w.payslip_run_id[0].slip_ids[0].company_id.vat) + '|' + str(
                w.payslip_run_id[0].slip_ids[0].company_id.email) + '|' + self.tipo_planilla + '\r\n'
            # CENTROS
            datos += '[centros]' + '\r\n'
            # POR CADA CENTRO DE TRABAJO EN LAS CONFIG DE LA COMPANIA
            for centro in w.payslip_run_id[0].slip_ids[0].company_id.centro_trabajo_ids:
                datos += str(centro.codigo) + '|' + str(centro.nombre) + '|' + str(centro.direccion) + '|' + str(
                    centro.zona) + '|' + str(centro.telefono) + '|' + str(centro.fax) + '|' + str(
                    centro.nombre_contacto) + '|' + str(centro.correo_electronico) + '|' + str(
                    centro.codigo_departamento) + '|' + str(centro.codigo_municipio) + '|' + str(
                    centro.codigo_actividad_economica) + '\r\n'

            # TIPOS DE PLANILLA
            datos += '[tiposplanilla]' + '\r\n'
            for planilla in w.payslip_run_id[0].slip_ids[0].company_id.tipo_planilla_ids:
                datos += str(planilla.ident_tipo_planilla) + '|' + str(planilla.nombre) + '|' + str(
                    planilla.tipo_afiliado) + '|' + str(planilla.periodo_planilla) + '|' + str(
                    planilla.departamento) + '|' + str(planilla.act_economica) + '|' + str(
                    planilla.clase_planilla) + '|' + str(planilla.tiempo_contrato) + '\r\n'
            # LIQUIDACIONES
            datos += '[liquidaciones]' + '\r\n'

            for liquidacion in self.relacion_ids:
                datos += (liquidacion.numero_liquidacion + '|' +
                          liquidacion.tipo_planilla_id.ident_tipo_planilla + '|' +
                          str(datetime.strptime(str(liquidacion.fecha_inicial),'%Y-%m-%d').date().strftime('%d/%m/%Y')) + '|' +
                          str(datetime.strptime(str(liquidacion.fecha_final),'%Y-%m-%d').date().strftime('%d/%m/%Y')) + '|' +
                          liquidacion.planilla_c_o + '|' + (liquidacion.numero_nota_recargo if liquidacion.numero_nota_recargo else '') + '|' +'\r\n')
            datos += '[empleados]' + '\r\n'
            empleados = {}
            suspensiones = []
            licencia = []
            for payslip_run in w.payslip_run_id:
                # POR CADA NOMINA EN EL LOTE
                for slip in payslip_run.slip_ids:
                    if slip.contract_id:
                        # ADJUNTAMOS EL EMPLEADO A AL DICCIONARIO
                        if slip.employee_id.id not in empleados:
                            empleados[slip.employee_id.id] = {'empleado_id': slip.employee_id.id,
                                                              'informacion': [0] * 19, 'suspension': ''}

                        # EXTRAEMOS DATOS DEL EMPLEADO
                        numero_liq = ''
                        for liq in self.relacion_ids:
                            print(liq.tipo_planilla_id,slip.employee_id.tipo_planilla_id,"heeey")
                            if liq.tipo_planilla_id == slip.employee_id.tipo_planilla_id:
                                numero_liq = liq.numero_liquidacion


                        numero_afiliado = str(slip.employee_id.igss) if slip.employee_id.igss else ''
                        primer_nombre = str(slip.employee_id.primer_nombre) if slip.employee_id.primer_nombre else ''
                        segundo_nombre = str(slip.employee_id.segundo_nombre) if slip.employee_id.segundo_nombre else ''
                        primer_apellido = str(
                            slip.employee_id.primer_apellido) if slip.employee_id.primer_apellido else ''
                        segundo_apellido = str(
                            slip.employee_id.segundo_apellido) if slip.employee_id.segundo_apellido else ''
                        apellido_casada = str(
                            slip.employee_id.apellido_casada) if slip.employee_id.apellido_casada else ''
                        sueldo = 0
                        # SUMAMOS TODO LO DEL IGGS (cantidad de lo que se deduce el Iggs)
                        # EL IMPORTE SOBRE EL CUAL SE CALCULO EL IGSS
                        for linea in slip.line_ids:
                            if linea.salary_rule_id.id in slip.employee_id.company_id.igss_ids.ids:
                                sueldo += linea.amount

                        mes_inicio_contrato = datetime.strptime(str(slip.contract_id.date_start), '%Y-%m-%d').month
                        mes_final_contrato = datetime.strptime(str(slip.contract_id.date_end),
                                                               '%Y-%m-%d').month if slip.contract_id.date_end else ''
                        mes_planilla = datetime.strptime(str(payslip_run.date_start), '%Y-%m-%d').month
                        fecha_alta = str(
                            datetime.strptime(str(slip.contract_id.date_start), '%Y-%m-%d').date().strftime(
                                '%d/%m/%Y')) if mes_inicio_contrato == mes_planilla else ''
                        fecha_baja = str(datetime.strptime(str(slip.contract_id.date_end), '%Y-%m-%d').date().strftime(
                            '%d/%m/%Y')) if mes_final_contrato == mes_planilla else ''

                        centro_trabajo = str(
                            slip.employee_id.codigo_centro_trabajo) if slip.employee_id.codigo_centro_trabajo else ''
                        nit = str(slip.employee_id.nit) if slip.employee_id.nit else ''
                        codigo_ocupacion = str(slip.employee_id.codigo_ocupacion_igss) if slip.employee_id.codigo_ocupacion_igss else ''
                        condicion_laboral = str(
                            slip.employee_id.condicion_laboral) if slip.employee_id.condicion_laboral else ''
                        deducciones = ''
                        tipo_salario = str(slip.employee_id.tipo_salario) if slip.employee_id.tipo_salario else ''
                        horas_laboradas = ''
                        tiempo_contrato = str(slip.employee_id.tiempo_contrato) if slip.employee_id.tiempo_contrato else ''
                        dias_laborados = ''

                        empleados[slip.employee_id.id]['informacion'][0] = (numero_liq)
                        empleados[slip.employee_id.id]['informacion'][1] = (numero_afiliado)
                        empleados[slip.employee_id.id]['informacion'][2] = (primer_nombre)
                        empleados[slip.employee_id.id]['informacion'][3] = (segundo_nombre)
                        empleados[slip.employee_id.id]['informacion'][4] = (primer_apellido)
                        empleados[slip.employee_id.id]['informacion'][5] = (segundo_apellido)
                        empleados[slip.employee_id.id]['informacion'][6] = (apellido_casada)
                        empleados[slip.employee_id.id]['informacion'][7] += sueldo
                        empleados[slip.employee_id.id]['informacion'][8] = (fecha_alta)
                        empleados[slip.employee_id.id]['informacion'][9] = (fecha_baja)
                        empleados[slip.employee_id.id]['informacion'][10] = (centro_trabajo)
                        empleados[slip.employee_id.id]['informacion'][11] = (nit)
                        empleados[slip.employee_id.id]['informacion'][12] = (codigo_ocupacion)
                        empleados[slip.employee_id.id]['informacion'][13] = (condicion_laboral)
                        empleados[slip.employee_id.id]['informacion'][14] = (deducciones)
                        empleados[slip.employee_id.id]['informacion'][15] = (tipo_salario)
                        empleados[slip.employee_id.id]['informacion'][16] = (horas_laboradas)
                        empleados[slip.employee_id.id]['informacion'][17] = (tiempo_contrato)
                        empleados[slip.employee_id.id]['informacion'][18] = (dias_laborados)
            # AGREGAOS LA INFO DE CADA EMPLEADO A LA LINEA DE TEXTO
            if empleados:
                for empleado in empleados.values():
                    for dato in empleado['informacion']:
                        datos += str(dato) + '|'
                    datos += '\r\n'
                    # OBTENEMOS TODAS LAS AUSENCIAS EN LAS FECHAS INGRESADAS
                    ausencias = self.env['hr.leave'].search(
                        [('employee_id', '=', empleado['empleado_id']), ('request_date_from', '>=', self.payslip_run_id.date_start),
                         ('request_date_to', '<=', self.payslip_run_id.date_end), ('state', '=', 'validate')])

                    if ausencias:
                        # OBTENEMOS EL CODIGO POR CADA REGLA CONFIUGRADA EN LA COMPANIA RELACIONADA AL IGGS
                        for ausencia in ausencias:
                            # SI EL CODIGO DE LA AUSENCIA ES DE TIPO IGGS
                            if ausencia.holiday_status_id.code == 'IGSS':
                                fecha_inicio = str(
                                    datetime.strptime(str(ausencia.date_from), '%Y-%m-%d %H:%M:%S').date().strftime(
                                        '%d/%m/%Y'))
                                fecha_fin = str(
                                    datetime.strptime(str(ausencia.date_to), '%Y-%m-%d %H:%M:%S').date().strftime(
                                        '%d/%m/%Y'))
                                suspensiones.append(
                                    numero_liq + '|' + numero_afiliado + '|' + primer_nombre + '|' + segundo_nombre + '|' + primer_apellido + '|' + segundo_apellido + '|' + apellido_casada + '|' + fecha_inicio + '|' + fecha_fin + '|' + '\r\n')

                            if ausencia.holiday_status_id.code == 'LIC':
                                fecha_inicio = str(
                                    datetime.strptime(str(ausencia.date_from), '%Y-%m-%d %H:%M:%S').date().strftime(
                                        '%d/%m/%Y'))
                                fecha_fin = str(
                                    datetime.strptime(str(ausencia.date_to), '%Y-%m-%d %H:%M:%S').date().strftime(
                                        '%d/%m/%Y'))
                                licencia.append(
                                    numero_liq + '|' + numero_afiliado + '|' + primer_nombre + '|' + segundo_nombre + '|' + primer_apellido + '|' + segundo_apellido + '|' + apellido_casada + '|' + fecha_inicio + '|' + fecha_fin + '|' + '\r\n')


            datos += '[suspendidos]' + '\r\n'
            if suspensiones:
                for suspension in suspensiones:
                    datos += suspension

            datos += '[licencias]' + '\r\n'
            if licencia:
                for l in licencia:
                    datos += l
            datos += '[juramento]' + '\r\n'
            datos += 'BAJO MI EXCLUSIVA Y ABSOLUTA RESPONSABILIDAD, DECLARO QUE LA INFORMACION QUE AQUI CONSIGNO ES FIEL Y EXACTA, QUE ESTA PLANILLA INCLUYE A TODOS LOS TRABAJADORES QUE ESTUVIERON A MI SERVICIO Y QUE SUS SALARIOS SON LOS EFECTIVAMENTE DEVENGADOS, DURANTE EL MES ARRIBA INDICADO' + '\r\n'
            datos += '[finplanilla]' + '\r\n'
            datos = datos.replace('False', '')
        datos = base64.b64encode(datos.encode("utf-8"))
        self.write({'archivo': datos, 'name': 'planilla.txt'})

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'rrhh.igss.wizard',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
