import json
import sys

import requests
from fabric import task as fabtask
from invoke import task


def _load_config():
    with open(".pythonanywhere.json") as f:
        # Has keys api_token, username, and domain_name.
        return json.load(f)


config = _load_config()


@task(name="reload")
def _reload(c):
    """Restart the web-app."""
    print("Reloading the WSGI app.")
    response = requests.post(
        "https://www.pythonanywhere.com/api/v0/user/{username}/webapps/{domain_name}/reload/".format(
            **config
        ),
        headers={
            "Authorization": "Token " + config["api_token"],
        },
    )

    if response.status_code != 200:
        print("Reloading the WSGI app failed.")
        sys.exit(1)


@fabtask(post=[_reload], hosts=[f"{config['username']}@{config['host']}"])
def deploy(c):
    """Deploy a new version of to-rss."""
    with c.cd("to-rss"):
        print("Fetching new code.")
        c.run("git fetch")
        c.run("git reset --hard origin/main")

        print("Cleaning old files.")
        c.run("git clean -dxf -- __pycache__ to_rss")
