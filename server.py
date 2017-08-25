"""
Simple Flask server that combines both the NHL and Wikipedia news parsers.

"""

from jinja2 import Template

from flask import Flask

from to_rss.nhl import nhl_news, team_news, VALID_TEAMS
from to_rss.patreon import patreon_posts
from to_rss.wikipedia import get_articles

application = Flask(__name__)
# PythonAnywhere likes to call this 'app'.
app = application


@application.route('/')
def serve_about():
    """A link to each endpoint that's supported."""
    template = Template('''<html>
<body>
<ul>
<li><a href="/nhl/">NHL News</a></li>
<li><a href="/patreon/">Patreon</a></li>
<li><a href="/wikipedia/">Wikipedia</a></li>
</ul>
</body>
</html>''')

    return template.render()


# Wikipedia end points.
@application.route('/wikipedia/')
def serve_wikipedia():
    template = Template('''<html>
<body>
<h2><a href="/wikipedia/current_events/">Wikipedia Current Events</a></h2>
</body>
</html>''')

    return template.render()


@application.route('/wikipedia/current_events/')
def serve_wikipedia_current_events():
    return get_articles()


# NHL end points.
@application.route('/nhl/')
def serve_nhl():
    template = Template('''<html>
<body>
<h2><a href="/nhl/news/">NHL Headlines</a></h2>

<ul>
{% for short, name in teams %}
<li><a href="/nhl/{{ short }}/">{{ name }}</a></li>
{% endfor %}
</ul>

</body>
</html>''')

    return template.render(teams=VALID_TEAMS.items())


@application.route('/nhl/news/')
def serve_nhl_news():
    return nhl_news()


@application.route('/nhl/<team>/')
def serve_nhl_team_news(team):
    if team not in VALID_TEAMS:
        abort(404)

    return team_news(team)


# Patreon end points.
@application.route('/patreon/')
def serve_patreon():
    template = Template('''<html>
<body>
<h2>Patreon Posts</h2>

</body>
</html>''')

    return template.render()


@application.route('/patreon/<user>/')
def serve_patreon_user(user):
    return patreon_posts(user)


if __name__ == "__main__":
    application.run()
