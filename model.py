from peewee import CharField, TextField, ForeignKeyField, BooleanField,        \
    IntegerField
from flask_security import UserMixin, RoleMixin
from app import db


class User(db.Model, UserMixin):
    name = TextField(null=True)
    email = TextField(unique=True)
    password = TextField()
    active = BooleanField(default=True)


class Role(db.Model, RoleMixin):
    name = CharField(unique=True)
    description = TextField(null=True)


class UserRoles(db.Model):
    user = ForeignKeyField(User, related_name='roles')
    role = ForeignKeyField(Role, related_name='users')
    name = property(lambda self: self.role.name)
    description = property(lambda self: self.role.description)


class Event(db.Model):
    name = TextField()
    description = TextField(null=True)
    max_teams = IntegerField(default=0)
    questions = TextField()
    questions_version = TextField(null=True)
    active = BooleanField(default=False)


class EventAdmin(db.Model):
    event = ForeignKeyField(Event, related_name='admins')
    user = ForeignKeyField(User, related_name='admin_events')


class Team(db.Model):
    name = TextField()
    event = ForeignKeyField(Event, related_name='teams')
    admin = ForeignKeyField(User, related_name='admin_teams')
    # TODO: key of name/event


class Answer(db.Model):
    team = ForeignKeyField(Team, related_name='answers')
    question = IntegerField()
    answer = TextField(null=True)
    correct = BooleanField(default=False)
    # TODO: key of team/question


class Participant(db.Model):
    user = ForeignKeyField(User, related_name='user')
    team = ForeignKeyField(Team, related_name='members')


def is_event_admin(event, user):
    return EventAdmin.select().where(EventAdmin.event == event,
                                     EventAdmin.user == user.id).count() > 0


def get_team(event, user):
    # Use 'first' here - there should only be one result
    return Team.select().join(Participant).where(Participant.user == user.id,
                                                 Team.event == event).first()
