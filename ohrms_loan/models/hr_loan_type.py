from odoo import models, fields, api, _


class HrLoanType(models.Model):
    _name = 'hr.loan.type'
    _description = "Loan Type"

    name = fields.Char(string="Loan Name Type", help="Name of the loan type")
    code = fields.Char(string="Codigo", help="Code")
