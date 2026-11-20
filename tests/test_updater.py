"""Updater behavior with controlled release feeds and a fake Velopack manager."""

import io
import json
import sys
from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

import updater


@pytest.fixture
def release_feed(monkeypatch):
    monkeypatch.delenv("PDF_WATERMARK_UPDATE_URL", raising=False)
    monkeypatch.setattr(updater, "_found", None)
    monkeypatch.setattr(updater, "current_version", lambda: "1.8.1")

    def respond(request, *, timeout):
        assert request.full_url == updater.FEED
        assert timeout > 0
        return io.BytesIO(json.dumps({"Assets": [{"Version": feed.version}]}).encode())

    feed = SimpleNamespace(version="1.8.1", open=Mock(side_effect=respond), manager=Mock())
    monkeypatch.setattr(updater.urllib.request, "urlopen", feed.open)
    monkeypatch.setattr(updater, "_manager", feed.manager)
    return feed


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


def test_packaged_version_reads_the_bundled_file(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    (tmp_path / "VERSION").write_text("3.4.5\n", encoding="utf-8")
    assert updater.current_version() == "3.4.5"


def test_update_checks_skip_current_versions_and_reuse_confirmed_releases(release_feed):
    feed = release_feed
    for version in ("1.8.0", "1.8.1"):
        feed.version = version
        assert updater.check() is None, version
    feed.manager.assert_not_called()

    check = feed.manager.return_value.check_for_updates
    for version in ("1.8.2", "1.9.0"):
        feed.version = version
        check.return_value = SimpleNamespace(TargetFullRelease=SimpleNamespace(Version=version))
        first = updater.check()
        assert first is not None, version
        assert first["version"] == version
        assert first["page"] == updater.PAGE
        assert updater.check() == first
    assert check.call_count == feed.manager.call_count == 2
    assert feed.open.call_count == 6


def test_checks_recover_after_feed_or_velopack_errors(release_feed):
    feed = release_feed
    respond = feed.open.side_effect
    feed.open.side_effect = [OSError("offline"), io.BytesIO(b"invalid json")]
    assert updater.check() is None
    assert updater.check() is None
    feed.manager.assert_not_called()

    feed.version = "1.8.2"
    feed.open.side_effect = respond
    feed.manager.return_value.check_for_updates.side_effect = [
        RuntimeError("Velopack unavailable"), None,
        SimpleNamespace(TargetFullRelease=SimpleNamespace(Version=feed.version)),
    ]
    assert updater.check() is None
    assert updater.check() is None
    assert updater.check()["version"] == feed.version


def test_local_update_feed_bypasses_github(monkeypatch, tmp_path):
    monkeypatch.setenv("PDF_WATERMARK_UPDATE_URL", str(tmp_path))
    remote = Mock(side_effect=AssertionError("local check tried to read GitHub"))
    monkeypatch.setattr(updater, "latest_version", remote)
    monkeypatch.setattr(updater, "_found", None)
    velopack = Mock()
    velopack.UpdateManager.return_value.check_for_updates.return_value = SimpleNamespace(
        TargetFullRelease=SimpleNamespace(Version="1.8.2"),
    )
    monkeypatch.setitem(sys.modules, "velopack", velopack)

    assert updater.check()["version"] == "1.8.2"
    remote.assert_not_called()
    velopack.GithubSource.assert_not_called()
    velopack.UpdateManager.assert_called_once_with(str(tmp_path))


def test_install_restarts_only_after_a_successful_download():
    manager = Mock()
    info = object()
    update = {"_manager": manager, "_info": info}
    manager.download_updates.side_effect = OSError("download interrupted")
    with pytest.raises(OSError, match="download interrupted"):
        updater.install(update)
    manager.wait_exit_then_apply_updates.assert_not_called()

    manager.reset_mock(side_effect=True)
    updater.install(update)
    assert manager.mock_calls == [
        call.download_updates(info),
        call.wait_exit_then_apply_updates(info, silent=True, restart=True),
    ]
