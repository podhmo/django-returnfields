# -*- coding:utf-8 -*-
from django_returnfields.app import App  # shorthand

app = App()
app.setup(apps=["crud"], root_urlconf="crud.urls")

if __name__ == "__main__":
    from crud.models import User, Skill
    from crud.client import main
    app.create_table(User, Skill)
    app.run(main)
