import mwparserfromhell

from tests import assert_items_exists
from to_rss.wikipedia import extract_content, get_articles

# The layout used until mid-2026: the day's news lives in the template's
# "content" parameter.
LEGACY_ARTICLE = """{{Current events|year=2026|month=07|day=20|content=
<!-- All news items below this line -->
'''Armed conflicts and attacks'''
*[[Example conflict]]
<!-- All news items above this line -->}}
"""

# The layout used since: a "top=yes" template, the news, then a "bottom=yes" one.
SANDWICH_ARTICLE = """{{Current events|year=2026|month=08|day=2|top=yes}}

<!-- All news items below this line -->
'''Armed conflicts and attacks'''
*[[Example conflict]]
{{Current events|year=2026|month=08|day=2|bottom=yes}}"""


def test_current_events():
    result = get_articles()
    assert_items_exists(result)


def test_extract_content_legacy():
    content = extract_content(mwparserfromhell.parse(LEGACY_ARTICLE))
    assert "Armed conflicts and attacks" in str(content)
    assert "[[Example conflict]]" in str(content)


def test_extract_content_sandwich():
    content = extract_content(mwparserfromhell.parse(SANDWICH_ARTICLE))
    assert "Armed conflicts and attacks" in str(content)
    assert "[[Example conflict]]" in str(content)
    # The wrapping templates themselves must not leak into the output.
    assert "Current events" not in str(content)


def test_extract_content_missing_template():
    assert extract_content(mwparserfromhell.parse("''Nothing to see here.''")) is None
