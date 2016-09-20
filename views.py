from flask_security import login_required, current_user
from flask import render_template, request, redirect, url_for
import json

from questions import questionsmanager
from model import Event, EventAdmin, Team, Answer, Participant
from model import get_team, is_event_admin
from app import app


@app.route('/event/<event_id>')
@login_required
def view_event(event_id):
    # TODO: Check event exists, check login vs not etc
    event = Event.get(Event.id == event_id)

    if event.active:
        # TODO: Check plugin exists
        questions = questionsmanager.getPluginByName(event.questions)
        return questions.plugin_object.render(event_id)
    else:
        return render_template('event.html', event=event)


@app.route('/answer_question/<event_id>/<question>', methods=['POST'])
@login_required
def answer_question(event_id, question):
    answer = request.get_json()

    # TODO: Check all this stuff exists
    event = Event.get(Event.id == event_id)

    # TODO: Error if event isn't active.
    if event.active:
        team = get_team(event, current_user)
        questions = questionsmanager.getPluginByName(event.questions)

        a, _ = Answer.get_or_create(team=team,
                                    question=question)
        a.answer = answer
        a.correct = questions.plugin_object.check_answer(question, answer)
        a.save()

    # No data to return
    return ('', 204)


@app.route('/get_answers/<event_id>')
@login_required
def get_answers(event_id):
    # TODO: Support getting answers for a particular team, for admins
    # TODO: Check everything exists
    event = Event.get(Event.id == event_id)

    team = get_team(event, current_user)

    answers = {a.question: a.answer for a in
               Answer.select().where(Answer.team == team.id)}
    return json.dumps(answers)


@app.route('/start_event/<event_id>')
@login_required
def start_event(event_id):
    # TODO: Post rather than get?
    # TODO: Check event exists
    event = Event.get(Event.id == event_id)

    # Don't start the event if it is already started, or if the current user
    # isn't an admin.
    if not event.active and is_event_admin(event, current_user):
        event.active = True
        event.save()

    return redirect(url_for('home'))


@app.route('/end_event/<event_id>')
@login_required
def end_event(event_id):
    # TODO: Check event exists
    event = Event.get(Event.id == event_id)

    # Don't stop the event if it isn't started, or if the current user isn't
    # an admin
    if event.active and is_event_admin(event, current_user):
        event.active = False
        event.save()

    return redirect(url_for('home'))


@app.route('/create_event/<questions>')
@login_required
def create_event(questions):
    # TODO: Should probably make it so that only an admin can create events
    # Check that the question set we're creating an event for exists
    if not questionsmanager.getPluginByName(questions):
        # TODO: some kind of error
        pass

    event = Event.create(questions=questions)
    EventAdmin.create(event=event, user=current_user.id)

    return redirect(url_for('home'))


@app.route('/create_team/<event>/<name>')
@login_required
def create_team(event, name):
    # TODO: Only an admin can create teams?
    # TODO: Use the name we're given
    import random
    import string
    name = ''.join(random.choice(string.ascii_lowercase) for _ in range(4))
    Team.create(name=name, event=event)

    return redirect(url_for('home'))


@app.route('/join_team/<event>/<name>')
@login_required
def join_team(event, name):
    # TODO: Check team exists
    # Check if this user is already in a team for this event.
    # TODO: don't think this works
    for p in Participant.select().join(Team).where(
            Team.event == event, Participant.user == current_user.id):
        p.delete()

    team = Team.get(Team.event == event, Team.name == name)
    p = Participant(user=current_user.id, team=team.id)
    p.save()

    return redirect(url_for('home'))


@app.route('/')
@login_required
def home():
    questions = [p.name for p in questionsmanager.getAllPlugins()]
    events = Event.select()
    return render_template('index.html', questions=questions, events=events)
