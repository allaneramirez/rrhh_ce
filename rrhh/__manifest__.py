# -*- coding: utf-8 -*-
{
    'name': "RRHH",
    'summary': """ Módulo de RRHH para Guatemala """,

    'description': """
        Módulo de RRHH para Guatemala
    """,

    'author': "Alexander Garzo",
    'website': "http://www.integrall.solutions",

    'category': 'Uncategorized',
    'version': '14.0.0.0',

    'depends': ['base', 'hr', 'hr_contract', 'l10n_gt_extra','payroll'],

    'data': [
        'security/ir.model.access.csv',
        'data/rrhh_data.xml',
        'views/payslip_input_type_view.xml',
        'views/hr_contract_views.xml',
        'views/hr_views.xml',
        'views/payslip_run_form.xml',
        'views/planilla_views.xml',
        'views/report.xml',
        'views/recibo.xml',
        'views/hr_payslip_view.xml',
        'wizard/entradas_planillas_wizard.xml',
        'wizard/planilla.xml',
        'wizard/payslip_employees_view.xml',
        'wizard/payslip_employees_view.xml',
],
    'license': 'LGPL-3',
}
