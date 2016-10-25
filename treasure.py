from flask_security.utils import encrypt_password

from app import app
from auth import user_datastore
from model import User, Role, UserRoles, Event, EventAdmin, Team, Answer,      \
    Participant
import views


@app.before_first_request
def init_tables():
    for Model in (User, Role, UserRoles, Event, EventAdmin, Team,
                  Answer, Participant):
        Model.create_table(fail_silently=True)

    # Create a test user
    if not User.select(User.email == 'juzley@gmailcom').exists():
        user_datastore.create_role(name='admin')
        user_datastore.create_user(email='juzley@gmail.com',
                                   password=encrypt_password('password'),
                                   roles=['admin'])

if __name__ == '__main__':
    app.run(threaded=True)
