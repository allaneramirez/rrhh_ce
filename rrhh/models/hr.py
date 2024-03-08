# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime
import logging
import xlsxwriter
import io
import base64

class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    codigo_empleado = fields.Char('Código del empleado')

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    numero_liquidacion = fields.Char('Numero o identificacion de liquidacion',groups="hr.group_hr_user")
    codigo_centro_trabajo = fields.Char('Codigo de centro de trabajo asignado',groups="hr.group_hr_user")
    codigo_ocupacion = fields.Char('Codigo ocupacion',groups="hr.group_hr_user")
    condicion_laboral = fields.Selection([('P', 'Permanente'), ('T', 'Temporal')], 'Condicion laboral',groups="hr.group_hr_user")
    tipo_discapacidad = fields.Char('Tipo Discapacidad',groups="hr.group_hr_user")
    numero_doc = fields.Char('Numero de identificación',groups="hr.group_hr_user")
    lugar_nacimiento = fields.Char('Lugar de Nacimiento',groups="hr.group_hr_user")
    hijos = fields.Char('Cantidad de hijos',groups="hr.group_hr_user")
    puesto = fields.Char('Puesto Laboral',groups="hr.group_hr_user")
    comunidad_ling = fields.Char('Comunidad Linguistica',groups="hr.group_hr_user")
    numero_permiso_extranjero = fields.Char('Numero de expediente, permiso estranjero',groups="hr.group_hr_user")

    job_id = fields.Many2one(track_visibility='onchange')
    department_id = fields.Many2one('hr.department', 'Department', track_visibility='onchange')
    diario_pago_id = fields.Many2one('account.journal', 'Diario de Pago',groups="hr.group_hr_user")
    igss = fields.Char('IGSS',groups="hr.group_hr_user")
    irtra = fields.Char('IRTRA',groups="hr.group_hr_user")
    nit = fields.Char('NIT',groups="hr.group_hr_user")
    recibo_id = fields.Many2one('rrhh.recibo', 'Formato de recibo',groups="hr.group_hr_user")
    nivel_academico = fields.Char('Nivel Academico',groups="hr.group_hr_user")
    profesion = fields.Char('Profesion',groups="hr.group_hr_user")
    etnia = fields.Char('Etnia',groups="hr.group_hr_user")
    idioma = fields.Char('Idioma',groups="hr.group_hr_user")
    pais_origen = fields.Many2one('res.country','Pais Origen',groups="hr.group_hr_user")
    trabajado_extranjero = fields.Boolean('A trabajado en el extranjero',groups="hr.group_hr_user")
    motivo_finalizacion = fields.Char('Motivo de finalizacion',groups="hr.group_hr_user")
    jornada_trabajo = fields.Char('Jornada de Trabajo',groups="hr.group_hr_user")
    permiso_trabajo = fields.Char('Permiso de Trabajo',groups="hr.group_hr_user")
    contacto_emergencia = fields.Many2one('res.partner','Contacto de Emergencia',groups="hr.group_hr_user")
    marital = fields.Selection(selection_add=[('separado', 'Separado(a)'),('unido', 'Unido(a)')],groups="hr.group_hr_user")
    edad = fields.Integer(string='Edad',compute="_get_edad",groups="hr.group_hr_user")
    vecindad_dpi = fields.Char('Vecindad DPI',groups="hr.group_hr_user")
    tarjeta_salud = fields.Boolean('Tarjeta de salud',groups="hr.group_hr_user")
    tarjeta_manipulacion = fields.Boolean('Tarjeta de manipulación',groups="hr.group_hr_user")
    tarjeta_pulmones = fields.Boolean('Tarjeta de pulmones',groups="hr.group_hr_user")
    tarjeta_fecha_vencimiento = fields.Date('Fecha de vencimiento tarjeta de salud',groups="hr.group_hr_user")
    codigo_empleado = fields.Char('Código del empleado',groups="hr.group_hr_user")
    departamento_id = fields.Many2one('res.country.state','Departmento',groups="hr.group_hr_user")
    pais_id = fields.Many2one('res.country','Pais',groups="hr.group_hr_user")
    documento_identificacion = fields.Char('Tipo documento identificacion',groups="hr.group_hr_user")
    forma_trabajo_extranjero = fields.Char('Forma trabajada en el extranjero',groups="hr.group_hr_user")
    pais_trabajo_extranjero_id = fields.Many2one('res.country','Pais trabajado en el extranjero',groups="hr.group_hr_user")
    finalizacion_laboral_extranjero = fields.Char('Motivo de finalización de la relación laboral en el extranjero',groups="hr.group_hr_user")
    pueblo_pertenencia = fields.Char('Pueblo de pertenencia',groups="hr.group_hr_user")
    primer_nombre = fields.Char('Primer nombre',groups="hr.group_hr_user")
    segundo_nombre = fields.Char('Segundo nombre',groups="hr.group_hr_user")
    primer_apellido = fields.Char('Primer apellido',groups="hr.group_hr_user")
    segundo_apellido = fields.Char('Segundo apellido',groups="hr.group_hr_user")
    apellido_casada = fields.Char('Apellido casada',groups="hr.group_hr_user")
    centro_trabajo_id = fields.Many2one('res.company.centro_trabajo',strin='Centro de trabajo',groups="hr.group_hr_user")
    cod_est_civil = fields.Char('Codigo Estado Civil',groups="hr.group_hr_user")
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        res1 = super(HrEmployee, self).name_search(name, args, operator=operator, limit=limit)

        records = self.search([('codigo_empleado', 'ilike', name)], limit=limit)
        res2 = records.name_get()

        return res1+res2

    @api.model
    def vacaciones(self, records):

        # Hacer algo con los registros seleccionados
        # for record in records:
        #     print(record)
        #     # Hacer alguna operación con cada registro
        #     pass
        f = io.BytesIO()
        libro = xlsxwriter.Workbook(f)

        header_format = libro.add_format(
            {'font_size': 12, 'align': 'center', 'text_wrap': True, 'valign': 'center',
             'bold': True, 'border': 1
             })
        hoja = libro.add_worksheet("Reporte de vacaciones")
        hoja.merge_range('B2:G2', 'hola', header_format)
        libro.close()
        f.seek(0)
        data = f.read()
        f.close()

        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=ir.attachment&id=%s&filename_field=name&field=datas' % (
                self.env['ir.attachment'].create({
                    'name': 'Reporte_de_vacaciones.xlsx',
                    'datas': base64.encodestring(data),
                    'res_model': 'hr.employee',
                    'res_id': self.id,
                }).id),
            'target': 'new',
        }


    def _get_edad(self):
        for employee in self:
            if employee.birthday:
                dia_nacimiento = int(employee.birthday.strftime('%d'))
                mes_nacimiento = int(employee.birthday.strftime('%m'))
                anio_nacimiento = int(employee.birthday.strftime('%Y'))
                dia_actual = int(datetime.date.today().strftime('%d'))
                mes_actual = int(datetime.date.today().strftime('%m'))
                anio_actual = int(datetime.date.today().strftime('%Y'))

                resta_dia = dia_actual - dia_nacimiento
                resta_mes = mes_actual - mes_nacimiento
                resta_anio = anio_actual - anio_nacimiento

                if (resta_mes < 0):
                    resta_anio = resta_anio - 1
                elif (resta_mes == 0):
                    if (resta_dia < 0):
                        resta_anio = resta_anio - 1
                    if (resta_dia > 0):
                        resta_anio = resta_anio
                employee.edad = resta_anio
            else:
                employee.edad = 0
