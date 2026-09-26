"""原稿 (TelopLine) を、タイムライン上のフレーム位置 (TelopJob) に落とし込む."""

import re
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from .parsers import TelopLine
from .timecode import seconds_to_frames

_DEFAULT_MARKER_NAME = re.compile(r"^(marker|マーカー)\s*\d*$", re.IGNORECASE)

MODE_SEQUENTIAL = 0  # 再生ヘッドから順番に並べる (行頭タイムスタンプ / SRT の時間があればそれを優先)
MODE_MARKERS = 1  # マーカーの位置に 1 行ずつ
MODE_SUBTITLES = 2  # 字幕トラックの内容をそのまま Text+ に変換


@dataclass
class TelopJob:
    text: str
    start: int  # 絶対フレーム (TimelineItem.GetStart と同じ座標系)
    duration: int  # フレーム数
    sfx: Optional[str] = None
    line_no: int = 0

    @property
    def end(self):
        return self.start + self.duration


@dataclass
class MarkerInfo:
    frame: int  # タイムライン先頭からの相対フレーム
    duration: int = 1
    color: str = ""
    name: str = ""
    note: str = ""


def build_plan(
    lines: Sequence[TelopLine],
    fps: float,
    timeline_start: int,
    origin: int,
    default_duration_sec: float,
    gap_sec: float = 0.0,
    clamp_overlaps: bool = True,
) -> Tuple[List[TelopJob], List[str]]:
    """順次配置. 行にタイムスタンプがあればタイムライン先頭基準でそこに置く.

    origin: タイムスタンプの無い最初の行を置く絶対フレーム (通常は再生ヘッド).
    """
    warnings = []
    jobs = []
    cursor = origin
    default_frames = max(1, seconds_to_frames(default_duration_sec, fps))
    gap_frames = max(0, seconds_to_frames(gap_sec, fps))
    for line in lines:
        if line.start_sec is not None:
            start = timeline_start + seconds_to_frames(line.start_sec, fps)
        else:
            start = cursor
        if line.start_sec is not None and line.end_sec is not None:
            duration = seconds_to_frames(line.end_sec, fps) - seconds_to_frames(line.start_sec, fps)
        elif line.duration_sec is not None:
            duration = seconds_to_frames(line.duration_sec, fps)
        else:
            duration = default_frames
        if duration < 1:
            warnings.append("%d行目: 表示時間が0以下なので1フレームにしました" % line.line_no)
            duration = 1
        jobs.append(TelopJob(text=line.text, start=start, duration=duration, sfx=line.sfx, line_no=line.line_no))
        cursor = start + duration + gap_frames
    if clamp_overlaps:
        _clamp(jobs, warnings)
    return jobs, warnings


def build_plan_markers(
    lines: Sequence[TelopLine],
    markers: Sequence[MarkerInfo],
    fps: float,
    timeline_start: int,
    default_duration_sec: float,
    color: Optional[str] = None,
    until_next_marker: bool = False,
    use_marker_text: bool = False,
) -> Tuple[List[TelopJob], List[str]]:
    """マーカーに 1 行ずつ割り当てる. use_marker_text の場合はマーカー名/メモをテロップにする."""
    warnings = []
    selected = sorted(
        [m for m in markers if not color or color == "すべて" or m.color == color],
        key=lambda m: m.frame,
    )
    default_frames = max(1, seconds_to_frames(default_duration_sec, fps))
    jobs = []
    # source の各要素は (selected 内の位置, マーカー, 行). 位置は「次のマーカー」検索に使う
    if use_marker_text:
        source = []
        for pos, m in enumerate(selected):
            text = (m.note or m.name or "").strip()
            if text and not _DEFAULT_MARKER_NAME.match(text):
                source.append((pos, m, TelopLine(text=text, line_no=pos + 1)))
    else:
        source = [(pos, m, line) for pos, (m, line) in enumerate(zip(selected, lines))]
        if len(lines) > len(selected):
            warnings.append(
                "原稿 %d 行に対してマーカーが %d 個しかありません (%d 行は未配置)"
                % (len(lines), len(selected), len(lines) - len(selected))
            )
    for pos, m, line in source:
        start = timeline_start + m.frame
        if line.duration_sec is not None:
            duration = seconds_to_frames(line.duration_sec, fps)
        elif until_next_marker and pos + 1 < len(selected):
            duration = selected[pos + 1].frame - m.frame
        elif m.duration and m.duration > 1:
            duration = m.duration
        else:
            duration = default_frames
        duration = max(1, duration)
        jobs.append(TelopJob(text=line.text, start=start, duration=duration, sfx=line.sfx, line_no=line.line_no))
    _clamp(jobs, warnings)
    return jobs, warnings


def build_plan_from_subtitles(subtitles: Sequence[Tuple[str, int, int]]) -> Tuple[List[TelopJob], List[str]]:
    """字幕トラックの (text, start_abs, duration) をそのまま Job に."""
    jobs = [
        TelopJob(text=t, start=int(s), duration=max(1, int(d)), line_no=i)
        for i, (t, s, d) in enumerate(subtitles, 1)
        if t and t.strip()
    ]
    return jobs, []


def _clamp(jobs: List[TelopJob], warnings: List[str]):
    """同一トラック前提で、次のテロップと重なる分を切り詰める."""
    ordered = sorted(jobs, key=lambda j: j.start)
    for a, b in zip(ordered, ordered[1:]):
        if a.end > b.start:
            new_dur = b.start - a.start
            if new_dur >= 1:
                warnings.append("%d行目: 次のテロップと重なるため %d フレーム短くしました" % (a.line_no, a.duration - new_dur))
                a.duration = new_dur
