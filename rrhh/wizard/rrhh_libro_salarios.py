# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import base64
import io
import xlsxwriter


class rrhh_libro_salarios(models.TransientModel):
    _name = 'rrhh.libro_salarios'

    anio = fields.Integer('Año', required=True)
    name = fields.Char('Nombre archivo')
    archivo = fields.Binary('Archivo')

    def print_report_excel(self):
        for w in self:
            dic = {}
            dic['anio'] = w['anio']
            f = io.BytesIO()
            libro = xlsxwriter.Workbook(f)

            bold = libro.add_format({'bold': True})
            center = libro.add_format({'align': 'center','valign': 'vcenter'})
            text_wrap_bold = libro.add_format(
                {'text_wrap': 'true', 'align': 'center', 'valign': 'vcenter','bold':True})
            center_border_top = libro.add_format({'top': 1, 'align': 'center',})
            num_format = libro.add_format({'num_format': 'Q#,##0.00'})
            num_format_top = libro.add_format({'num_format': 'Q#,##0.00', 'top': 1, })
            date_format = libro.add_format({'num_format': 'dd/mm/yy', 'align': 'center'})

            ids = self.env.context.get('active_ids', [])
            for id_employee in ids:
                empleado = self.env['report.rrhh.libro_salarios']._get_empleado(id_employee)
                nominas = self.env['report.rrhh.libro_salarios']._get_nominas(id_employee, dic['anio'])
                fecha = self.env['report.rrhh.libro_salarios']._get_contrato(id_employee)
                hoja = libro.add_worksheet(empleado.name)
                # Ancho y alto de las columnas
                i = 1
                while i <22:
                    hoja.set_column(0,i,9)
                    i += 1

                hoja.write(4, 19, 'Folio No.', bold)
                hoja.merge_range('A6:V6', empleado.company_id.name,text_wrap_bold)
                hoja.merge_range('A7:V7', empleado.company_id.vat,text_wrap_bold)
                hoja.merge_range('A8:V8', 'LIBRO COMPUTARIZADO PARA LA OPERACIÓN DE SALARIOS DE TRABAJADORES PERMANENTES,'
                                          'AUTORIZADO POR EL MINISTERIO DE TRABAJO Y',center )
                hoja.merge_range('A9:V9',
                           'PREVISION SOCIAL, FUNDAMENTO LEGAL: ARTÍCULOS 102 DEL DECRETO No. 1441 Y 2 DEL '
                           'ACUERDO MINISTERIAL No. 124-2019', center)
                # FIRST LINE
                hoja.merge_range('A12:E12', empleado.name, center)
                hoja.write(11, 7, empleado.edad, center)
                hoja.merge_range('K12:L12', 'Hombre' if empleado.gender == 'male' else 'Mujer', center)
                hoja.merge_range('N12:Q12', empleado.country_id.name, center)
                hoja.merge_range('S12:V12', empleado.job_id.name, center)

                hoja.merge_range('A13:E13', 'Nombre del trabajador', center_border_top)
                hoja.write(12, 7, 'Edad', center_border_top)
                hoja.merge_range('K13:L13', 'Sexo', center_border_top)
                hoja.merge_range('N13:Q13', 'Nacionalidad', center_border_top)
                hoja.merge_range('S13:V13','Ocupación', center_border_top)
                # SECOND LINE
                hoja.merge_range('A15:E15', empleado.igss, center)
                hoja.merge_range('G15:I15', empleado.identification_id, center)
                hoja.merge_range('N15:Q15', fecha['fecha_ingreso'], date_format)
                if fecha['fecha_finalizacion']:
                    hoja.merge_range('S15:V15', fecha['fecha_finalizacion'], date_format)

                hoja.merge_range('A16:E16', 'No. de afiliación al IGSS', center_border_top)
                hoja.merge_range('G16:I16', 'No. DPI ó permiso de Trabajo', center_border_top)
                hoja.merge_range('N16:Q16', 'Fecha de Ingreso', center_border_top)
                hoja.merge_range('S16:V16','   Fecha de finalización de relación laboral', center_border_top)


                ordinario_total = 0
                extra_ordinario_total = 0
                otros_salarios_total = 0
                septimo_asueto_total = 0
                vacaciones_total = 0
                boni_incentivo_total = 0
                salario_total = 0
                igss_total = 0
                otras_deducciones_total = 0
                isr_total = 0
                total_deducciones = 0
                bono_agui_indem_total = 0
                boni_incentivo_decreto_total = 0
                dev_isr_otro_total = 0
                decreto_total = 0
                incentivo_decreto_total = 0
                liquido_total = 0

                hoja.merge_range('A18:A20', 'No. de Pago', text_wrap_bold)
                hoja.merge_range('B18:B20', 'Periodo de trabajo', text_wrap_bold)
                hoja.merge_range('C18:C20', 'Salario en Quetzales', text_wrap_bold)
                hoja.merge_range('D18:D20', 'Dias Trabajados', text_wrap_bold)
                hoja.merge_range('E18:F18','HORAS TRABAJADAS', text_wrap_bold)
                hoja.merge_range('E19:E20','Ordinarias', text_wrap_bold)
                hoja.merge_range('F19:F20', 'Extraordinarias', text_wrap_bold)

                hoja.merge_range('G18:K18', 'SALARIO DEVENGADO', text_wrap_bold)
                hoja.merge_range('G19:G20', 'Ordinario', text_wrap_bold)
                hoja.merge_range('H19:H20', 'Extraordinario', text_wrap_bold)
                hoja.merge_range('I19:I20',  'Otros salarios', text_wrap_bold)
                hoja.merge_range('J19:J20',  'Septimos y asuetos', text_wrap_bold)
                hoja.merge_range('K19:K20' , 'Vacaciones', text_wrap_bold)

                hoja.merge_range('L18:L20',  'SALARIO TOTAL', text_wrap_bold)

                hoja.merge_range('M18:P18','DEDUCCIONES LEGALES', bold)
                hoja.merge_range('M19:M20', 'Cuota laboral IGSS', text_wrap_bold)
                hoja.merge_range('N19:N20','Descuentos ISR', text_wrap_bold)
                hoja.merge_range('O19:O20','Otras deducciones', text_wrap_bold)
                hoja.merge_range('P19:P20', 'Total', text_wrap_bold)

                hoja.merge_range('Q18:Q20', 'Bonificación anual 42-92,Aguinaldo Decreto 76-78', text_wrap_bold)
                hoja.merge_range('R18:R20', 'Bonificación Incentivo Decreto 37-2001', text_wrap_bold)
                hoja.merge_range('S18:S20', 'Devoluciones I.S.R. y otras', text_wrap_bold)
                hoja.merge_range('T18:T20','Liquido a Recibir', text_wrap_bold)
                hoja.merge_range('U18:U20', 'Firma o No. de boleta', text_wrap_bold)
                hoja.merge_range('V18:V20', 'Observaciones', text_wrap_bold)

                y = 21
                for nomina in nominas:
                    hoja.write(y, 0, nomina['orden'])
                    hoja.write(y, 1, str(nomina['fecha_inicio']) + ' - ' + str(nomina['fecha_fin']))
                    hoja.write(y, 2, nomina['salario'], num_format)
                    hoja.write(y, 3, nomina['dias_trabajados'])
                    # horas
                    hoja.write(y, 4, nomina['ordinarias'])
                    hoja.write(y, 5, nomina['extra_ordinarias'])
                    # salario
                    hoja.write(y, 6, nomina['ordinario'], num_format)
                    hoja.write(y, 7, nomina['extra_ordinario'], num_format)
                    hoja.write(y, 8, nomina['otros_salarios'], num_format)
                    hoja.write(y, 9, nomina['septimos_asuetos'], num_format)
                    hoja.write(y, 10, nomina['vacaciones'], num_format)
                    hoja.write(y, 11, nomina['total_salario_devengado'], num_format)
                    hoja.write(y, 12, nomina['igss'], num_format)
                    hoja.write(y, 13, nomina['isr'], num_format)
                    hoja.write(y, 14, nomina['otras_deducciones'], num_format)
                    hoja.write(y, 15, nomina['total_deducciones'], num_format)
                    hoja.write(y, 16, nomina['bono_agui_indem'], num_format)
                    hoja.write(y, 17, nomina['boni_incentivo_decreto'], num_format)
                    hoja.write(y, 18, nomina['dev_isr_otro'], num_format)
                    hoja.write(y, 19, nomina['liquido_recibir'], num_format)

                    y += 1
                    ordinario_total += nomina['ordinario']
                    extra_ordinario_total += nomina['extra_ordinario']
                    otros_salarios_total += nomina['otros_salarios']
                    septimo_asueto_total += nomina['septimos_asuetos']
                    vacaciones_total += nomina['vacaciones']
                    salario_total += nomina['total_salario_devengado']
                    igss_total += nomina['igss']
                    isr_total += nomina['isr']
                    otras_deducciones_total += nomina['otras_deducciones']
                    total_deducciones += nomina['total_deducciones']
                    bono_agui_indem_total += nomina['bono_agui_indem']
                    boni_incentivo_decreto_total += nomina['boni_incentivo_decreto']
                    dev_isr_otro_total += nomina['dev_isr_otro']
                    liquido_total += nomina['liquido_recibir']

                hoja.write(y, 6, ordinario_total, num_format_top)
                hoja.write(y, 7, extra_ordinario_total, num_format_top)
                hoja.write(y, 8, otros_salarios_total, num_format_top)
                hoja.write(y, 9, septimo_asueto_total, num_format_top)
                hoja.write(y, 10, vacaciones_total, num_format_top)
                hoja.write(y, 11, salario_total, num_format_top)
                hoja.write(y, 12, igss_total, num_format_top)
                hoja.write(y, 13, isr_total, num_format_top)
                hoja.write(y, 14, otras_deducciones_total, num_format_top)
                hoja.write(y, 15, total_deducciones, num_format_top)
                hoja.write(y, 16, bono_agui_indem_total, num_format_top)
                hoja.write(y, 17, boni_incentivo_decreto_total, num_format_top)
                hoja.write(y, 18, dev_isr_otro_total, num_format_top)
                hoja.write(y, 19, liquido_total, num_format_top)

            libro.close()
            datos = base64.b64encode(f.getvalue())
            self.write({'archivo': datos, 'name': 'Libro_salarios.xlsx'})

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'rrhh.libro_salarios',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }