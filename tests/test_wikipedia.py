from tests import assert_items_exists
from to_rss.wikipedia import get_articles


def test_current_events():
    result = get_articles()
    assert_items_exists(result)
