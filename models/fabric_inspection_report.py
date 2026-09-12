# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class FabricInspectionReport(models.Model):
    _name = 'fabric.inspection.report'
    _description = 'Fabric Inspection Report (4 Point System)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Report No.', required=True, copy=False,
        readonly=True, default=lambda self: ('New'))

    company_type = fields.Selection([
        ('temakaw', 'Temakaw Fashion Ltd'),
        ('kaw', 'K.A.W. Garments Industry Ltd'),
    ], string='Company', required=True, default='temakaw', tracking=True)

    form_reference = fields.Char(
        string='Form Reference', default='TFL-QMS-MCDQ-03-012', readonly=True)
    revision_no = fields.Char(string='Revision No.', default='1')
    revision_date = fields.Date(string='Revision Date')

    date = fields.Date(string='Date', required=True, default=fields.Date.context_today, tracking=True)
    fabric_type = fields.Char(string='Fabric Type', help='e.g. Shell Fabric, Lining, etc.')

    buyer = fields.Char(string='Buyer', tracking=True)
    style = fields.Char(string='Style')
    color = fields.Char(string='Color')
    fabric_supplier = fields.Char(string='Fabric Supplier')
    fabric_item = fields.Char(string='Fabric Item')
    lot_no = fields.Char(string='Lot No.')

    inspection_qty = fields.Float(string='Inspection Qty (Yds)', digits=(12, 2))
    pkg = fields.Integer(string='PKG')
    received_rolls = fields.Integer(string='Received Rolls')
    received_qty = fields.Float(string='Received Qty (Yds)', digits=(12, 2))
    found_cwidth = fields.Char(
        string='Found C-Width', compute='_compute_found_cwidth', store=True,
        help='Automatically derived from the narrowest roll width found across all '
             'inspected rolls (cutting is constrained by the narrowest roll).')
    is_cutable = fields.Boolean(
        string='Cutable', compute='_compute_found_cwidth', store=True,
        help='Automatically ticked once every roll in this report has a recorded width.')

    line_ids = fields.One2many(
        'fabric.inspection.line', 'report_id', string='Roll Inspection Lines', copy=True)

    roll_count = fields.Integer(string='No. of Rolls', compute='_compute_totals', store=True)
    total_point = fields.Integer(string='Total Point', compute='_compute_totals', store=True)
    total_actual_qty = fields.Float(string='Total Actual Qty (Yds)', compute='_compute_totals', store=True)
    average_point = fields.Float(string='Average Point', compute='_compute_totals', store=True, digits=(12, 2))
    average_points_100sqyd = fields.Float(
        string='Avg. Points / 100 Sq. Yds', compute='_compute_totals', store=True, digits=(12, 2))

    pass_threshold = fields.Float(
        string='Pass Threshold (Points/100 Sq.Yd)', default=28.0,
        help='Buyer-specific acceptance limit for the 4-point system (a contractual value, '
             'not something the fabric itself can tell us). Defaults to the industry-standard '
             '28 and auto-fills from this buyer\'s last report when you pick a Buyer, but you '
             'can always override it if this buyer/order requires a stricter or looser limit.')
    points_per_piece = fields.Integer(
        string='Points per Piece', default=4,
        help='Each "Piece" (join/splice) found in a roll is scored using this many points, '
             'per standard 4-point system rules (a splice is treated as a major flaw). '
             'Change this if a specific buyer uses a different rule.')

    computed_result = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Computed Result', compute='_compute_totals', store=True)

    manual_override_fail = fields.Boolean(
        string='Force Fail (e.g. Shading/Other)',
        help='Tick this to fail the lot for a reason not captured by the point '
             'calculation (e.g. shading issue), regardless of the computed points.')

    result = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Final Result', compute='_compute_result', store=True, tracking=True)

    comments = fields.Text(string='Comments')

    prepared_by = fields.Many2one('res.users', string='Prepared By', default=lambda self: self.env.user)
    quality_inch_id = fields.Many2one('res.users', string='Quality/Inch')
    cutting_inch_id = fields.Many2one('res.users', string='Cutting/Inch')
    tm_id = fields.Many2one('res.users', string='T.M')
    qm_id = fields.Many2one('res.users', string='QM')
    merchandiser_id = fields.Many2one('res.users', string='Merchandiser (MRCH)')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('approved', 'Approved'),
    ], string='Status', default='draft', tracking=True, copy=False)

    company_id = fields.Many2one(
        'res.company', string='Operating Company', default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'fabric.inspection.report') or 'New'
        return super().create(vals_list)

    @api.depends(
        'line_ids.total_point', 'line_ids.actual_qty', 'line_ids.points_per_100sqyd',
        'pass_threshold')
    def _compute_totals(self):
        for rec in self:
            lines = rec.line_ids
            rec.roll_count = len(lines)
            rec.total_point = sum(lines.mapped('total_point'))
            rec.total_actual_qty = sum(lines.mapped('actual_qty'))
            rec.average_point = (rec.total_point / rec.roll_count) if rec.roll_count else 0.0
            valid_lines = lines.filtered(lambda l: l.points_per_100sqyd)
            rec.average_points_100sqyd = (
                sum(valid_lines.mapped('points_per_100sqyd')) / len(valid_lines)
            ) if valid_lines else 0.0
            rec.computed_result = (
                'pass' if rec.average_points_100sqyd <= rec.pass_threshold else 'fail'
            ) if rec.roll_count else False

    @api.depends('line_ids.avg_width')
    def _compute_found_cwidth(self):
        for rec in self:
            widths = [w for w in rec.line_ids.mapped('avg_width') if w]
            if not widths:
                rec.found_cwidth = False
                rec.is_cutable = False
                continue
            min_w, max_w = min(widths), max(widths)
            if min_w == max_w:
                rec.found_cwidth = '%.2f"' % min_w
            else:
                # Cutting width is limited by the narrowest roll; show the full
                # range found so the range is visible, narrowest first.
                rec.found_cwidth = '%.2f" - %.2f"' % (min_w, max_w)
            # Cutable once every roll in the report has a recorded width.
            rec.is_cutable = len(widths) == len(rec.line_ids)

    @api.depends('computed_result', 'manual_override_fail')
    def _compute_result(self):
        for rec in self:
            if not rec.computed_result:
                rec.result = False
            elif rec.manual_override_fail:
                rec.result = 'fail'
            else:
                rec.result = rec.computed_result

    @api.onchange('buyer')
    def _onchange_buyer_pass_threshold(self):
        """Suggest this buyer's most recently used pass threshold, since the
        limit is a buyer/contract policy and not something derivable from the
        fabric data itself. The user can still override it freely."""
        if self.buyer:
            last_report = self.search([
                ('buyer', '=', self.buyer),
                ('id', '!=', self._origin.id),
            ], order='date desc, id desc', limit=1)
            if last_report:
                self.pass_threshold = last_report.pass_threshold

    def action_confirm(self):
        for rec in self:
            if not rec.line_ids:
                raise UserError('Please add at least one roll inspection line before confirming.')
            rec.state = 'confirmed'

    def action_approve(self):
        for rec in self:
            rec.state = 'approved'

    def action_reset_to_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_print_report(self):
        self.ensure_one()
        return self.env.ref(
            'fabric_inspection_report.action_report_fabric_inspection'
        ).report_action(self)
