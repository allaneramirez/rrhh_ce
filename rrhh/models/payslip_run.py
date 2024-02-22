from odoo import models, fields, api

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'
    payslip_count = fields.Integer(compute='_compute_payslip_count')

    def _compute_payslip_count(self):
        for payslip_run in self:
            payslip_run.payslip_count = len(payslip_run.slip_ids)
    def action_open_payslips(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.payslip",
            "views": [[False, "tree"], [False, "form"]],
            "domain": [['id', 'in', self.slip_ids.ids]],
            "context": {'default_payslip_run_id': self.id},
            "name": "Payslips",
        }

