from xml.etree import ElementTree

import pytest

from tests import assert_items_exists
from to_rss.nhl import VALID_TEAMS, nhl_news, team_news


def _get_items(contents: str) -> list[tuple[str, list[str]]]:
    """Return one (link, categories) tuple per item in the feed."""
    items = []
    for item in ElementTree.fromstring(contents).findall(".//item"):
        link = item.find("link")
        categories = [
            node.text for node in item.findall("category") if node.text is not None
        ]
        items.append((link.text if link is not None and link.text else "", categories))
    return items


@pytest.mark.parametrize("team_name", VALID_TEAMS.keys())
def test_nhl_team(team_name):
    result = team_news(team_name)
    assert_items_exists(result)

    # Each team feed picks up the previews of its own games (the filtering of
    # the league-wide previews to a single team is covered by
    # test_filter_previews_keeps_only_own_games; team pages also embed other
    # teams' previews, e.g. the Sabres' "season in review" module, which pass
    # through as-published).
    items = _get_items(result)
    assert any("Game Preview" in categories for _, categories in items)


def test_nhl_news():
    result = nhl_news()
    assert_items_exists(result)

    # The game preview articles dropped from nhl.com's main feed are merged in.
    items = _get_items(result)
    assert any("Game Preview" in categories for _, categories in items)
