# -*- encoding: utf-8 -*-
import locale
from odoo import api, models, fields
from datetime import datetime
from . import a_letras

class ReportRecibo(models.AbstractModel):
    _name = 'report.rrhh.contr_report_fire'
    _description = 'Repote contrato'

    def fecha_a_letras(self,date):
        if date:
            fecha = str(date)
            year, month, day = fecha.split("-")
            year = int(year)
            month = int(month)
            print(month,"month!!")
            day = int(day)
            date_in_words = self.a_letras(day)+" de "+a_letras.mes_a_letras(month)+" de "+self.a_letras(year)
            return date_in_words

    def formato_fecha(self, fecha):
        if fecha:
            mes = fecha.month
            print(mes,"mes")
            mes_letras = a_letras.mes_a_letras(mes)
            print(mes_letras,"mes!!")
            # Obtener el nombre del mes y formatear la fecha
            return fecha.strftime(f'%d de {mes_letras} de %Y')
        else:
            return ''

    def capitalize(self,text):
        return text.title()




    @api.model
    def _get_report_values(self, docids, data=None):
        model = 'hr.contract'
        # las planillas que se seleccionan en el lote
        docs = self.env[model].browse(docids)


        return {
            'doc_ids': docids,
            'doc_model': model,
            'docs': docs,
            'fecha_a_letras': self.fecha_a_letras,
            'formato_fecha': self.formato_fecha,
            'capitalize': self.capitalize,
        }
