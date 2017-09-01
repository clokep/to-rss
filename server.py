"""
Simple Flask server that provides paths to the various RSS feeds.

"""

from flask import abort, Flask

from jinja2 import Environment, FileSystemLoader

from to_rss.nhl import nhl_news, team_news, VALID_TEAMS
from to_rss.patreon import patreon_posts
from to_rss.wikipedia import get_articles

application = Flask(__name__)
# PythonAnywhere likes to call this 'app'.
app = application

# Jinja2 environment.
env = Environment(loader=FileSystemLoader('to_rss/templates'))


@application.route('/')
def serve_about():
    """A link to each endpoint that's supported."""
    template = env.get_template('index.html')
    return template.render()


# Wikipedia end points.
@application.route('/wikipedia/')
def serve_wikipedia():
    template = env.get_template('wikipedia.html')
    return template.render()


@application.route('/wikipedia/current_events/')
def serve_wikipedia_current_events():
    return get_articles()


# NHL end points.
@application.route('/nhl/')
def serve_nhl():
    template = env.get_template('nhl.html')
    return template.render(teams=VALID_TEAMS)


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
    template = env.get_template('patreon.html')
    return template.render()


@application.route('/patreon/<user>/')
def serve_patreon_user(user):
    return patreon_posts(user)


if __name__ == "__main__":
    application.run()
