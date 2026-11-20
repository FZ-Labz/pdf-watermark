"""
The update check's version handling. The parts that talk to Velopack and
GitHub only run in the installed app; these are the pure helpers they use.
"""

import updater


def test_version_key_orders_numerically():
    assert updater.version_key("1.10.0") > updater.version_key("1.9.9")
    assert updater.version_key("1.8.1") > updater.version_key("1.2.1")
    assert updater.version_key("2.0") == (2, 0, 0)
    assert updater.version_key("v1.2.3") == (1, 2, 3)


def test_version_key_ignores_prerelease_labels_like_velopack():
    # Velopack treats an installed 1.2.1-test.1 as 1.2.1, so the check must too.
    assert updater.version_key("1.2.1-test.1") == updater.version_key("1.2.1")


def test_version_key_survives_rubbish():
    assert updater.version_key("") == (0, 0, 0)
    assert updater.version_key("not a version") == (0, 0, 0)


def test_newest_in_feed_picks_the_highest_full_package():
    feed = {"Assets": [
        {"Version": "1.2.1", "Type": "Full"},
        {"Version": "1.10.0", "Type": "Full"},
        {"Version": "1.9.0", "Type": "Full"},
        {"Version": "2.0.0", "Type": "Delta"},
    ]}
    assert updater.newest_in_feed(feed) == "1.10.0"


def test_newest_in_feed_of_an_empty_feed():
    assert updater.newest_in_feed({}) is None
    assert updater.newest_in_feed({"Assets": []}) is None


def test_current_version_reads_the_version_file():
    assert updater.current_version() == (updater.Path(updater.__file__).parent / "VERSION").read_text().strip()
