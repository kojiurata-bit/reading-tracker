import pytest

from telopsfx.timecode import (
    frame_to_timecode,
    hms_to_seconds,
    parse_fps,
    seconds_to_frames,
    timecode_to_frame,
)


def test_parse_fps():
    assert parse_fps("24") == 24.0
    assert parse_fps("29.97 DF") == pytest.approx(29.97)
    assert parse_fps(30) == 30.0


def test_non_drop_roundtrip():
    for fps in (24.0, 25.0, 30.0, 23.976, 60.0):
        for frame in (0, 1, 86399, 86400, 123456):
            tc = frame_to_timecode(frame, fps)
            assert timecode_to_frame(tc, fps) == frame


def test_drop_frame_roundtrip():
    for frame in (0, 1, 1798, 1799, 1800, 17982, 17983, 107892, 500000):
        tc = frame_to_timecode(frame, 29.97, drop_frame=True)
        assert ";" in tc
        assert timecode_to_frame(tc, 29.97, drop_frame=True) == frame


def test_drop_frame_known_values():
    # 1 分の頭で ;00 ;01 がスキップされるので 00:01:00;02 は 1800 フレーム目
    assert timecode_to_frame("00:01:00;02", 29.97, True) == 1800
    assert frame_to_timecode(1800, 29.97, True) == "00:01:00;02"
    assert frame_to_timecode(1799, 29.97, True) == "00:00:59;29"
    # 10 分の位置はスキップしない
    assert frame_to_timecode(17982, 29.97, True) == "00:10:00;00"


def test_start_tc_one_hour():
    assert timecode_to_frame("01:00:00:00", 24) == 86400
    assert timecode_to_frame("01:00:00:00", 29.97) == 108000


def test_hms():
    assert hms_to_seconds("1:23") == 83
    assert hms_to_seconds("01:02:03") == 3723
    assert hms_to_seconds("00:00:01,500") == 1.5
    assert hms_to_seconds("00:00:01.5") == 1.5
    with pytest.raises(ValueError):
        hms_to_seconds("abc")


def test_seconds_to_frames():
    assert seconds_to_frames(2.5, 24) == 60
    assert seconds_to_frames(1, 29.97) == 30
