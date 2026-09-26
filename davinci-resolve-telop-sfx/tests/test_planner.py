from telopsfx.parsers import TelopLine, parse_lines
from telopsfx.planner import MarkerInfo, build_plan, build_plan_from_subtitles, build_plan_markers


def test_sequential_from_playhead():
    lines = parse_lines("A\nB\t2\nC")
    jobs, warnings = build_plan(lines, 24, timeline_start=86400, origin=86400 + 240, default_duration_sec=3, gap_sec=0.5)
    assert [(j.start, j.duration) for j in jobs] == [
        (86640, 72),
        (86640 + 72 + 12, 48),
        (86640 + 72 + 12 + 48 + 12, 72),
    ]
    assert warnings == []


def test_timestamped_lines_are_relative_to_timeline_start():
    lines = parse_lines("[00:10] A\nB\n00:20-00:22 C")
    jobs, _ = build_plan(lines, 24, timeline_start=86400, origin=0, default_duration_sec=3)
    assert jobs[0].start == 86400 + 240
    assert jobs[1].start == jobs[0].end  # 続きから
    assert jobs[2].start == 86400 + 480 and jobs[2].duration == 48


def test_overlap_clamped():
    lines = [TelopLine("A", start_sec=0, end_sec=5, line_no=1), TelopLine("B", start_sec=3, end_sec=6, line_no=2)]
    jobs, warnings = build_plan(lines, 24, 0, 0, 3)
    assert jobs[0].duration == 72
    assert len(warnings) == 1


def test_markers_assignment_and_color_filter():
    lines = parse_lines("A\nB\nC")
    markers = [MarkerInfo(100, 1, "Blue"), MarkerInfo(50, 1, "Red"), MarkerInfo(200, 48, "Blue")]
    jobs, warnings = build_plan_markers(lines, markers, 24, 1000, 2.0, color="Blue")
    assert [(j.start, j.duration, j.text) for j in jobs] == [(1100, 48, "A"), (1200, 48, "B")]
    assert warnings and "1 行は未配置" in warnings[0]


def test_markers_until_next():
    lines = parse_lines("A\nB")
    markers = [MarkerInfo(0), MarkerInfo(30), MarkerInfo(90)]
    jobs, _ = build_plan_markers(lines, markers, 24, 0, 5.0, until_next_marker=True)
    assert [(j.start, j.duration) for j in jobs] == [(0, 30), (30, 60)]


def test_markers_use_marker_text():
    markers = [MarkerInfo(0, name="Marker 1", note="ここが見どころ"), MarkerInfo(24, name="Marker 2", note="")]
    jobs, _ = build_plan_markers([], markers, 24, 0, 1.0, use_marker_text=True)
    assert [j.text for j in jobs] == ["ここが見どころ"]


def test_from_subtitles():
    jobs, _ = build_plan_from_subtitles([("A", 10, 20), ("", 40, 5), ("B", 50, 0)])
    assert [(j.text, j.start, j.duration) for j in jobs] == [("A", 10, 20), ("B", 50, 1)]


def test_markers_use_marker_text_until_next_skips_default_names():
    markers = [MarkerInfo(frame=0, name="Marker 1"), MarkerInfo(frame=100, name="A"),
               MarkerInfo(frame=200, name="B"), MarkerInfo(frame=300, name="C")]
    jobs, _ = build_plan_markers([], markers, 30, 0, 2.0, until_next_marker=True, use_marker_text=True)
    assert [(j.text, j.start, j.duration) for j in jobs] == [("A", 100, 100), ("B", 200, 100), ("C", 300, 60)]
