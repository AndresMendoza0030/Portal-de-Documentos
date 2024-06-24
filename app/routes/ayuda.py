import os
from flask import Blueprint, render_template, session,send_from_directory, redirect, url_for, request, flash, current_app
from werkzeug.utils import secure_filename
from ..models import submit_feedback, get_feedback
from config import Config
bp = Blueprint('ayuda', __name__)

@bp.route('/ayuda')
def ayuda():
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))
    
    feedback_entries = []
    if session.get('role') == 'admin':  # Suponiendo que tienes un campo de rol en la sesión
        feedback_entries = get_feedback()
    
    return render_template('ayuda.html', feedback_entries=feedback_entries)

@bp.route('/submits_feedback', methods=['POST'])
def submits_feedback():
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))

    feedback = request.form['feedback']
    capture = request.files.get('capture')

    if capture and capture.filename != '':
        filename = secure_filename(capture.filename)
        capture_path = os.path.join(current_app.config['CAPTURES_FOLDER'], filename)
        capture.save(capture_path)
    else:
        filename = None

    submit_feedback(session['username'], feedback, filename)
    flash('Gracias por tu retroalimentación.')
    return redirect(url_for('ayuda.ayuda'))
@bp.route('/captures/<filename>')
def get_capture(filename):
    return send_from_directory(current_app.config['CAPTURES_FOLDER'], filename)