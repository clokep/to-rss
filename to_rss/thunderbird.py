from datetime import datetime

import feedgenerator

import mwcomposerfromhell

import mwparserfromhell

from to_rss.wikipedia import get_article


def get_status_meetings(resolver):
    """Get the list of status meetings."""
    url = resolver.get_article_url(
        resolver.resolve_article("Thunderbird/StatusMeetings", "")
    )

    # Download the article.
    data = get_article(url)
    # Parse the contents.
    wikicode = mwparserfromhell.parse(data)

    # Each table represents a year.
    for table in wikicode.ifilter_tags(
        recursive=False, matches=lambda el: el.tag == "table"
    ):
        # Each link in the contents is a separate meeting.
        for meeting_link in table.contents.ifilter_wikilinks(recursive=True):
            # Convert the text title to a real date (e.g. from Jan 22, 2019).
            # Unfortunately some of the dates use the full month, not the short
            # month. So try both.
            try:
                meeting_date = datetime.strptime(str(meeting_link.text), "%b %d, %Y")
            except ValueError:
                meeting_date = datetime.strptime(str(meeting_link.text), "%B %d, %Y")

            yield meeting_date.date(), str(meeting_link.title)


def thunderbird_status_meetings():
    """Return an RSS feed of Thunderbird Status Meetings."""
    # Add custom templates that are necessary.
    templates = mwcomposerfromhell.Namespace(
        {
            # See https://wiki.mozilla.org/Template:Bug
            "bug": mwparserfromhell.parse(
                "[https://bugzilla.mozilla.org/show_bug.cgi?id={{{1}}} {{{2|bug {{{1}}}}}}]"
            ),
        }
    )
    resolver = mwcomposerfromhell.ArticleResolver(base_url="https://wiki.mozilla.org/")
    resolver.add_namespace("Template", templates)

    feed = feedgenerator.Rss201rev2Feed(
        "Thunderbird: Status Meetings",
        resolver.get_article_url(
            resolver.resolve_article("Thunderbird/StatusMeetings", "")
        ),
        "Thunderbird: Status Meetings",
    )

    article_count = 0

    for meeting_date, meeting_title in get_status_meetings(resolver):
        # Download the article content.
        url = resolver.get_article_url(resolver.resolve_article(meeting_title, ""))
        meeting_notes = get_article(url)

        # If the article isn't there, skip it.
        if not meeting_notes:
            continue

        # Parse the article contents.
        wikicode = mwparserfromhell.parse(meeting_notes)

        # Create a new composer with some templates pre-built into it.
        composer = mwcomposerfromhell.WikicodeToHtmlComposer(resolver=resolver)

        try:
            # Convert the Wikicode to HTML.
            result = composer.compose(wikicode)
        except mwcomposerfromhell.HtmlComposingError:
            print(f"Unable to render status meeting notes from: {meeting_date}")
            continue

        # Add the results to the RSS feed.
        feed.add_item(
            title=f"Status Meeting: {meeting_date}",
            link=url,
            description=result,
            pubdate=datetime(*meeting_date.timetuple()[:3]),
        )

        # Include 10 articles.
        article_count += 1
        if article_count == 10:
            break

    return feed.writeString("utf-8")
