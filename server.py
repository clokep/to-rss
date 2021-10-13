"""
Simple Flask server that provides paths to the various RSS feeds.

"""
import os
from os import path

from dotenv import load_dotenv

# Load .env from the same directory as this file.
load_dotenv(path.join(path.dirname(__file__), ".env"))

from flask import abort, Flask, Response

from jinja2 import Environment, FileSystemLoader

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

from to_rss.nhl import nhl_news, team_news, VALID_TEAMS
from to_rss.patreon import patreon_posts
from to_rss.players_tribune import sports_news, VALID_SPORTS
from to_rss.pottermore import pottermore_page
from to_rss.thunderbird import thunderbird_status_meetings
from to_rss.wikipedia import get_articles

app = Flask(__name__)

# Jinja2 environment.
root = path.dirname(path.abspath(__file__))
env = Environment(loader=FileSystemLoader(path.join(root, "to_rss", "templates")))

# Configure Sentry (if credentials are available).
sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn, integrations=[FlaskIntegration()], traces_sample_rate=0.1
    )


# Use a custom response class to set security headers.
class ToRssResponse(Response):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # See https://flask.palletsprojects.com/en/1.1.x/security/#security-headers
        allowed_sources = [
            "'self'",
            "'unsafe-inline'",
            "https://stackpath.bootstrapcdn.com",
            "https://plausible.io",
        ]
        self.headers["Content-Security-Policy"] = "default-src " + " ".join(
            allowed_sources
        )
        self.headers["X-Content-Type-Options"] = "nosniff"
        self.headers["X-Frame-Options"] = "SAMEORIGIN"
        self.headers["X-XSS-Protection"] = "1; mode=block"


app.response_class = ToRssResponse


@app.route("/")
def serve_about():
    """A link to each endpoint that's supported."""
    template = env.get_template("index.html")
    return template.render()


# Wikipedia end points.
@app.route("/wikipedia/")
def serve_wikipedia():
    template = env.get_template("wikipedia.html")
    return template.render()


@app.route("/wikipedia/current_events/")
def serve_wikipedia_current_events():
    return Response(get_articles(), mimetype="application/rss+xml")


# NHL end points.
@app.route("/nhl/")
def serve_nhl():
    template = env.get_template("nhl.html")
    return template.render(teams=VALID_TEAMS)


@app.route("/nhl/news/")
def serve_nhl_news():
    return Response(nhl_news(), mimetype="application/rss+xml")


@app.route("/nhl/<team>/")
def serve_nhl_team_news(team):
    if team not in VALID_TEAMS:
        abort(404)

    return Response(team_news(team), mimetype="application/rss+xml")


# Patreon end points.
# @app.route('/patreon/')
def serve_patreon():
    template = env.get_template("patreon.html")
    return template.render()


# @app.route('/patreon/<user>/')
def serve_patreon_user(user):
    return Response(patreon_posts(user), mimetype="application/rss+xml")


# Pottermore endpoints.
@app.route("/pottermore/")
def serve_pottermore():
    template = env.get_template("pottermore.html")
    return template.render()


@app.route("/pottermore/news/")
def serve_pottermore_news():
    return Response(
        pottermore_page(
            "news",
            "news",
            "Pottermore News",
            "Get the latest Wizarding World news here. Faster than an owl and more accurate than the Daily Prophet",
        ),
        mimetype="application/rss+xml",
    )


@app.route("/pottermore/features/")
def serve_pottermore_features():
    return Response(
        pottermore_page(
            "feature",
            "features",
            "Pottermore Features",
            "For beginners, for novices, for Harry Potter superfans going 20 years-strong, dig deep into the Wizarding World with our collection of features",  # noqa E501
        ),
        mimetype="application/rss+xml",
    )


# Thunderbird endpoints.
@app.route("/thunderbird/")
def serve_thunderbird():
    template = env.get_template("thunderbird.html")
    return template.render()


@app.route("/thunderbird/status-meetings/")
def serve_thunderbird_status_meetings():
    return Response(thunderbird_status_meetings(), mimetype="application/rss+xml")


# The Players Tribune endpoints.
@app.route("/players_tribune/")
def serve_players_tribune():
    template = env.get_template("players_tribune.html")
    return template.render(sports=VALID_SPORTS)


@app.route("/players_tribune/<sport>/")
def serve_players_tribune_sport(sport):
    if sport not in VALID_SPORTS:
        abort(404)

    return Response(sports_news(sport), mimetype="application/rss+xml")


if __name__ == "__main__":
    # This is only used for development purposes, run `python server.py`.
    app.run(debug=True)
