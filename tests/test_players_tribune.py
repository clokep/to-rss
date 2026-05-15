import pytest

from tests import assert_items_exists
from to_rss.players_tribune import VALID_SPORTS, sports_news


@pytest.mark.parametrize("sport_name", VALID_SPORTS.keys())
def test_players_tribune(sport_name):
    result = sports_news(sport_name)
    assert_items_exists(result)
