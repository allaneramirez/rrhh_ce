# -*- encoding: utf-8 -*-
import locale
from odoo import api, models, fields
import datetime
import pytz
from . import a_letras

class ReportRecibo(models.AbstractModel):
    _name = 'report.rrhh.vac_report'
    _description = 'Repote contrato'

    def salario_formateado(self,salario):
        salario_formateado = "Q{:,.2f}".format(salario)
        return salario_formateado


    @api.model
    def _get_report_values(self, docids, data=None):
        model = 'hr.payslip'
        # los contratos que se seleccionan en el lote
        docs = self.env[model].browse(docids)
        docs_filterd = docs.filtered(lambda doc: doc.line_ids.filtered(lambda line: line.salary_rule_id.code == "VAC"))
        print(docs_filterd)


        return {
            'doc_ids': docids,
            'doc_model': model,
            'docs': docs_filterd,
            'salario_formateado': self.salario_formateado,
        }
