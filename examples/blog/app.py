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
MIDDLEWARE_CLASSES = [
    "misc.query_count_middleware.QueryCountMiddleware"
]

app = App()
extra_settings = {"LOGGING": LOGGING, "MIDDLEWARE_CLASSES": MIDDLEWARE_CLASSES}
app.setup(apps=["blog"], root_urlconf="blog.urls", extra_settings=extra_settings)

if __name__ == "__main__":
    from django.db.models import Model
    from blog import models
    for v in vars(models).values():
        if isinstance(v, type) and issubclass(v, Model):
            app.create_table(v)
    from misc import setup_db
    setup_db.setup()
    from blog.client import main
    app.run(main)
