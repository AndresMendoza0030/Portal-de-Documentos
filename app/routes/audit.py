from flask import Blueprint, render_template, redirect, url_for, request, session, send_from_directory, flash, current_app, Response
from datetime import datetime
from ..models import get_db_connection
import pandas as pd
from fpdf import FPDF
import os

bp = Blueprint('audit', __name__)

def get_auditoria_history(page, per_page, start_date=None, end_date=None, acciones=None, search_document=None, search_user=None):
    offset = (page - 1) * per_page
    conn = get_db_connection()
    query = 'SELECT id, fecha_subida, accion, documento, autor, version FROM auditoria WHERE 1=1'
    total_query = 'SELECT COUNT(*) FROM auditoria WHERE 1=1'
    params = []
    total_params = []

    if start_date and end_date:
        query += ' AND fecha_subida BETWEEN ? AND ?'
        total_query += ' AND fecha_subida BETWEEN ? AND ?'
        params.extend([start_date, end_date])
        total_params.extend([start_date, end_date])

    if acciones:
        query += ' AND (' + ' OR '.join(['accion = ?'] * len(acciones)) + ')'
        total_query += ' AND (' + ' OR '.join(['accion = ?'] * len(acciones)) + ')'
        params.extend(acciones)
        total_params.extend(acciones)

    if search_document:
        query += ' AND documento LIKE ?'
        total_query += ' AND documento LIKE ?'
        params.append(f'%{search_document}%')
        total_params.append(f'%{search_document}%')

    if search_user:
        query += ' AND autor LIKE ?'
        total_query += ' AND autor LIKE ?'
        params.append(f'%{search_user}%')
        total_params.append(f'%{search_user}%')

    query += ' ORDER BY fecha_subida DESC LIMIT ? OFFSET ?'
    params.extend([per_page, offset])

    registros = conn.execute(query, params).fetchall()
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
    acciones = request.args.getlist('acciones')
    search_document = request.args.get('search_document')
    search_user = request.args.get('search_user')

    registros, total = get_auditoria_history(page, per_page, start_date, end_date, acciones, search_document, search_user)
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
        col_widths = [40, 30, 150, 40, 20]
        col_headers = ['Fecha de Subida', 'Acción', 'Documento', 'Autor', 'Versión']

        for col_header, col_width in zip(col_headers, col_widths):
            self.cell(col_width, 10, col_header, 1)

        self.ln()

        self.set_font('Arial', '', 10)
        for registro in registros:
            self.cell(col_widths[0], 10, registro['fecha_subida'], 1)
            self.cell(col_widths[1], 10, registro['accion'], 1)
            self.cell(col_widths[2], 10, registro['documento'], 1)
            self.cell(col_widths[3], 10, registro['autor'], 1)
            self.cell(col_widths[4], 10, str(registro['version']), 1)
            self.ln()

@bp.route('/auditoria/export/pdf')
def export_auditoria_pdf():
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    acciones = request.args.getlist('acciones')
    search_document = request.args.get('search_document')
    search_user = request.args.get('search_user')
    filename_pdf = request.args.get('filename_pdf', 'auditoria.pdf')

    conn = get_db_connection()
    query = 'SELECT fecha_subida, accion, documento, autor, version FROM auditoria WHERE 1=1'
    params = []

    if start_date and end_date and start_date != 'None' and end_date != 'None':
        query += ' AND fecha_subida BETWEEN ? AND ?'
        params.extend([start_date, end_date])
    if acciones:
        query += ' AND (' + ' OR '.join(['accion = ?'] * len(acciones)) + ')'
        params.extend(acciones)
    if search_document:
        query += ' AND documento LIKE ?'
        params.append(f'%{search_document}%')
    if search_user:
        query += ' AND autor LIKE ?'
        params.append(f'%{search_user}%')

    query += ' ORDER BY fecha_subida DESC'

    registros = conn.execute(query, params).fetchall()
    conn.close()

    pdf = PDF('L', 'mm', 'A4')
    pdf.add_page()
    pdf.add_table(registros)

    response = Response(pdf.output(dest='S').encode('latin1'), mimetype='application/pdf')
    response.headers['Content-Disposition'] = f'attachment; filename={filename_pdf}'
    return response

@bp.route('/auditoria/export/excel')
def export_auditoria_excel():
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    acciones = request.args.getlist('acciones')
    search_document = request.args.get('search_document')
    search_user = request.args.get('search_user')
    filename_excel = request.args.get('filename_excel', 'auditoria.xlsx')

    conn = get_db_connection()
    query = 'SELECT fecha_subida, accion, documento, autor, version FROM auditoria WHERE 1=1'
    params = []

    if start_date and end_date and start_date != 'None' and end_date != 'None':
        query += ' AND fecha_subida BETWEEN ? AND ?'
        params.extend([start_date, end_date])
    if acciones:
        query += ' AND (' + ' OR '.join(['accion = ?'] * len(acciones)) + ')'
        params.extend(acciones)
    if search_document:
        query += ' AND documento LIKE ?'
        params.append(f'%{search_document}%')
    if search_user:
        query += ' AND autor LIKE ?'
        params.append(f'%{search_user}%')

    query += ' ORDER BY fecha_subida DESC'

    registros = conn.execute(query, params).fetchall()
    conn.close()

    df = pd.DataFrame(registros, columns=['fecha_subida', 'accion', 'documento', 'autor', 'version'])
    output = os.path.join(current_app.config['TEMP_FOLDER'], filename_excel)
    df.to_excel(output, index=False, sheet_name='Auditoria')

    return send_from_directory(current_app.config['TEMP_FOLDER'], filename_excel, as_attachment=True)
