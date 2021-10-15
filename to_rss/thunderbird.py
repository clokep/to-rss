from datetime import datetime
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

import feedgenerator

from to_rss import get_session

STATUS_MEETINGS_DOC = "https://docs.google.com/document/d/e/2PACX-1vTWWRaJg6vfM73FWPZtJHv0uQJHnYbVM35cxmGaW1HHtsdvXkdASU0K5NpaW4Vhva0A5OHFOTpSRe3u/pub"


def _clean_html(element) -> None:
    """
    Cleans a Tag to simplify the resulting HTML.
    """
    # If a string is found, nothing to do.
    if element.name is None:
        return

    # Remove spans and replace with the contents.
    if element.name == "span":
        for child in element.children:
            _clean_html(child)
            element.insert_before(child)
        element.decompose()
        return

    # Remove the redirects via Google. The real URL is stored in the q query
    # parameter.
    if element.name == "a":
        element["href"] = parse_qs(urlparse(element["href"]).query)["q"][0]

    # Remove attributes related to stylesheets which are unused.
    element.attrs.pop("id", None)
    element.attrs.pop("class", None)

    # And clean any children.
    for child in element.children:
        _clean_html(child)


def _get_level(element):
    """Find the indentation level of a <ul>."""
    for c in element["class"]:
        if c.startswith("lst-kix_"):
            return int(c[c.rfind("-") + 1 :])

    raise ValueError(f'No indentation level found: {element["class"]}')


def thunderbird_status_meetings():
    """Return an RSS feed of Thunderbird Status Meetings."""
    response = get_session().get(STATUS_MEETINGS_DOC)

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

        # Create a new section that we'll work in.
        section = soup.new_tag("div")
        header.insert_after(section)

        # Find siblings of the header and add to the section until the next
        # header (or the end of the document) is found.
        element = section.next_sibling
        while element and element.name != "h1":
            section.append(element)
            element = section.next_sibling

        # Process that section to clean it up a bit.
        for child in section.children:
            # Remove children which have no string content.
            if not child.string and not any(child.strings):
                child.decompose()
                continue

            # Google Docs doesn't properly nest list elements.
            if child.name == "ul":
                last = child
                sibling = child.next_sibling

                while sibling and sibling.name == "ul":
                    sibling_level = _get_level(sibling)
                    last_level = _get_level(last)

                    # If the level is further indented, move it under the last element.
                    if sibling_level > last_level:
                        last.append(sibling.extract())
                        last = sibling

                    # If it is less indented than the last, move up one or more levels.
                    elif sibling_level <= last_level:
                        for _ in range(last_level - sibling_level):
                            last = last.parent

                        # Copy the contents into the parent.
                        for c in sibling.children:
                            last.append(c.extract())
                        sibling.decompose()

                    # Move to the next element.
                    sibling = child.next_sibling

        # Clean-up the HTML a bit.
        _clean_html(section)

        # Add the results to the RSS feed.
        feed.add_item(
            title=f"Status Meeting: {meeting_date}",
            link=STATUS_MEETINGS_DOC + "#" + header["id"],
            description=str(section),
            pubdate=meeting_date,
        )

        # Include 10 articles.
        article_count += 1
        if article_count == 10:
            break

    return feed.writeString("utf-8")
