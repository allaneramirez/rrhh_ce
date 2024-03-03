# -*- encoding: utf-8 -*-
import locale
from odoo import api, models, fields
from . import a_letras


class PrestReport(models.AbstractModel):
    _name = 'report.ohrms_loan.prest_report'
    _description = 'Repote Prestaciones'

    def salario_formateado(self,salario):
        salario_formateado = "Q{:,.2f}".format(salario)
        return salario_formateado
    def area(self,area):
        print(area,"area")

    def a_letras(self,amount):
        return a_letras.num_a_letras(amount)

    def planilla(self,pl):
        if pl == 'b14':
            return 'bono 14'
        else:
            return 'aguinaldo'

    def marital(self,marital):
        print(marital,"mari!!")
        if marital == 1:
            return 'soltero(a)'
        elif marital == 2:
            return 'casado(a)'
        elif marital == 3:
            return 'unido(a)'
        else:
            return 'sin codigo'

    def fecha_a_letras(self,date):
        print(date,"datee!!!!!")
        if date:
            fecha = str(date)
            year, month, day = fecha.split("-")
            year = int(year)
            month = int(month)
            day = int(day)
            date_in_words = self.a_letras(day)+" de "+a_letras.mes_a_letras(month)+" de "+self.a_letras(year)
            return date_in_words
        else: return 'No hay fecha'

    def salario_a_letras(self,amount):
        return a_letras.salario_a_letras(amount)

    @api.model
    def _get_report_values(self, docids, data=None):
        model = 'hr.loan'
        # los contratos que se seleccionan en el lote
        docs = self.env[model].browse(docids)


        return {
            'doc_ids': docids,
            'doc_model': model,
            'docs': docs,
            'salario_formateado': self.salario_formateado,
            'area': self.area,
            'a_letras': self.a_letras,
            'marital': self.marital,
            'fecha_a_letras': self.fecha_a_letras,
            'salario_a_letras': self.salario_a_letras,
            'planilla': self.planilla,
        }
