# -*- coding: utf-8 -*-
{
    'name': 'Fabric Inspection Report (4-Point System)',
    'version': '18.0.1.0.3',
    'summary': 'Digitized Fabric Inspection Report (4-Point System) for Temakaw Fashion Ltd / K.A.W. Garments Industry Ltd',
    'description': """
Fabric Inspection Report - 4 Point System
==========================================
Digitizes the physical "Fabric Inspection Reports (4 point system)" form
(TFL-QMS-MCDQ-03-012) used by Temakaw Fashion Ltd / K.A.W. Garments Industry Ltd.

Features:
---------
* Header details: Buyer, Style, Color, Fabric Supplier, Fabric Item, Lot No,
  Inspection Qty, PKG, Received Rolls, Received Qty, Cutable Width.
* Roll-wise inspection lines with Ticket Qty / Actual Qty / Short-Excess,
  Cutable Width (1st / Middle / Last), LCR Shade, Running Shade, Pieces.
* Full defect capture: Shade bar, Foreign yarn, Crease marks, Dying fault,
  Slub, Knot, Hole, Spot/Stain, Missing Yarn (1/2/3/4 point) and
  Thick Yarn (1/2/3/4 point).
* Automatic 4-Point System calculations:
    - Total Point per roll
    - Points per 100 Sq. Yards = (Total Points x 3600) / (Width(inch) x Yards)
    - Average Point for the whole report
    - Automatic Pass / Fail result against a configurable threshold
* Sign-off workflow (Draft -> Confirmed -> Approved) with Prepared By,
  Quality/Inch, Cutting/Inch, T.M, QM and Merchandiser fields.
* Printable PDF report mirroring the original paper form.
* Dashboard-style list/kanban views with Pass/Fail color decoration.
""",
    'category': 'Manufacturing/Quality',
    'author': 'Nishu',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'security/fabric_inspection_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/fabric_inspection_report_views.xml',
        'views/fabric_inspection_line_views.xml',
        'views/menu.xml',
        'report/fabric_inspection_report_paperformat.xml',
        'report/fabric_inspection_report_template.xml',
        'report/report_actions.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
