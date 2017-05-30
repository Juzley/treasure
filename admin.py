from flask_admin import Admin
from flask_admin.contrib.peewee import ModelView
import model
from app import app

admin = Admin(app, name='Treasure', template_mode='bootstrap3')
admin.add_view(ModelView(model.User))
admin.add_view(ModelView(model.Role))
admin.add_view(ModelView(model.UserRoles))
admin.add_view(ModelView(model.Event))
admin.add_view(ModelView(model.EventAdmin))
admin.add_view(ModelView(model.Team))
admin.add_view(ModelView(model.Participant))
admin.add_view(ModelView(model.Answer))
