from flask_security import login_required, current_user, roles_required
from flask import render_template, request, redirect, url_for
import json

from questions import questionsmanager
from model import Event, EventAdmin, Team, Answer, Participant
from model import get_team, is_event_admin
from app import app


@app.route('/admin')
@roles_required('admin')
def admin():
    questions = [p.name for p in questionsmanager.getAllPlugins()]
    events = Event.select()
    return render_template('admin.html', questions=questions, events=events)


@app.route('/event/<event_id>')
@login_required
def view_event(event_id):
    # TODO: Check event exists, check login vs not etc
    event = Event.get(Event.id == event_id)

    # If the event is active, display the questions, otherwise show the
    # event info page.
    if event.active:
        # TODO: Check plugin exists
        questions = questionsmanager.getPluginByName(event.questions)
        return questions.plugin_object.render(event_id)
    else:
        return render_template('event.html', event=event)


@app.route('/')
@login_required
def home():
    questions = [p.name for p in questionsmanager.getAllPlugins()]
    events = Event.select()
    return render_template('index.html', questions=questions, events=events)
