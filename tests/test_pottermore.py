from tests import assert_items_exists
from to_rss.pottermore import pottermore_features, pottermore_news


def test_pottermore_features():
    result = pottermore_features()
    assert_items_exists(result)


def test_pottermore_news():
    result = pottermore_news()
    assert_items_exists(result)
