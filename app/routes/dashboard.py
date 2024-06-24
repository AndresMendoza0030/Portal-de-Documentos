from flask import Blueprint, render_template, session, redirect, url_for, request, flash, current_app
from ..models import get_recent_documents, get_notifications, get_user_tasks, get_favorite_documents, get_shared_documents, add_user_task, get_user_events, submit_feedback
from datetime import datetime
import os
from config import Config
bp = Blueprint('dashboard', __name__)
from werkzeug.utils import secure_filename
@bp.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))

    recent_documents = get_recent_documents(session['username'])
    notifications = get_notifications(session['username'])
    user_tasks = get_user_tasks(session['username'])
    favorite_documents = get_favorite_documents(session['username'])
    shared_documents = get_shared_documents(session['username'])
    user_events = get_user_events(session['username'])

    return render_template('dashboard.html', 
                           recent_documents=recent_documents, 
                           notifications=notifications,
                           user_tasks=user_tasks,
                           favorite_documents=favorite_documents,
                           shared_documents=shared_documents,
                           user_events=user_events)

@bp.route('/add_task', methods=['POST'])
def add_task():
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))

    task_description = request.form['task_description']
    task_due_date = request.form['task_due_date']
    
    # Convertir la fecha a objeto datetime
    task_due_date = datetime.strptime(task_due_date, '%Y-%m-%d')

    add_user_task(session['username'], task_description, task_due_date)
    return redirect(url_for('dashboard.dashboard'))



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
    return redirect(url_for('dashboard.dashboard'))

