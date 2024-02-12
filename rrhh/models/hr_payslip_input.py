from odoo import fields, models


class CustomHrPayslipInput(models.Model):
    _inherit = "hr.payslip.input"

    input_type_id = fields.Many2one('hr.payslip.input.type.2', string='Type', required=False)
    # Add more fields as needed

    contract_id = fields.Many2one(
        "hr.contract",
        string="Contract",
        required=False,
        help="The contract for which applied this input",
    )
