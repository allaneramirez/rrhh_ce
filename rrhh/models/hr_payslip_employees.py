from odoo import _, fields, models, api
from odoo.exceptions import UserError


class HrPayslipEmployees(models.TransientModel):
    _inherit = "hr.payslip.employees"


    employee_ids = fields.Many2many(
        "hr.employee", "hr_employee_group_rel", "payslip_id", "employee_id", "Employees"
    )
    department_id = fields.Many2one('hr.department', string='Department')

    @api.onchange('department_id')
    def _onchange_department_id(self):
        if self.department_id:
            department_ids = self.env['hr.department'].search([('id', 'child_of', self.department_id.id)]).ids
            employees = self.env['hr.employee'].search([('department_id', 'in', department_ids)])
            self.employee_ids = [(6, 0, employees.ids)]
        else:
            self.employee_ids = [(5,)]

    def compute_sheet(self):
        payslips = self.env["hr.payslip"]
        [data] = self.read()
        active_id = self.env.context.get("active_id")
        if active_id:
            [run_data] = (
                self.env["hr.payslip.run"]
                .browse(active_id)
                .read(["date_start", "date_end", "credit_note", "struct_id","slip_ids"])
            )
        from_date = run_data.get("date_start")
        to_date = run_data.get("date_end")
        struct_id = run_data.get("struct_id")
        slip_ids = run_data.get("slip_ids")
        if not struct_id:
            raise UserError(_("Seleccionar una estructura salarial"))
        if not data["employee_ids"]:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))

        # Limpiar todos los slip_ids antes de iterar
        payslips_to_reset = self.env['hr.payslip'].search([('id', 'in', slip_ids)])
        if payslips_to_reset:
            # Cambiar el estado de las liquidaciones a 'Borrador' para poder eliminarlos
            payslips_to_reset.write({'state': 'draft'})
            payslips_to_reset.unlink()
        employees = self.env['hr.employee'].search([('department_id', '=', self.department_id.id)])

        for employee in employees:
            slip_data = self.env["hr.payslip"].get_payslip_vals(
                from_date, to_date, employee.id, contract_id=False, struct_id=struct_id
            )
            res = {
                "employee_id": employee.id,
                "name": slip_data["value"].get("name"),
                "struct_id": struct_id[0],
                "contract_id": slip_data["value"].get("contract_id"),
                "payslip_run_id": active_id,
                "input_line_ids": [
                    (0, 0, x) for x in slip_data["value"].get("input_line_ids")
                ],
                "worked_days_line_ids": [
                    (0, 0, x) for x in slip_data["value"].get("worked_days_line_ids")
                ],
                "date_from": from_date,
                "date_to": to_date,
                "credit_note": run_data.get("credit_note"),
                "company_id": employee.company_id.id,
            }
            payslips += self.env["hr.payslip"].create(res)

        payslips._compute_name()
        payslips.compute_sheet()

        return {"type": "ir.actions.act_window_close"}
