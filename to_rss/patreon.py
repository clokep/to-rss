from bs4 import BeautifulSoup

import feedgenerator

import iso8601

import requests

API_URL = 'https://api.patreon.com/stream'
PATREON_URL = 'https://www.patreon.com/{}'


def get_patreon_posts(user_id):
    """Gets a list of a user's posts."""
    # Fields to include in the response.
    fields = {
        'post': [
            'post_type',
            'title',
            'content',
            'min_cents_pledged_to_view',
            'published_at',
            'url',
            # 'comment_count',
            # 'like_count',
            'post_file',
            'image',
            'thumbnail_url',
            'embed',
            # 'is_paid',
            # 'pledge_url',
            # 'patreon_url',
            # 'current_user_has_liked',
            # 'patron_count',
            # 'current_user_can_view',
            # 'current_user_can_delete',
            # 'upgrade_url',
        ],
        'user': [
            'image_url',
            'full_name',
            'url',
        ],
    }

    # Additional fields to filter the user.
    filters = {
        'is_by_creator': 'true',
        'is_following': 'false',
        'creator_id': user_id,
        'contains_exclusive_posts': 'true',
    }

    params = {'fields[' + field_type + ']': ','.join(values) for field_type, values in fields.items()}

    params.update({
        'filter[' + filter_type + ']': value for filter_type, value in filters.items()
    })
    params['page[cursor]'] = 'null'

    # Some default properties.
    params['json-api-version'] = '1.0'

    # Get the JSON API response.
    response = requests.get(API_URL, params=params)

    return response.json()


def get_user_id(user):
    """Get the user ID from a user name."""
    response = requests.get(PATREON_URL.format(user))

    # Process the HTML using BeautifulSoup!
    soup = BeautifulSoup(response.content, 'html.parser')

    # Get the creator ID from the JavaScript.
    script = soup.find_all('script')[3]
    parts = script.string.split('\n')
    for part in parts:
        part = part.strip()
        if part.startswith('"creator_id"'):
            return part.lstrip('"creator_id":').rstrip(',').strip()


def patreon_posts(user):
    user_id = get_user_id(user)
    data = get_patreon_posts(user_id)

    # Get a description.
    try:
        included = data['include']
    except KeyError:
        description = '{} on Patreon'.format(user)
    else:
        campaigns = [d for d in data['included'] if d['type'] == 'campaign']
        description = campaigns[0]['attributes']['summary']

    feed = feedgenerator.Rss201rev2Feed(user, PATREON_URL.format(user), description)

    # Iterate over each article.
    for post in data['data']:
        # Some articles don't have their content available.
        try:
            content = post['attributes']['content']
        except KeyError:
            content = 'This posts if for Patrons only. You must pledge ${:.2f}'.format(
                float(post['attributes']['min_cents_pledged_to_view']) / 100)

        feed.add_item(title=post['attributes']['title'],
                      link=post['attributes']['url'],
                      description=content,
                      author_name=user,
                      author_link=PATREON_URL.format(user),
                      pubdate=iso8601.parse_date(post['attributes']['published_at']))

    return feed.writeString('utf-8')
