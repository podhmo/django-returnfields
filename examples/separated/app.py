# -*- coding:utf-8 -*-
from django_returnfields.app import App  # shorthand
import sys

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[%(asctime)s][%(name)s:L%(lineno)d:%(levelname)s] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'stdout': {
            'level': 'DEBUG',
            'formatter': 'verbose',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
        },
    },
    'loggers': {
        'django.db': {
            'handlers': ['stdout'],
            'level': 'DEBUG',
        }
    }
}


app = App()
app.setup(apps=["crud"], root_urlconf="crud.urls", extra_settings={"LOGGING": LOGGING})

if __name__ == "__main__":
    from crud.models import User, Skill
    from crud.client import main
    app.create_table(User, Skill)
    app.run(main)
