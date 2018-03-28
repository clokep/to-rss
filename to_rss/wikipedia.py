from datetime import date, datetime, timedelta
from urllib.parse import quote as url_quote

import feedgenerator

import mwparserfromhell
from mwparserfromhell.definitions import MARKUP_TO_HTML
from mwparserfromhell.nodes import Comment, ExternalLink, HTMLEntity, Tag, Template, Text, Wikilink
from mwparserfromhell.wikicode import Wikicode

import mwcomposerfromhell

import requests


def get_current_events_by_date(lookup_date):
    # Format the date as a string, this is formatted using the #time extension
    # to Wiki syntax:
    # https://www.mediawiki.org/wiki/Help:Extension:ParserFunctions#.23time with
    # a format of "Y F j". This is awkward because we want the day *not* zero
    # padded, but the month as a string.
    datestr = '{} {} {}'.format(lookup_date.year, lookup_date.strftime('%B'), lookup_date.day)
    return 'Portal:Current_events/' + datestr


def get_article_url(name):
    return 'https://en.wikipedia.org/wiki/' + name


def get_article(url):
    """Fetches and returns the article content as a string."""
    response = requests.get(url, params={'action': 'raw'})
    return response.text


def get_articles():
    """
    Returns a map of dates to a list of current events on that date.

    The root of this is parsing https://en.wikipedia.org/wiki/Portal:Current_events
    The true information we're after is included via
    https://en.wikipedia.org/wiki/Portal:Current_events/Inclusion
    which then includes the past seven days.
    """
    feed = feedgenerator.Rss201rev2Feed('Wikipedia: Portal: Current events',
                                        'https://en.wikipedia.org/wiki/Portal:Current_events',
                                        'Wikipedia: Portal: Current events')

    # Start at today.
    day = date.today()

    for i in range(7):
        day -= timedelta(days=1)

        # Download the article content.
        url = get_article_url(get_current_events_by_date(day))
        article = get_article(url)
        # Parse the article contents.
        wikicode = mwparserfromhell.parse(article)

        # Current event pages have a top-level template.
        for template in wikicode.ifilter_templates():
            if template.name == 'Current events':
                content = template.get('content').value

                try:
                    feed.add_item(title=u'Current events: {}'.format(day),
                                  link=url,
                                  # Convert the Wikicode to HTML.
                                  description=mwcomposerfromhell.compose(content),
                                  pubdate=datetime(*day.timetuple()[:3]))
                except mwcomposerfromhell.HtmlComposingError:
                    print("Unable to render article from: {}".format(day))

                # Stop processing this article.
                break

        # TODO If the template is not found, we should do something.

    return feed.writeString('utf-8')
