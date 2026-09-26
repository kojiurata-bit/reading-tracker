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
