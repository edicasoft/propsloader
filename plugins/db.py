from cement.core import hook
from core.data import Database


def extend_db_object(app):
    conf = app.config.get_section_dict('db')
    db_client = Database(conf)
    app.extend('db', db_client)


def load(app):
    hook.register('pre_run', extend_db_object)