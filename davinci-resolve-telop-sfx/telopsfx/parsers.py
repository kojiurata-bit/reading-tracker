"""テロップ原稿 (テキスト / SRT) のパーサ."""

import re
from dataclasses import dataclass
from typing import List, Optional

from .timecode import hms_to_seconds

_TAG_RE = re.compile(r"<[^>]+>")
_SRT_TIME_RE = re.compile(
    r"(\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})"
)
# 行頭のタイムスタンプ: "[00:12] text", "00:12 text", "00:12-00:15 text", "1:02:03.5 text"
_LINE_TIME_RE = re.compile(
    r"^\[?\s*(\d{1,2}(?::\d{2}){1,2}(?:[.,]\d{1,3})?)"
    r"(?:\s*[-~〜]\s*(\d{1,2}(?::\d{2}){1,2}(?:[.,]\d{1,3})?))?\s*\]?[\s:：]+"
)
_SFX_TAG_RE = re.compile(r"\s@([^\s@]+)\s*$")


@dataclass
class TelopLine:
    """原稿 1 行 = テロップ 1 枚."""

    text: str
    start_sec: Optional[float] = None  # None -> 順次配置 / マーカー配置
    end_sec: Optional[float] = None
    duration_sec: Optional[float] = None  # 行末 "\t3.5" などで個別指定
    sfx: Optional[str] = None  # "@ぴこん" のような効果音指定
    line_no: int = 0


def strip_tags(text):
    return _TAG_RE.sub("", text)


def parse_srt(content: str) -> List[TelopLine]:
    """SRT を TelopLine のリストへ. 空行区切り、番号行は任意."""
    lines = content.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    result = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i].strip().lstrip("﻿")
        if not line:
            i += 1
            continue
        m = _SRT_TIME_RE.search(line)
        if not m and i + 1 < n:
            m = _SRT_TIME_RE.search(lines[i + 1])
            if m:
                i += 1
        if not m:
            i += 1
            continue
        start = hms_to_seconds(m.group(1))
        end = hms_to_seconds(m.group(2))
        i += 1
        text_lines = []
        while i < n and lines[i].strip():
            text_lines.append(strip_tags(lines[i].rstrip()))
            i += 1
        text = "\n".join(text_lines).strip()
        if text:
            tl = TelopLine(text=text, start_sec=start, end_sec=end, line_no=len(result) + 1)
            _extract_sfx_tag(tl)
            result.append(tl)
    return result


def _extract_sfx_tag(tl: TelopLine):
    m = _SFX_TAG_RE.search(tl.text)
    if m:
        tl.sfx = m.group(1)
        tl.text = tl.text[: m.start()].rstrip()


def parse_lines(content: str) -> List[TelopLine]:
    """1 行 = 1 テロップ のテキスト原稿.

    対応する書式:
      - "こんにちは"                    -> 順次 (再生ヘッド / マーカー基準) 配置
      - "こんにちは\t2.5"               -> 表示秒数を個別指定
      - "[00:12] こんにちは"            -> 12 秒地点に配置
      - "00:12-00:15 こんにちは"        -> 12 秒〜15 秒
      - "こんにちは @ぴこん"            -> 効果音 "ぴこん" を同時に挿入
      - "# コメント" / 空行             -> 無視
      - "こんにちは // 改行したい" ?    -> "\\n" と書けば Text+ 内で改行
    """
    result = []
    for idx, raw in enumerate(content.replace("\r\n", "\n").replace("\r", "\n").split("\n"), 1):
        line = raw.strip().lstrip("﻿")
        if not line or line.startswith("#"):
            continue
        tl = TelopLine(text=line, line_no=idx)
        m = _LINE_TIME_RE.match(line)
        if m:
            tl.start_sec = hms_to_seconds(m.group(1))
            if m.group(2):
                tl.end_sec = hms_to_seconds(m.group(2))
            tl.text = line[m.end():].strip()
        if "\t" in tl.text:
            body, _, dur = tl.text.rpartition("\t")
            try:
                tl.duration_sec = float(dur.strip())
                tl.text = body.strip()
            except ValueError:
                pass
        _extract_sfx_tag(tl)
        tl.text = tl.text.replace("\\n", "\n")
        if tl.text:
            result.append(tl)
    return result


def parse_auto(content: str, filename: Optional[str] = None) -> List[TelopLine]:
    """拡張子 / 内容から SRT かテキストかを判定してパースする."""
    if filename and filename.lower().endswith((".srt", ".vtt")):
        return parse_srt(content)
    if _SRT_TIME_RE.search(content):
        return parse_srt(content)
    return parse_lines(content)
