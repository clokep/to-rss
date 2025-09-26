import pytest

from tests import assert_items_exists
from to_rss.nhl import VALID_TEAMS, nhl_news, team_news


@pytest.mark.parametrize("team_name", VALID_TEAMS.keys())
def test_nhl_team(team_name):
    result = team_news(team_name)
    assert_items_exists(result)


def test_nhl_news():
    result = nhl_news()
    assert_items_exists(result)
