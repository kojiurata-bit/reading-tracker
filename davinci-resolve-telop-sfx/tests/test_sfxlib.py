from telopsfx.sfxlib import filter_sfx, find_sfx, scan_folder


def test_scan_filter_find(tmp_path):
    (tmp_path / "ピコン.wav").write_bytes(b"")
    (tmp_path / "ぴこん2.WAV").write_bytes(b"")
    (tmp_path / "readme.txt").write_bytes(b"")
    (tmp_path / "hit").mkdir()
    (tmp_path / "hit" / "Drum Roll.mp3").write_bytes(b"")
    items = scan_folder(str(tmp_path), favorites=[str(tmp_path / "hit" / "Drum Roll.mp3")])
    assert len(items) == 3
    assert filter_sfx(items, "drum roll")[0].name == "Drum Roll"
    assert [s.name for s in filter_sfx(items, "")][0] == "Drum Roll"  # お気に入りが先頭
    assert filter_sfx(items, "", favorites_only=True)[0].favorite
    assert find_sfx(items, "ﾋﾟｺﾝ").name == "ピコン"  # NFKC で半角カナも一致
    assert find_sfx(items, "ぴこん").name == "ぴこん2"
    assert find_sfx(items, "roll").name == "Drum Roll"
    assert find_sfx(items, "なし") is None


def test_scan_missing_folder():
    assert scan_folder("/nonexistent/path") == []
