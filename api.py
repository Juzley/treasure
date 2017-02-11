from flask_security import login_required, current_user, roles_required
from flask import render_template, request, redirect, url_for, jsonify
import json

from questions import questionsmanager
from model import Event, EventAdmin, Team, Answer, Participant
from model import get_team, is_event_admin
from app import app

class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

class EventNotFound(InvalidUsage):
    def __init__(self, event_id):
        InvalidUsage.__init__(
            self,
            message='Event with id {} does not exist'.format(event_id),
            status_code=404)

class TeamNotFound(InvalidUsage):
    def __init__(self, name, event_id):
        InvalidUsage.__init__(
            self,
            message='Team {} for event id {} does not exist'.format(name,
                                                                    event_id),
            status_code=404)

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.route('/create_event/<questions>/<name>')
@login_required
def create_event(questions, name):
    # TODO: Should probably make it so that only an admin can create events
    # Check that the question set we're creating an event for exists
    if not questionsmanager.getPluginByName(questions):
        raise InvalidUsage(
            'Question set "{}" not found'.format(questions), 404)

    event = Event.create(name=name, questions=questions)
    EventAdmin.create(event=event, user=current_user.id)

    return ('', 200)


@app.route('/start_event/<event_id>')
@login_required
def start_event(event_id):
    event = Event.get(Event.id == event_id)
    if not event:
        raise EventNotFound(event_id)

    if event.active:
        raise InvalidUsage(
            'Event id {} already started'.format(event_id), 403)

    if not is_event_admin(event, current_user):
        raise InvalidUsage(
            'Only event admins can start events', 403)

    event.active = True
    event.save()

    return ('', 200)


@app.route('/end_event/<event_id>')
@login_required
def end_event(event_id):
    event = Event.get(Event.id == event_id)
    if not event:
        raise EventNotFound(event_id)

    if not event.active:
        raise InvalidUsage(
            'Event id {} not started'.format(event_id), 403)

    if not is_event_admin(event, current_user):
        raise InvalidUsage(
            'Only event admins can end events', 403)

    event.active = False
    event.save()

    return ('', 200)


@app.route('/create_team/<event_id>/<name>')
@login_required
def create_team(event_id, name):
    # TODO: Can't do this while the event is active.
    # TODO: Only an admin can create teams?
    query = Team.select().where(Team.event == event_id, Team.name == name)
    if query.exists():
        raise InvalidUsage(
            'Team {} for event id {} exists'.format(name, event_id), 409)
    Team.create(name=name, event=event_id, admin=current_user.id)

    return ('', 200)


@app.route('/join_team/<event_id>/<name>')
@login_required
def join_team(event_id, name):
    # TODO: Can't do this while the event is active.
    # Check if this user is already in a team for this event.
    for p in Participant.select().join(Team).where(
            Team.event == event_id, Participant.user == current_user.id):
        p.delete().execute()

    team = Team.get(Team.event == event_id, Team.name == name)
    if not team:
        raise TeamNotFound(name, event_id)

    p = Participant(user=current_user.id, team=team.id)
    p.save()

    return ('', 200)


@app.route('/leave_team/<event_id>/<name>')
@login_required
def leave_team(event_id, name):
    # TODO: Can't do this while the event is active.
    query = Participant.select().join(Team).where(
        Team.event == event_id, Participant.user == current_user.id)
    if not query.exists():
        raise InvalidUsage(
            'User {} is not in team {} for event id {}'.format(current_user.id,
                                                               name,
                                                               event_id),
            404)

    for p in query:
        p.delete().execute()

    return ('', 200)


@app.route('/answer_question/<event_id>/<question>', methods=['POST'])
@login_required
def answer_question(event_id, question):
    answer = request.get_json()

    event = Event.get(Event.id == event_id)
    if not event:
        raise InvalidUsage(
            'Event with id {} does not exist'.format(event_id), 404)

    if not event.active:
        raise InvalidUsage(
            'Event id {} has not started'.format(event_id), 403)

    team = get_team(event, current_user)
    if not team:
        raise InvalidUsage(
            'User {} is not on a team'.format(current_user.id), 403)

    questions = questionsmanager.getPluginByName(event.questions)
    # TODO: Questions not found

    a, _ = Answer.get_or_create(team=team, question=question)
    a.answer = answer
    a.correct = questions.plugin_object.check_answer(question, answer)
    a.save()

    # No data to return
    return ('', 204)


@app.route('/get_answers/<event_id>')
@login_required
def get_answers(event_id):
    # TODO: Support getting answers for a particular team, for admins
    event = Event.get(Event.id == event_id)
    if not event:
        raise EventNotFound(event_id)

    team = get_team(event, current_user)
    if not team:
        raise InvalidUsage(
            'User {} is not on a team'.format(current_user.id), 403)

    answers = {a.question: a.answer for a in
               Answer.select().where(Answer.team == team.id)}
    return json.dumps(answers)

