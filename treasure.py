from flask import Flask, render_template
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
    user_datastore.create_user(email='juzley@gmail.com',
                               password=encrypt_password('password'))


################################################################################
# Plugins
################################################################################

pluginManager = PluginManager(directories_list=['./questions'],
                              plugin_info_ext='plugin')
pluginManager.collectPlugins()


################################################################################
# Views
################################################################################
@app.route('/register')
def register_user():
    return render_template('security/register_user.html')


@app.route('/start_event/<event>')
@login_required()
def start_event('event'):
    pass

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

    return home()


@app.route('/create_team/<event>/<name>')
@login_required
def create_team(event, name):
    # TODO: Only an admin can create teams?
    # TODO: Use the name we're given
    name = ''.join(random.choice(string.ascii_lowercase) for _ in range(4))
    Team.create(name=name, event=event)

    return home()


@app.route('/join_team/<event>/<name>')
@login_required
def join_team(event, name):
    # TODO: Check team exists
    # Check if this user is already in a team for this event.
    for p in Participant.select().join(Team).where(
            Team.event == event, Participant.user == current_user.id):
        p.delete()

    team = Team.get(Team.event == event, Team.name == name)
    p = Participant(user=current_user.id, team=team.id)
    p.save()
    print(team.members)
    for m in team.members:
        print(m.user.email)


    return home()


@app.route('/')
@login_required
def home():
    questions = [p.name for p in pluginManager.getAllPlugins()]
    events = Event.select()
    return render_template('index.html', questions=questions, events=events)


if __name__ == '__main__':
    app.run()
