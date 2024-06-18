from flask import Blueprint, render_template, redirect, url_for, request, session, send_from_directory, flash, current_app, Response, jsonify
from datetime import datetime
from ..models import get_db_connection
import pandas as pd
from fpdf import FPDF
import os

bp = Blueprint('audit', __name__)

def get_auditoria_history(page, per_page, start_date=None, end_date=None):
    offset = (page - 1) * per_page
    conn = get_db_connection()
    query = 'SELECT * FROM auditoria'
    params = []

    if start_date and end_date:
        query += ' WHERE fecha_subida BETWEEN ? AND ?'
        params.extend([start_date, end_date])

    query += ' ORDER BY fecha_subida DESC LIMIT ? OFFSET ?'
    params.extend([per_page, offset])

    registros = conn.execute(query, params).fetchall()
    total_query = 'SELECT COUNT(*) FROM auditoria'
    if start_date and end_date:
        total_query += ' WHERE fecha_subida BETWEEN ? AND ?'
        total_params = [start_date, end_date]
    else:
        total_params = []

    total = conn.execute(total_query, total_params).fetchone()[0]
    conn.close()
    return registros, total

@bp.route('/auditoria')
def auditoria():
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))

    page = request.args.get('page', 1, type=int)
    per_page = 10
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    registros, total = get_auditoria_history(page, per_page, start_date, end_date)
    return render_template('auditoria.html', registros=registros, total=total, page=page, per_page=per_page)

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Historial de Auditoría', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def add_table(self, registros):
        self.set_font('Arial', 'B', 10)
        col_widths = [40, 80, 20, 40, 20, 15]
        col_headers = ['Fecha de Subida', 'Documento', 'Autor', 'Fecha de Edición', 'Usuario', 'Versión']

        for col_header, col_width in zip(col_headers, col_widths):
            self.cell(col_width, 10, col_header, 1)

        self.ln()

        self.set_font('Arial', '', 10)
        for registro in registros:
            self.cell(col_widths[0], 10, registro['fecha_subida'], 1)
            self.cell(col_widths[1], 10, registro['documento'], 1)
            self.cell(col_widths[2], 10, registro['autor'], 1)
            self.cell(col_widths[3], 10, str(registro['fecha_edicion']), 1)
            self.cell(col_widths[4], 10, str(registro['usuario']), 1)
            self.cell(col_widths[5], 10, str(registro['version']), 1)
            self.ln()

@bp.route('/auditoria/export/pdf')
def export_auditoria_pdf():
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    conn = get_db_connection()
    query = 'SELECT * FROM auditoria'
    params = []

    if start_date and end_date:
        query += ' WHERE fecha_subida BETWEEN ? AND ?'
        params.extend([start_date, end_date])

    registros = conn.execute(query, params).fetchall()
    conn.close()

    pdf = PDF('L', 'mm', 'A4')
    pdf.add_page()
    pdf.add_table(registros)

    response = Response(pdf.output(dest='S').encode('latin1'), mimetype='application/pdf')
    response.headers['Content-Disposition'] = 'attachment; filename=auditoria.pdf'
    return response

@bp.route('/auditoria/export/excel')
def export_auditoria_excel():
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    conn = get_db_connection()
    query = 'SELECT * FROM auditoria'
    params = []

    if start_date and end_date:
        query += ' WHERE fecha_subida BETWEEN ? AND ?'
        params.extend([start_date, end_date])

    registros = conn.execute(query, params).fetchall()
    conn.close()

    df = pd.DataFrame(registros, columns=['id', 'fecha_subida', 'documento', 'autor', 'fecha_edicion', 'usuario', 'version'])
    output = os.path.join(current_app.config['TEMP_FOLDER'], 'auditoria.xlsx')
    df.to_excel(output, index=False, sheet_name='Auditoria')

    return send_from_directory(current_app.config['TEMP_FOLDER'], 'auditoria.xlsx', as_attachment=True)
