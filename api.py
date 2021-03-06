from flask_security import login_required, current_user
from flask_api import status
from flask import request, jsonify
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
    event.finished = False
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
    event.finished = True
    event.save()

    return ('', 200)


@app.route('/get_event_info/<event_id>')
def get_event_info(event_id):
    event = Event.get(Event.id == event_id)
    if not event:
        raise EventNotFound(event_id)

    teams = []
    for t in Team.select().where(Team.event == event_id):
        members = []
        for m in t.members:
            # TODO: Name rather than email - need to set the name when creating
            # users.
            members.append({'name': m.user.email,
                            'id': m.user.id})
        teams.append({'name': t.name,
                      'members': members})

    data = {'name': event.name,
            'id': event.id,
            'teams': teams}

    return json.dumps(data)


@app.route('/active_events')
def active_events():
    events = [{'name': e.name, 'id': e.id} for e in
              Event.select().where(Event.active == True)]
    return json.dumps(events)


@app.route('/upcoming_events')
def upcoming_events():
    events = [{'name': e.name, 'id': e.id} for e in
              Event.select().where(
                  Event.active == False, Event.finished == False)]
    return json.dumps(events)


@app.route('/past_events')
def past_events():
    events = [{'name': e.name, 'id': e.id} for e in
              Event.select().where(Event.finished == True)]
    return json.dumps(events)


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
    # TODO: Leaving a team deletes it if empty?
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


@app.route('/api/v1/events/<event_id>/answers/', methods=['GET'])
@login_required
def answers_get(event):
    event = Event.get(Event.id == event_id)
    if not event:
        return ('Event with id {} does not exist'.format(event_id),
                status.HTTP_404_NOT_FOUND)

    # TODO: Support filtering for specific questoins
    # TODO: Need the option to get answers for all teams after the event has
    # finished.

    team = get_team(event, current_user)
    if not team:
        return ('User {} is not on a team'.format(current_user.id),
                status.HTTP_400_BAD_REQUEST)

    response = {'answers': {a.question: a.answer for a in
                   Answer.select().where(Answer.team == team.id)}}


@app.route('/api/v1/events/<event_id>/answers/',
           methods=['POST', 'PUT', 'PATCH'])
@login_required
def answers_update(event_id):
    event = Event.get(Event.id == event_id)
    if not event:
        return ('Event with id {} does not exist'.format(event_id),
                status.HTTP_404_NOT_FOUND)

    if not event.active:
        return ('Event with id {} has not started'.format(event_id),
                status.HTTP_400_BAD_REQUEST)

    team = get_team(event, current_user)
    if not team:
        return ('User {} is not on a team'.format(current_user.id),
                status.HTTP_400_BAD_REQUEST)

    data = request.get_json()
    if 'answers' not in data:
        return ('Data must contain "answers" object',
                status.HTTP_400_BAD_REQUEST)

    for question, answer in data['answers']:
        # TODO: Need to check that the question exists. 
        a, _ = Answer.get_or_create(team=team, question=question)
        a.answer = answer

        # TODO: Don't store correctness in the DB, check it when we need to know
        a.correct = questions.plugin_object.check_answer(question, answer)
        a.save()


    # TODO: Just return the updated answers.
    response = {'answers': {a.question: a.answer for a in
                   Answer.select().where(Answer.team == team.id)}}
    return json.dumps(answers)
