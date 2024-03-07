# -*- encoding: utf-8 -*-
import locale
from odoo import api, models, fields
from datetime import datetime
from . import a_letras
import math

class ReportRecibo(models.AbstractModel):
    _name = 'report.rrhh.contr_report'
    _description = 'Repote contrato'


    def a_letras(self,amount):

        return a_letras.num_a_letras(amount)

    def fecha_a_letras(self,date):
        if date:
            fecha = str(date)
            year, month, day = fecha.split("-")
            year = int(year)
            month = int(month)
            day = int(day)
            date_in_words = self.a_letras(day)+" de "+a_letras.mes_a_letras(month)+" de "+self.a_letras(year)
            return date_in_words

    def salario_a_letras(self,amount):
        return a_letras.salario_a_letras(amount)
    def formato_fecha(self, fecha):
        if fecha:
            # # Configurar la localización a español
            # locale.setlocale(locale.LC_TIME, 'es_ES.utf-8')

            # Obtener el nombre del mes y formatear la fecha
            return fecha.strftime('%d de %B de %Y')
        else:
            return ''

    def salario_formateado(self,salario):
        salario_formateado = "Q{:,.2f}".format(salario)
        return salario_formateado

    def horarios(self, dep):
        if dep.lower() == 'planta':
            return ('De las jornadas de trabajo DIURNA CONTINUA: '
                    'será de 8 horas diarias y 44 horas a la semana así: de 7:00 am a 15:00 horas, '
                    'excepto el día sábado que será de las 7:00 am horas hasta las 11:00 '
                    'horas para completar las 44 horas de la semana, NOCTURNA: será de 6 horas '
                    'diarias y 36 horas a la semana así: de 18:00 pm a 24:00 pm horas para '
                    'completar las 36 horas de la semana.')
        else:
            return ('5o. De las jornadas de trabajo DIURNA CONTINUA: será de 8 horas diarias '
                    'y 44 horas a la semana así: de 7:30 am a 16:30 horas, excepto el día sábado '
                    'que será de las 8:00 am horas hasta las 11:00 horas para completar las 44 horas '
                    'de la semana. Si por conveniencia se pactare otro horario de ingreso con su jefe '
                    'inmediato o bien de salida este horario debe de respetar la normativa legal '
                    'completando las 44 horas de trabajo semanales, y un día de descanso remunerado. ')
        # jornadas_text = 'De las jornadas de trabajo '
        # for calendar in horarios:
        #
        #     jornadas_text += calendar.name+":"
        #     lunes = calendar.attendance_ids.filtered(lambda att: 'lunes' in att.name.lower())
        #     sabado = calendar.attendance_ids.filtered(lambda att: 'sabado' in att.name.lower())
        #     print()
        #     print(sabado,"sabadoo!!")
        #
        #     from_hours = []
        #     to_hours = []
        #
        #     horas_diarias = 0
        #     for att in lunes:
        #         horas_diarias += att.hour_to - att.hour_from
        #         from_hours.append(att.hour_from)
        #         to_hours.append(att.hour_to)
        #     print(horas_diarias,"diarias!")
        #     horas_diarias = math.ceil(horas_diarias)
        #
        #     horas_semanales = 0
        #     for att in calendar.attendance_ids:
        #         horas_semanales += att.hour_to - att.hour_from
        #     print(horas_semanales,"semanales!")
        #     horas_semanales = math.ceil(horas_semanales)
        #
        #     jornadas_text += f' será de {int(horas_diarias)} horas diarias y {int(horas_semanales)} horas a la semana así: '
        #     primer_ciclo = True
        #     for fromh, toh in zip(from_hours,to_hours):
        #         if primer_ciclo:
        #             jornadas_text += f'de {"{:.0f}:00".format(fromh)} a {"{:.0f}:00".format(toh)}'
        #             primer_ciclo = False
        #         else:
        #             jornadas_text += f' y de {"{:.0f}:00".format(fromh)} a {"{:.0f}:00".format(toh)} horas'
        #
        #     if sabado and calendar.name.lower() != 'nocturna':
        #         for att in sabado:
        #             jornadas_text += f' excepto el día sábado que será de las {att.hour_from} am horas hasta las {att.hour_to} horas'
        #
        #     jornadas_text += f' para completar las {int(horas_semanales)} horas de la semana. '

        return jornadas_text

    def gender(self,gender):
        if gender == 'male':
            return 'masculino'
        else:
            return 'femenino'

    def marital(self,marital):
        if marital == "single":
            return 'soltero'
        else:
            return 'casado'

    def nationality(self, gender):
        if gender == 'male':
            return 'guatemalteco'
        else:
            return 'guatemalteca'



    @api.model
    def _get_report_values(self, docids, data=None):
        model = 'hr.contract'
        # las planillas que se seleccionan en el lote
        docs = self.env[model].browse(docids)
        # current_year = datetime.now().year
        # previous_year = current_year - 1
        # current_day = datetime.now().day
        #
        current_month_in_words = datetime.now().strftime('%B')

        return {
            'doc_ids': docids,
            'doc_model': model,
            'docs': docs,
            'a_letras': self.a_letras,
            'fecha_a_letras': self.fecha_a_letras,
            'salario_a_letras': self.salario_a_letras,
            'salario_formateado': self.salario_formateado,
            'horarios': self.horarios,
            'nationality': self.nationality,
            'marital': self.marital,
            'gender': self.gender,
            # 'formato_fecha': self.formato_fecha,
            'index_range': range(len(docs)),
            'current_month_in_words': current_month_in_words,
        }
