# -*- coding: utf-8 -*-
from odoo import api, fields, models


class FabricInspectionLine(models.Model):
    _name = 'fabric.inspection.line'
    _description = 'Fabric Inspection Line (Roll-wise)'
    _order = 'sequence, id'

    report_id = fields.Many2one(
        'fabric.inspection.report', string='Inspection Report',
        required=True, ondelete='cascade')
    sequence = fields.Integer(string='Seq', default=10)

    roll_no = fields.Char(string='Roll No.', required=True)
    ticket_qty = fields.Float(string='Ticket Qty (Yds)', digits=(12, 2))
    actual_qty = fields.Float(string='Actual Qty (Yds)', digits=(12, 2))
    short_excess = fields.Float(
        string='Short/Excess', compute='_compute_short_excess', store=True, digits=(12, 2))

    width_first = fields.Float(string='Width - 1st (inch)', digits=(6, 2))
    width_middle = fields.Float(string='Width - Middle (inch)', digits=(6, 2))
    width_last = fields.Float(string='Width - Last (inch)', digits=(6, 2))
    avg_width = fields.Float(
        string='Avg. Width (inch)', compute='_compute_avg_width', store=True, digits=(6, 2))

    lcr_shade = fields.Boolean(string='LCR Shade')
    running_shade = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Running Shade')
    pieces = fields.Integer(
        string='Pieces', help='Number of joins/splices (piece-marks) found in this roll. '
                               'Each piece is scored using the report\'s "Points per Piece" '
                               'setting (4 points by default, per standard 4-point system rules).')

    # --- Defects captured directly as points on the roll ---
    shade_bar = fields.Integer(string='Shade Bar', default=0)
    foreign_yarn = fields.Integer(string='Foreign Yarn', default=0)
    crease_marks = fields.Integer(string='Crease Marks', default=0)
    dying_fault = fields.Integer(string='Dying Fault', default=0)
    slub = fields.Integer(string='Slub', default=0)
    knot = fields.Integer(string='Knot', default=0)
    hole = fields.Integer(string='Hole', default=0)
    spot_stain = fields.Integer(string='Spot / Stain', default=0)

    # --- Missing Yarn: count of occurrences at each point-tier ---
    missing_yarn_1pt = fields.Integer(string='Missing Yarn - 1 Point', default=0)
    missing_yarn_2pt = fields.Integer(string='Missing Yarn - 2 Point', default=0)
    missing_yarn_3pt = fields.Integer(string='Missing Yarn - 3 Point', default=0)
    missing_yarn_4pt = fields.Integer(string='Missing Yarn - 4 Point', default=0)

    # --- Thick Yarn: count of occurrences at each point-tier ---
    thick_yarn_1pt = fields.Integer(string='Thick Yarn - 1 Point', default=0)
    thick_yarn_2pt = fields.Integer(string='Thick Yarn - 2 Point', default=0)
    thick_yarn_3pt = fields.Integer(string='Thick Yarn - 3 Point', default=0)
    thick_yarn_4pt = fields.Integer(string='Thick Yarn - 4 Point', default=0)

    missing_yarn_points = fields.Integer(
        string='Missing Yarn Points', compute='_compute_points', store=True)
    thick_yarn_points = fields.Integer(
        string='Thick Yarn Points', compute='_compute_points', store=True)
    pieces_points = fields.Integer(
        string='Pieces Points', compute='_compute_points', store=True)

    total_point = fields.Integer(
        string='Total Point', compute='_compute_points', store=True)
    points_per_100sqyd = fields.Float(
        string='Points / 100 Sq. Yds', compute='_compute_points', store=True, digits=(12, 2))

    pass_threshold = fields.Float(
        string='Pass Threshold', related='report_id.pass_threshold', store=False)
    line_result = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Result', compute='_compute_points', store=True)

    comments = fields.Char(string='Remarks')

    @api.depends('ticket_qty', 'actual_qty')
    def _compute_short_excess(self):
        for line in self:
            line.short_excess = (line.actual_qty or 0.0) - (line.ticket_qty or 0.0)

    @api.depends('width_first', 'width_middle', 'width_last')
    def _compute_avg_width(self):
        for line in self:
            widths = [w for w in (line.width_first, line.width_middle, line.width_last) if w]
            line.avg_width = (sum(widths) / len(widths)) if widths else 0.0

    @api.depends(
        'shade_bar', 'foreign_yarn', 'crease_marks', 'dying_fault', 'slub', 'knot',
        'hole', 'spot_stain', 'pieces',
        'missing_yarn_1pt', 'missing_yarn_2pt', 'missing_yarn_3pt', 'missing_yarn_4pt',
        'thick_yarn_1pt', 'thick_yarn_2pt', 'thick_yarn_3pt', 'thick_yarn_4pt',
        'avg_width', 'actual_qty', 'report_id.pass_threshold', 'report_id.points_per_piece')
    def _compute_points(self):
        for line in self:
            line.missing_yarn_points = (
                line.missing_yarn_1pt * 1 + line.missing_yarn_2pt * 2 +
                line.missing_yarn_3pt * 3 + line.missing_yarn_4pt * 4
            )
            line.thick_yarn_points = (
                line.thick_yarn_1pt * 1 + line.thick_yarn_2pt * 2 +
                line.thick_yarn_3pt * 3 + line.thick_yarn_4pt * 4
            )
            points_per_piece = line.report_id.points_per_piece or 4
            line.pieces_points = line.pieces * points_per_piece
            line.total_point = (
                line.shade_bar + line.foreign_yarn + line.crease_marks +
                line.dying_fault + line.slub + line.knot + line.hole +
                line.spot_stain + line.missing_yarn_points + line.thick_yarn_points +
                line.pieces_points
            )
            if line.avg_width and line.actual_qty:
                # Standard 4-Point System formula:
                # Points/100 sq.yd = (Total Points x 3600) / (Width(inch) x Yards)
                line.points_per_100sqyd = (
                    line.total_point * 3600.0) / (line.avg_width * line.actual_qty)
            else:
                line.points_per_100sqyd = 0.0

            threshold = line.report_id.pass_threshold or 28.0
            if line.avg_width and line.actual_qty:
                line.line_result = 'pass' if line.points_per_100sqyd <= threshold else 'fail'
            else:
                line.line_result = False
