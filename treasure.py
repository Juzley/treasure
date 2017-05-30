from flask_security.utils import encrypt_password
from app import app
from auth import user_datastore
from model import Role, User
import admin
import views
import api


@app.before_first_request
def init_admin():
    # Create the admin role
    if not Role.select(Role.name == 'admin').exists():
        user_datastore.create_role(name='admin')

    # Temporary - create a test user
    if not User.select(User.email == 'juzley@gmail.com').exists():
        user_datastore.create_user(email='juzley@gmail.com',
                                   password=encrypt_password('password'),
                                   roles=['admin'])

if __name__ == '__main__':
    import logging
    logger = logging.getLogger('peewee')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())

    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    app.run(threaded=True)
