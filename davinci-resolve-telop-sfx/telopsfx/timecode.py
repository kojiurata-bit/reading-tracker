"""タイムコード・フレーム・秒の相互変換 (Resolve 非依存)."""

import math
import re

_TC_RE = re.compile(r"^(\d{1,2})[:;](\d{2})[:;](\d{2})[:;](\d{2,3})$")


def parse_fps(value):
    """Resolve の GetSetting("timelineFrameRate") 等の文字列を float に変換する."""
    if value is None:
        raise ValueError("fps が取得できません")
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().upper().replace("DF", "").strip()
    return float(text)


def timecode_base(fps):
    """タイムコードの桁が進む基準 fps (29.97 -> 30, 23.976 -> 24)."""
    return int(round(fps))


def is_drop_frame_fps(fps):
    base = timecode_base(fps)
    return abs(fps - base) > 0.001 and base in (30, 60, 120)


def seconds_to_frames(seconds, fps):
    return int(round(float(seconds) * fps))


def frames_to_seconds(frames, fps):
    return float(frames) / fps


def timecode_to_frame(tc, fps, drop_frame=None):
    """タイムコード文字列を絶対フレームに変換する.

    drop_frame が None の場合は区切り文字 ';' か fps から推定する.
    """
    m = _TC_RE.match(tc.strip())
    if not m:
        raise ValueError("タイムコードの形式が不正です: %r" % tc)
    hh, mm, ss, ff = (int(x) for x in m.groups())
    base = timecode_base(fps)
    if drop_frame is None:
        drop_frame = ";" in tc
    drop_frame = bool(drop_frame) and is_drop_frame_fps(fps)  # 非 DF レートでは DF 指定を無視 (frame_to_timecode と同じ)
    if not drop_frame:
        return ((hh * 60 + mm) * 60 + ss) * base + ff
    # ドロップフレーム: 毎分 (10分毎を除く) 先頭の 2 (or 4) フレームを飛ばす
    drop = 2 if base == 30 else 4 if base == 60 else 8
    total_minutes = hh * 60 + mm
    frame = ((hh * 3600 + mm * 60 + ss) * base + ff)
    frame -= drop * (total_minutes - total_minutes // 10)
    return frame


def frame_to_timecode(frame, fps, drop_frame=False):
    base = timecode_base(fps)
    frame = int(frame)
    if drop_frame and is_drop_frame_fps(fps):
        drop = 2 if base == 30 else 4 if base == 60 else 8
        frames_per_10min = base * 600 - drop * 9
        frames_per_min = base * 60 - drop
        d = frame // frames_per_10min
        m = frame % frames_per_10min
        if m > drop:
            frame += drop * 9 * d + drop * ((m - drop) // frames_per_min)
        else:
            frame += drop * 9 * d
        sep = ";"
    else:
        sep = ":"
    ff = frame % base
    total_sec = frame // base
    ss = total_sec % 60
    mm = (total_sec // 60) % 60
    hh = (total_sec // 3600) % 24
    return "%02d:%02d:%02d%s%02d" % (hh, mm, ss, sep, ff)


_HMS_RE = re.compile(
    r"^(?:(\d{1,2}):)?(\d{1,2}):(\d{2})(?:[.,](\d{1,3}))?$"
)


def hms_to_seconds(text):
    """'1:23', '01:02:03', '01:02:03.500', '00:01:02,500' -> 秒 (float)."""
    m = _HMS_RE.match(text.strip())
    if not m:
        raise ValueError("時刻の形式が不正です: %r" % text)
    hh, mm, ss, ms = m.groups()
    seconds = int(mm) * 60 + int(ss)
    if hh:
        seconds += int(hh) * 3600
    if ms:
        seconds += int(ms.ljust(3, "0")) / 1000.0
    return float(seconds)


def ceil_frames(seconds, fps):
    return int(math.ceil(float(seconds) * fps - 1e-9))
