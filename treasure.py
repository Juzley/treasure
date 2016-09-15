from flask import Flask, render_template, redirect, url_for
from flask_peewee.db import Database
from flask_security import Security, PeeweeUserDatastore, UserMixin,           \
    RoleMixin, login_required, current_user
from flask_security.utils import encrypt_password
from peewee import CharField, TextField, ForeignKeyField, BooleanField
from yapsy.PluginManager import PluginManager
import random
import string


app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'secret'
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_PASSWORD_HASH'] = 'bcrypt'
app.config['SECURITY_PASSWORD_SALT'] = '''
                            naAiVrNOWLrPu9qeIeZD0wgBLFjV/JsuhJsn/YC8V7U'''
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
app.config['SECURITY_SEND_PASSWORD_CHANGE_EMAIL'] = False
app.config['SECURITY_SEND_PASSORD_RESET_NOTICE_EMAIL'] = False
app.config['DATABASE'] = {
    'name': 'treasure.db',
    'engine': 'peewee.SqliteDatabase'
}


# Connect to the database
db = Database(app)


# Define the data model
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
    questions = TextField()
    questions_version = TextField(null=True)
    active = BooleanField(default=False)


class EventAdmin(db.Model):
    event = ForeignKeyField(Event, related_name='admins')
    user = ForeignKeyField(User, related_name='admin_events')


class Team(db.Model):
    name = TextField()
    event = ForeignKeyField(Event, related_name='teams')
    # TODO: key of name/event


class Participant(db.Model):
    user = ForeignKeyField(User, related_name='events')
    team = ForeignKeyField(Team, related_name='members')


# Set up flask-security
user_datastore = PeeweeUserDatastore(db, User, Role, UserRoles)
security = Security(app, user_datastore)


# Create a test user
@app.before_first_request
def init_tables():
    for Model in (User, Role, UserRoles, Event, EventAdmin, Team, Participant):
        Model.create_table(fail_silently=True)
    if not User.select(User.email=='juzley@gmailcom').exists():
        user_datastore.create_user(email='juzley@gmail.com',
                                   password=encrypt_password('password'))


################################################################################
# Plugins
################################################################################

pluginManager = PluginManager(directories_list=['./questions'],
                              plugin_info_ext='plugin')
pluginManager.collectPlugins()


################################################################################
# Helper functions
################################################################################
def is_event_admin(event, user):
    return EventAdmin.select().where(EventAdmin.event==event,
                                     EventAdmin.user==user.id).count() > 0


################################################################################
# Views
################################################################################
@app.route('/register')
def register_user():
    return render_template('security/register_user.html')


@app.route('/start_event/<event_id>')
@login_required
def start_event(event_id):
    # TODO: Post rather than get?
    # TODO: Check event exists
    event = Event.get(Event.id==event_id)

    # Don't start the event if it is already started, or if the current user
    # isn't an admin.
    if not event.active and is_event_admin(event, current_user):
        print("Started")
        event.active = True
        event.save()

    return redirect(url_for('home'))



@app.route('/end_event/<event_id>')
@login_required
def end_event(event_id):
    # TODO: Check event exists
    event = Event.get(Event.id==event_id)

    # Don't stop the event if it isn't started, or if the current user isn't
    # an admin
    if event.active and is_event_admin(event, current_user):
        print("Stopped")
        event.active = False
        event.save()

    return redirect(url_for('home'))

@app.route('/create_event/<questions>')
@login_required
def create_event(questions):
    # TODO: Should probably make it so that only an admin can create events
    # Check that the question set we're creating an event for exists
    if not pluginManager.getPluginByName(questions):
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
    questions = [p.name for p in pluginManager.getAllPlugins()]
    events = Event.select()
    return render_template('index.html', questions=questions, events=events)


if __name__ == '__main__':
    app.run()
