from datetime import datetime

from bs4 import BeautifulSoup

import feedgenerator

from to_rss import session

STATUS_MEETINGS_DOC = "https://docs.google.com/document/d/e/2PACX-1vTWWRaJg6vfM73FWPZtJHv0uQJHnYbVM35cxmGaW1HHtsdvXkdASU0K5NpaW4Vhva0A5OHFOTpSRe3u/pub"


def thunderbird_status_meetings():
    """Return an RSS feed of Thunderbird Status Meetings."""
    response = session.get(STATUS_MEETINGS_DOC)

    # Process the HTML using BeautifulSoup!
    soup = BeautifulSoup(response.content, "html.parser")

    feed = feedgenerator.Rss201rev2Feed(
        "Thunderbird: Status Meetings",
        STATUS_MEETINGS_DOC,
        "Thunderbird: Status Meetings",
    )

    article_count = 0

    for header in soup.find_all("h1"):
        # The header should match a date of some sort.
        try:
            meeting_date = datetime.strptime(header.string, "%Y-%m-%d")
        except ValueError:
            # Likely the template.
            continue

        # Find siblings of the header and add to the content until the next
        # header (or the end of the document) is found.
        result = ""
        element = header.next_sibling
        while element and element.name != "h1":
            current = element
            element = current.next_sibling

            # If there's no content, skip.
            if not current.string:
                continue

            result += str(current)

        # Add the results to the RSS feed.
        feed.add_item(
            title=f"Status Meeting: {meeting_date}",
            link=STATUS_MEETINGS_DOC + "#" + header["id"],
            description=result,
            pubdate=meeting_date,
        )

        # Include 10 articles.
        article_count += 1
        if article_count == 10:
            break

    return feed.writeString("utf-8")
