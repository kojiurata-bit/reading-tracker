import pytest

from telopsfx.parsers import parse_auto, parse_lines, parse_srt


def test_parse_lines_basic():
    lines = parse_lines("# comment\n\nこんにちは\n世界\t2.5\n")
    assert [l.text for l in lines] == ["こんにちは", "世界"]
    assert lines[0].duration_sec is None
    assert lines[1].duration_sec == 2.5
    assert lines[0].line_no == 3


def test_parse_lines_timestamps():
    lines = parse_lines("[00:12] ここから\n00:20-00:24 価格\n1:02:03.5 長い\n00:30: コロン区切り")
    assert lines[0].start_sec == 12 and lines[0].text == "ここから"
    assert lines[1].start_sec == 20 and lines[1].end_sec == 24 and lines[1].text == "価格"
    assert lines[2].start_sec == 3723.5
    assert lines[3].start_sec == 30 and lines[3].text == "コロン区切り"


def test_parse_lines_sfx_and_newline():
    lines = parse_lines("発表会です @ぴこん\n1行目\\n2行目")
    assert lines[0].text == "発表会です" and lines[0].sfx == "ぴこん"
    assert lines[1].text == "1行目\n2行目" and lines[1].sfx is None


def test_parse_lines_tab_and_sfx_together():
    (line,) = parse_lines("テスト @ドン\t1.5")
    assert line.text == "テスト" and line.sfx == "ドン" and line.duration_sec == 1.5


def test_parse_srt():
    srt = """1
00:00:01,000 --> 00:00:03,500
こんにちは
二行目

2
00:00:04,000 --> 00:00:07,000
<b>太字</b>タグは除去 @ぴこん
"""
    lines = parse_srt(srt)
    assert len(lines) == 2
    assert lines[0].text == "こんにちは\n二行目"
    assert lines[0].start_sec == 1.0 and lines[0].end_sec == 3.5
    assert lines[1].text == "太字タグは除去" and lines[1].sfx == "ぴこん"


def test_parse_srt_without_index_lines_and_crlf():
    srt = "00:00:01.000 --> 00:00:02.000\r\nA\r\n\r\n00:00:03.000 --> 00:00:04.000\r\nB\r\n"
    lines = parse_srt(srt)
    assert [l.text for l in lines] == ["A", "B"]


def test_parse_auto_detects_srt_by_content():
    lines = parse_auto("1\n00:00:01,000 --> 00:00:02,000\nX\n")
    assert lines[0].end_sec == 2.0
    lines = parse_auto("ただの行\n")
    assert lines[0].start_sec is None


def test_parse_srt_without_blank_separator():
    srt = "1\n00:00:01,000 --> 00:00:02,000\nHello\n2\n00:00:03,000 --> 00:00:04,000\nWorld"
    lines = parse_srt(srt)
    assert [(l.text, l.start_sec, l.end_sec) for l in lines] == [("Hello", 1.0, 2.0), ("World", 3.0, 4.0)]
    # a pure-digit text line not followed by a timing line is still subtitle text
    assert parse_srt("1\n00:00:01,000 --> 00:00:02,000\nHello\n2024\n")[0].text == "Hello\n2024"


def test_parse_vtt_short_form_timestamps():
    content = "WEBVTT\n\n00:01.000 --> 00:02.000 align:start\nhello\n\n00:00:03.000 --> 00:00:04.000\nworld\n"
    res = parse_auto(content, "a.vtt")
    assert [(t.text, t.start_sec, t.end_sec) for t in res] == [("hello", 1.0, 2.0), ("world", 3.0, 4.0)]


def test_bracket_without_space():
    lines = parse_lines("[00:12]こんにちは\n[00:20-00:24]価格")
    assert (lines[0].text, lines[0].start_sec) == ("こんにちは", 12.0)
    assert (lines[1].text, lines[1].start_sec, lines[1].end_sec) == ("価格", 20.0, 24.0)


def test_tab_duration_fullwidth_and_non_finite():
    lines = parse_lines("世界\t２．５\nA\tnan\nB\tinf\nC\tabc")
    assert (lines[0].text, lines[0].duration_sec) == ("世界", 2.5)
    assert lines[1].duration_sec is None and lines[1].text == "A\tnan"
    assert lines[2].duration_sec is None and lines[2].text == "B\tinf"
    assert lines[3].duration_sec is None and lines[3].text == "C\tabc"


def test_read_script_text_encodings(tmp_path):
    from telopsfx.engine import load_script_file, read_script_text

    sjis = tmp_path / "sjis.txt"
    sjis.write_bytes("こんにちは\n世界\t2\n".encode("cp932"))
    assert read_script_text(str(sjis)) == "こんにちは\n世界\t2\n"
    assert [(l.text, l.duration_sec) for l in load_script_file(str(sjis))] == [("こんにちは", None), ("世界", 2.0)]

    bom = tmp_path / "bom.txt"
    bom.write_bytes("\ufeffこんにちは\n".encode("utf-8"))
    assert read_script_text(str(bom)) == "こんにちは\n"

    u16 = tmp_path / "u16.txt"
    u16.write_bytes("こんにちは\n".encode("utf-16"))
    assert read_script_text(str(u16)) == "こんにちは\n"

    bad = tmp_path / "bad.bin"
    bad.write_bytes(b"\xff\xfe\x00\xd8\x80\x81\xff\xff\x81")  # UTF-16 BOM だが壊れている & CP932 でも不正
    with pytest.raises(OSError):
        read_script_text(str(bad))
    with pytest.raises(OSError):
        read_script_text(str(tmp_path / "missing.txt"))
