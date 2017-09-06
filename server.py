"""
Simple Flask server that provides paths to the various RSS feeds.

"""

from os import path

from flask import abort, Flask

from jinja2 import Environment, FileSystemLoader

from to_rss.nhl import nhl_news, team_news, VALID_TEAMS
from to_rss.patreon import patreon_posts
from to_rss.pottermore import pottermore_news, pottermore_features
from to_rss.wikipedia import get_articles

application = Flask(__name__)
# PythonAnywhere likes to call this 'app'.
app = application

# Jinja2 environment.
root = path.dirname(path.abspath(__file__))
env = Environment(loader=FileSystemLoader(path.join(root, 'to_rss', 'templates')))


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


# Pottermore endpoints.
@application.route('/pottermore/news/')
def serve_pottermore_news():
    return pottermore_news()


@application.route('/pottermore/features/')
def serve_pottermore_features():
    return pottermore_features()


if __name__ == "__main__":
    application.run()
