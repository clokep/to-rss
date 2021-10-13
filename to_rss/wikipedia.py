from datetime import date, datetime, timedelta

import feedgenerator

import mwcomposerfromhell

import mwparserfromhell

from sentry_sdk import start_span

from to_rss import session

BASE_URL = "https://en.wikipedia.org/wiki/"


def get_current_events_by_date(lookup_date):
    # Format the date as a string, this is formatted using the #time extension
    # to Wiki syntax:
    # https://www.mediawiki.org/wiki/Help:Extension:ParserFunctions#.23time with
    # a format of "Y F j". This is awkward because we want the day *not* zero
    # padded, but the month as a string.
    datestr = f"{lookup_date.year} {lookup_date.strftime('%B')} {lookup_date.day}"
    return "Portal:Current_events/" + datestr


def get_article(url):
    """Fetches and returns the article content as a string."""
    response = session.get(url, params={"action": "raw"})
    return response.text


def get_articles():
    """
    Returns a map of dates to a list of current events on that date.

    The root of this is parsing https://en.wikipedia.org/wiki/Portal:Current_events
    The true information we're after is included via
    https://en.wikipedia.org/wiki/Portal:Current_events/Inclusion
    which then includes the past seven days.
    """
    resolver = mwcomposerfromhell.ArticleResolver(
        base_url="https://en.wikipedia.org/wiki/"
    )
    feed = feedgenerator.Rss201rev2Feed(
        "Wikipedia: Portal: Current events",
        resolver.get_article_url(resolver.resolve_article("Portal:Current_events", "")),
        "Wikipedia: Portal: Current events",
    )

    # Start at today.
    day = date.today()

    for i in range(7):
        day -= timedelta(days=1)

        # Create a composer.
        composer = mwcomposerfromhell.WikicodeToHtmlComposer(resolver=resolver)

        # Download the article content.
        url = resolver.get_article_url(
            resolver.resolve_article(get_current_events_by_date(day), "")
        )
        article = get_article(url)
        # Parse the article contents.
        with start_span(op="parse-wikitext", description="Parse " + url):
            wikicode = mwparserfromhell.parse(article)

        with start_span(op="wiki-to-html", description="Convert " + url):
            # Current event pages have a top-level template.
            for template in wikicode.ifilter_templates():
                if template.name == "Current events":
                    content = template.get("content").value

                    try:
                        # Convert the Wikicode to HTML.
                        result = composer.compose(content)
                    except mwcomposerfromhell.HtmlComposingError:
                        print(f"Unable to render article from: {day}")
                        continue

                    # Add the results to the RSS feed.
                    feed.add_item(
                        title=f"Current events: {day}",
                        link=url,
                        description=result,
                        pubdate=datetime(*day.timetuple()[:3]),
                    )

                    # Stop processing this article.
                    break

        # TODO If the template is not found, we should do something.

    return feed.writeString("utf-8")
