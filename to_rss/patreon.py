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
            # 'teaser_text',
            'min_cents_pledged_to_view',
            # 'is_automated_monthly_charge',
            'published_at',
            # 'scheduled_for',
            'url',
            'edited_at',
            # 'edit_url',
            # 'deleted_at',
            # 'comment_count',
            # 'like_count',
            'image',
            # 'is_paid',
            # 'pledge_url',
            # 'patreon_url',
            # 'current_user_has_liked',
            # 'current_user_can_view',
            # 'current_user_can_delete',
            # 'upgrade_url',
            # 'num_pushable_users',
            # 'was_posted_by_campaign_owner',
        ],
        'user': [
            'full_name',
            # 'first_name',
            # 'last_name',
            # 'about',
            # 'created',
            # 'gender',
            # 'default_country_code',
            'url',
            'image_url',
            # 'thumb_url',
            # 'social_connections',
            # 'facebook',
            # 'twitch',
            # 'twitter',
            # 'vanity',
            # 'youtube',
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
    response.raise_for_status()

    return response.json()


def get_user_id(user):
    """Get the user ID from a user name."""
    response = requests.get(PATREON_URL.format(user))
    response.raise_for_status()

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
        included = data['included']
    except KeyError:
        description = '{} on Patreon'.format(user)
        users = {}
        tags = {}
    else:
        # Use the 1st campaign description as the feed description.
        campaigns = [d for d in included if d['type'] == 'campaign']
        description = campaigns[0]['attributes']['summary']

        # Get the users associated with this Patreon.
        users = {u['id']: u for u in included if u['type'] == 'user'}

        # Get the custom tags.
        tags = {t['id']: t for t in included if t['type'] == 'post_tag'}

    feed = feedgenerator.Rss201rev2Feed(
        title=user,
        link=PATREON_URL.format(user),
        description=description)

    # Iterate over each article.
    for post in data['data']:
        try:
            # If the content is available, use it.
            content = post['attributes']['content']
        except KeyError:
            # Otherwise, advertise how much you would need to pay to see it.
            min_cents_pledged_to_view = post['attributes']['min_cents_pledged_to_view']

            # Some posts you need to have a certain reward level, unfortunately
            # it is unclear how to query that information from the post (the
            # only link seems to be back to the campaign, not the individual
            # rewards).
            if min_cents_pledged_to_view is None:
                min_cents_pledged_to_view = 'an unknown amount'

            else:
                min_cents_pledged_to_view = '${:.2f}'.format(
                    float(post['attributes']['min_cents_pledged_to_view']) / 100)

            content = 'This posts if for Patrons only. You must pledge {}.'.format(
                min_cents_pledged_to_view)

        # Pull the current author's information.
        try:
            author_id = post['relationships']['user']['data']['id']
            author_name = users[author_id]['attributes']['full_name']
            author_link = users[author_id]['attributes']['url']
        except KeyError:
            author_name = None
            author_link = None

        # Check if the post has been edited.
        edited_at = None
        if post['attributes']['edited_at']:
            edited_at = iso8601.parse_date(post['attributes']['edited_at'])

        # Get the categories/tags if there are any.
        categories = []
        for tag in post['relationships']['user_defined_tags']['data']:
            try:
                tag = tags[tag['id']]
                categories.append(tag['attributes']['value'])
            except KeyError:
                pass

        feed.add_item(
            title=post['attributes']['title'],
            link=post['attributes']['url'],
            description=content,
            author_name=author_name,
            author_link=author_link,
            pubdate=iso8601.parse_date(post['attributes']['published_at']),
            unique_id=post['id'],
            categories=categories,
            updateddate=edited_at,
        )

    return feed.writeString('utf-8')
