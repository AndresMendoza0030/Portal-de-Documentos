from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from ..models import  submit_feedback
bp = Blueprint('ayuda', __name__)

@bp.route('/ayuda')
def ayuda():
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))
    return render_template('ayuda.html')

@bp.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))

    feedback = request.form['feedback']
    # Aquí llamas a la función para guardar el feedback en la base de datos o enviarlo por correo
    save_feedback(session['username'], feedback)
    flash('Gracias por tu retroalimentación.')
    return redirect(url_for('ayuda.ayuda'))

def save_feedback(username, feedback):
    # Implementa esta función para guardar el feedback en la base de datos
    pass
