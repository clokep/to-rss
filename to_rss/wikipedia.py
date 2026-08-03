import logging
from datetime import date, datetime, timedelta

import feedgenerator
import mwcomposerfromhell
import mwparserfromhell
from sentry_sdk import start_span

from to_rss import get_session

logger = logging.getLogger(__name__)

BASE_URL = "https://en.wikipedia.org/wiki/"


def get_current_events_by_date(lookup_date: date) -> str:
    # Format the date as a string, this is formatted using the #time extension
    # to Wiki syntax:
    # https://www.mediawiki.org/wiki/Help:Extension:ParserFunctions#.23time with
    # a format of "Y F j". This is awkward because we want the day *not* zero
    # padded, but the month as a string.
    datestr = f"{lookup_date.year} {lookup_date.strftime('%B')} {lookup_date.day}"
    return "Portal:Current_events/" + datestr


def get_article(url: str) -> str:
    """Fetches and returns the article content as a string."""
    response = get_session().get(
        url,
        params={"action": "raw"},
        headers={"User-agent": "to-rssbot (+https://www.to-rss.xyz/)"},
    )
    return response.text


def extract_content(wikicode: mwparserfromhell.wikicode.Wikicode):
    """
    Returns a day's news items as Wikicode, or None if they can't be found.

    Current event pages come in two layouts. Historically a single
    ``{{Current events}}`` template carried the whole day in its ``content``
    parameter. Newer pages instead sandwich the news between two copies of the
    template, marked ``top=yes`` and ``bottom=yes``, leaving the items in the
    article body between them.
    """
    templates = [
        template
        for template in wikicode.filter_templates(recursive=False)
        if template.name == "Current events"
    ]
    if not templates:
        return None

    # Legacy layout: the news is a parameter of the template.
    for template in templates:
        if template.has("content"):
            return template.get("content").value

    # Current layout: the news is whatever follows the opening template, up to
    # the closing one (dropped along with anything after it).
    start = wikicode.index(templates[0]) + 1
    end = wikicode.index(templates[-1]) if len(templates) > 1 else len(wikicode.nodes)
    return mwparserfromhell.wikicode.Wikicode(wikicode.nodes[start:end])


def get_articles() -> str:
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
        with start_span(op="parse-wikitext", name="Parse " + url):
            wikicode = mwparserfromhell.parse(article)

        with start_span(op="wiki-to-html", name="Convert " + url):
            # Current event pages have a top-level template.
            content = extract_content(wikicode)
            if content is None:
                logger.error(
                    f"'Current events' template not found in article for {day}"
                )
                continue

            try:
                # Convert the Wikicode to HTML.
                result = composer.compose(content)
            except mwcomposerfromhell.HtmlComposingError:
                logger.error("Unable to render article from: %s", day)
                continue

            # Add the results to the RSS feed.
            feed.add_item(
                title=f"Current events: {day}",
                link=url,
                description=result,
                pubdate=datetime(*day.timetuple()[:3]),
            )

    if len(feed.items) == 0:
        logger.error("Created empty feed for Wikipedia current events")

    return feed.writeString("utf-8")
