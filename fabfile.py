import json
import sys

from invoke import task

import requests


@task
def reload(c):
    """Restart the web-app."""
    with open('.pythonanywhere.json', 'r') as f:
        # Has keys api_token, username, and domain_name.
        config = json.load(f)

    print("Reloading the WSGI app.")
    response = requests.post(
        'https://www.pythonanywhere.com/api/v0/user/{username}/webapps/{domain_name}/reload/'.format(**config),
        headers={
            "Authorization": "Token " + config['api_token'],
        }
    )

    if response.status_code != 200:
        print("Reloading the WSGI app failed.")
        sys.exit(1)


@task(post=[reload])
def deploy(c):
    """Deploy a new version of to-rss."""
    with c.cd('to-rss'):
        print('Fetching new code.')
        c.run('git fetch')
        c.run('git reset --hard origin/master')

        print('Cleaning old Python files.')
        c.run('pyclean .')
