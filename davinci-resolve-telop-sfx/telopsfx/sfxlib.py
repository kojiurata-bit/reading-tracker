"""効果音ライブラリ (ローカルフォルダのスキャン / 検索 / お気に入り)."""

import os
import unicodedata
from dataclasses import dataclass
from typing import List, Optional

AUDIO_EXTS = (".wav", ".mp3", ".aif", ".aiff", ".m4a", ".flac", ".ogg", ".caf")


@dataclass
class SfxFile:
    path: str
    name: str  # 拡張子なしのファイル名
    rel: str  # ライブラリ内の相対パス
    favorite: bool = False


def _norm(text):
    return unicodedata.normalize("NFKC", text).casefold()


def scan_folder(folder, favorites=None) -> List[SfxFile]:
    favorites = set(favorites or [])
    result = []
    if not folder or not os.path.isdir(folder):
        return result
    for root, dirs, files in os.walk(folder):
        dirs.sort()
        for fn in sorted(files):
            if fn.startswith(".") or not fn.lower().endswith(AUDIO_EXTS):
                continue
            path = os.path.join(root, fn)
            rel = os.path.relpath(path, folder)
            result.append(
                SfxFile(path=path, name=os.path.splitext(fn)[0], rel=rel, favorite=path in favorites)
            )
    return result


def filter_sfx(items: List[SfxFile], query: str, favorites_only=False) -> List[SfxFile]:
    q = _norm(query or "").strip()
    terms = q.split()
    out = []
    for it in items:
        if favorites_only and not it.favorite:
            continue
        hay = _norm(it.rel)
        if all(t in hay for t in terms):
            out.append(it)
    # お気に入りを先頭に
    out.sort(key=lambda s: (not s.favorite, _norm(s.rel)))
    return out


def find_sfx(items: List[SfxFile], name: str) -> Optional[SfxFile]:
    """"@ぴこん" のような指定にマッチする効果音を返す (完全一致 > 前方一致 > 部分一致)."""
    if not name:
        return None
    key = _norm(name)
    exact = [s for s in items if _norm(s.name) == key]
    if exact:
        return exact[0]
    prefix = [s for s in items if _norm(s.name).startswith(key)]
    if prefix:
        return prefix[0]
    partial = [s for s in items if key in _norm(s.rel)]
    return partial[0] if partial else None
