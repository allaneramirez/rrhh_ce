# -*- encoding: utf-8 -*-
import locale
from odoo import api, models, fields
from datetime import datetime

class ReportRecibo(models.AbstractModel):
    _name = 'report.rrhh.recibo'
    _description = 'Repote recibo'

    def lineas(self, o):
        result = {'lineas': [], 'totales': [0, 0, 0]}
        if o.payslip_run_id.recibo_id:
            ##### Todas de la nomina ####
            lineas_reglas = {}
            # iteramos sobre las reglas salariales en la nomina
            for l in o.line_ids:
                if l.salary_rule_id.id not in lineas_reglas:
                    # lo agregamos al diccionario
                    lineas_reglas[l.salary_rule_id.id] = 0
                # acomulamos el valor segun la regla salarial
                lineas_reglas[l.salary_rule_id.id] += l.total
            entradas = {}
            # iteramos sobre las entradas de la nomina
            for l in o.input_line_ids:
                # buscamos en el modelo de tipo de otros tipos entradas
                input_id = self.env['hr.payslip.input.type.2'].search([('code', '=', l.code )])
                if len(input_id):
                    if input_id[0].code not in entradas:
                        entradas[input_id[0].code] = 0
                    # acumulamos el valor de otro tipo de entrada
                    entradas[input_id[0].code] += l.amount
            ### solo sobre las lineas del recibo
            recibo = o.payslip_run_id.recibo_id
            lineas_ingresos = []
            # iteramos sobre cada linea de tipo ingreso presente en el recibo
            for li in recibo.linea_ingreso_id:
                datos = {'nombre': li.name, 'total': 0}
                # iteramos sobre cada regla presente en el recibo de tipo ingreso
                for r in li.regla_id:
                    datos['total'] += lineas_reglas.get(r.id, 0)
                    # agregamos al resultoado totales en el primer index, las entradas
                    result['totales'][0] += lineas_reglas.get(r.id, 0)
                lineas_ingresos.append(datos)

            # lo  mismo que lo anterior pero acumulando las deducciones
            lineas_deducciones = []
            for ld in recibo.linea_deduccion_id:
                datos = {'nombre': ld.name, 'total': 0}
                for r in ld.regla_id:
                    datos['total'] += lineas_reglas.get(r.id, 0)
                    # segundo index
                    result['totales'][1] += lineas_reglas.get(r.id, 0)
                lineas_deducciones.append(datos)

            lineas_entradas = []
            # iteramos sobre todas las entradas presente en el recibo
            # for entrada in recibo.entrada_id:
            #     datos = {'nombre': entrada.input_id.name, 'total': 0}
            #     datos['total'] = entradas.get(entrada.input_id.code, 0)
            #     result['totales'][2] += entradas.get(entrada.input_id.code, 0)
            #     # acumulamos todo lo de las otras entradas
            #     lineas_entradas.append(datos)
            largo = max(len(lineas_ingresos), len(lineas_deducciones), len(lineas_entradas))
            lineas_ingresos += [None] * (largo - len(lineas_ingresos))
            lineas_deducciones += [None] * (largo - len(lineas_deducciones))
            lineas_entradas += [None] * (largo - len(lineas_entradas))
            result['lineas'] = zip(lineas_ingresos, lineas_deducciones, lineas_entradas)

        return result
    def formato_fecha(self, fecha):
        if fecha:
            # Configurar la localización a español
            locale.setlocale(locale.LC_TIME, 'es_ES.utf-8')

            # Obtener el nombre del mes y formatear la fecha
            return fecha.strftime('%d de %B de %Y')
        else:
            return ''


    @api.model
    def _get_report_values(self, docids, data=None):
        model = 'hr.payslip'
        # las planillas que se seleccionan en el lote
        docs = self.env[model].browse(docids)
        current_year = datetime.now().year
        previous_year = current_year - 1
        current_day = datetime.now().day

        # Configurar la localización a español
        locale.setlocale(locale.LC_TIME, 'es_ES.utf-8')

        # Obtener el nombre del mes
        current_month_in_words = datetime.now().strftime('%B')

        return {
            'doc_ids': docids,
            'doc_model': model,
            'docs': docs,
            'lineas': self.lineas,
            'formato_fecha': self.formato_fecha,
            'index_range': range(len(docs)),
            'current_year': current_year,
            'previous_year': previous_year,
            'current_day': current_day,
            'current_month_in_words': current_month_in_words,
        }
