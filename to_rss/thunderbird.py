from datetime import datetime

import feedgenerator

import mwcomposerfromhell

import mwparserfromhell

from to_rss.wikipedia import get_article


def get_article_url(name):
    return 'https://wiki.mozilla.org/' + name


def get_status_meetings():
    """Get the list of status meetings."""
    url = get_article_url('Thunderbird/StatusMeetings')

    # Download the article.
    data = get_article(url)
    # Parse the contents.
    wikicode = mwparserfromhell.parse(data)

    # Each table represents a year.
    for table in wikicode.ifilter_tags(recursive=False, matches=lambda el: el.tag == 'table'):
        # Each link in the contents is a separate meeting.
        for meeting_link in table.contents.ifilter_wikilinks(recursive=True):
            # Convert the text title to a real date (e.g. from Jan 22, 2019).
            # Unfortunately some of the dates use the full month, not the short
            # month. So try both.
            try:
                meeting_date = datetime.strptime(str(meeting_link.text), '%b %d, %Y')
            except ValueError:
                meeting_date = datetime.strptime(str(meeting_link.text), '%B %d, %Y')

            yield meeting_date.date(), str(meeting_link.title)


def thunderbird_status_meetings():
    """Return an RSS feed of Thunderbird Status Meetings."""
    feed = feedgenerator.Rss201rev2Feed('Thunderbird: Status Meetings',
                                        get_article_url('Thunderbird/StatusMeetings'),
                                        'Thunderbird: Status Meetings')

    article_count = 0

    for meeting_date, meeting_title in get_status_meetings():
        # Download the article content.
        url = get_article_url(meeting_title)
        meeting_notes = get_article(url)

        # If the article isn't there, skip it.
        if not meeting_notes:
            continue

        # Parse the article contents.
        wikicode = mwparserfromhell.parse(meeting_notes)

        try:
            feed.add_item(title=u'Status Meeting: {}'.format(meeting_date),
                          link=url,
                          # Convert the Wikicode to HTML.
                          description=mwcomposerfromhell.compose(wikicode),
                          pubdate=datetime(*meeting_date.timetuple()[:3]))
        except mwcomposerfromhell.HtmlComposingError:
            print("Unable to render article from: {}".format(meeting_date))

        # Include 10 articles.
        article_count += 1
        if article_count == 10:
            break

    return feed.writeString('utf-8')
