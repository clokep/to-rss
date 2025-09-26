import os

os.environ["DISABLE_CACHED_SESSION"] = "true"


def assert_items_count(contents: str, count: int) -> None:
    assert contents.count("<item>") == count


def assert_items_exists(contents: str) -> None:
    assert contents.count("<item>") > 0
