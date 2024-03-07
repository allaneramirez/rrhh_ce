# -*- encoding: utf-8 -*-
import locale
from odoo import api, models, fields
import datetime
import pytz
from . import a_letras

class ReportRecibo(models.AbstractModel):
    _name = 'report.rrhh.contr_report_record_resig'
    _description = 'Repote contrato'

    def fecha_a_letras(self,date):
        if date:
            fecha = str(date)
            year, month, day = fecha.split("-")
            year = int(year)
            month = int(month)
            day = int(day)
            date_in_words = self.a_letras(day)+" de "+a_letras.mes_a_letras(month)+" de "+self.a_letras(year)
            return date_in_words

    def salario_formateado(self,salario):
        salario_formateado = "Q{:,.2f}".format(salario)
        return salario_formateado

    def formato_fecha(self, fecha):
        if fecha:
            mes = fecha.month
            mes_letras = a_letras.mes_a_letras(mes)
            # Obtener el nombre del mes y formatear la fecha
            return fecha.strftime(f'%d de {mes_letras} de %Y')
        else:
            return ''

    def a_letras(self,amount):
        return a_letras.num_a_letras(amount)

    def a_mes(self, number):
        return a_letras.mes_a_letras(number)

    def date_text(self):
        fecha_actual_utc = datetime.datetime.utcnow()

        # Obtener la zona horaria local del sistema
        zona_horaria_local = datetime.timezone(
            datetime.timedelta(hours=-6))

        fecha_actual_local = fecha_actual_utc.replace(tzinfo=datetime.timezone.utc).astimezone(zona_horaria_local)
        print(fecha_actual_local, "actual")
        fecha_hora = datetime.datetime.strptime(str(fecha_actual_local), "%Y-%m-%d %H:%M:%S.%f%z")
        year = fecha_hora.year
        mes = fecha_hora.month
        dia = fecha_hora.day
        print(mes,"mes")
        text = f" los {a_letras.num_a_letras(dia)} días del mes de {a_letras.mes_a_letras(mes)} de {a_letras.num_a_letras(year)}."
        return text




    @api.model
    def _get_report_values(self, docids, data=None):
        model = 'hr.contract'
        # los contratos que se seleccionan en el lote
        docs = self.env[model].browse(docids)


        return {
            'doc_ids': docids,
            'doc_model': model,
            'docs': docs,
            'fecha_a_letras': self.fecha_a_letras,
            'formato_fecha': self.formato_fecha,
            'date_text': self.date_text,
            'salario_formateado': self.salario_formateado,
        }
