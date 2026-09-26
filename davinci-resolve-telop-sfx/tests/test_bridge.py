import os

import pytest

from fake_resolve import FakeResolve
from telopsfx.engine import TelopOptions, plan_telops, run_sfx_at_markers, run_telops
from telopsfx.parsers import parse_lines
from telopsfx.planner import MODE_MARKERS, MODE_SUBTITLES
from telopsfx.resolve_bridge import ResolveBridge, ResolveError
from telopsfx.sfxlib import SfxFile


@pytest.fixture
def sfx_dir(tmp_path):
    (tmp_path / "ぴこん.wav").write_bytes(b"x")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "drumroll.mp3").write_bytes(b"x")
    return tmp_path


def _lib(sfx_dir):
    return [
        SfxFile(str(sfx_dir / "ぴこん.wav"), "ぴこん", "ぴこん.wav"),
        SfxFile(str(sfx_dir / "sub" / "drumroll.mp3"), "drumroll", os.path.join("sub", "drumroll.mp3")),
    ]


@pytest.mark.parametrize("record_relative", [False, True])
@pytest.mark.parametrize("end_exclusive", [False, True])
def test_telops_land_at_exact_frames_regardless_of_api_semantics(record_relative, end_exclusive, sfx_dir):
    fake = FakeResolve(fps=24, record_relative=record_relative, end_exclusive=end_exclusive)
    fake.add_template("Text+", frames=240)
    fake.timeline.playhead = fake.timeline.start_frame + 100
    bridge = ResolveBridge(fake, print)
    lines = parse_lines("こんにちは @ぴこん\nつぎ\t2\n[00:30] 三枚目")
    opt = TelopOptions(default_duration_sec=3, video_track=2, audio_track=2, sfx_library=_lib(sfx_dir))
    jobs, warnings = plan_telops(bridge, lines, opt)
    res = run_telops(bridge, jobs, opt, print)

    assert res.errors == []
    assert res.telops == 3 and res.sfx == 1
    v2 = fake.timeline.tracks["video"][2]
    assert [(i.start, i.duration) for i in v2] == [
        (86500, 72), (86572, 48), (86400 + 720, 72),
    ]
    assert [i.comp.tool.inputs["StyledText"] for i in v2] == ["こんにちは", "つぎ", "三枚目"]
    assert v2[0].name == "こんにちは"
    a2 = fake.timeline.tracks["audio"][2]
    assert [(i.start, i.duration) for i in a2] == [(86500, 48)]
    assert fake.media_pool.imported == [str(sfx_dir / "ぴこん.wav")]
    # 補正で消した仮クリップが残っていない
    assert len(fake.timeline.tracks["video"][2]) == 3


def test_preset_applied_and_clip_color():
    fake = FakeResolve()
    fake.add_template()
    bridge = ResolveBridge(fake)
    preset = {"Font": "Hiragino Sans", "Size": 0.08, "Center": [0.5, 0.12], "ClipColor": "Yellow"}
    opt = TelopOptions(default_duration_sec=1, video_track=1, preset=preset)
    jobs, _ = plan_telops(bridge, parse_lines("A"), opt)
    run_telops(bridge, jobs, opt)
    item = fake.timeline.tracks["video"][1][0]
    assert item.comp.tool.inputs["Font"] == "Hiragino Sans"
    assert item.comp.tool.inputs["Center"] == {1: 0.5, 2: 0.12}
    assert "ClipColor" not in item.comp.tool.inputs
    assert item.color == "Yellow"
    assert item.comp.locked == 0


def test_auto_free_track_moves_overlapping_telops_up():
    fake = FakeResolve()
    tmpl = fake.add_template()
    fake.timeline.tracks["video"][2] = []
    fake.timeline.add_item("video", 2, tmpl, fake.timeline.start_frame, 48)  # 既存クリップ
    bridge = ResolveBridge(fake)
    opt = TelopOptions(default_duration_sec=1, video_track=2, auto_free_track=True)
    jobs, _ = plan_telops(bridge, parse_lines("A\nB\nC"), opt)
    run_telops(bridge, jobs, opt)
    assert len(fake.timeline.tracks["video"][2]) == 1 + 1  # 既存 + C (48 フレーム以降は空いている)
    assert len(fake.timeline.tracks["video"][3]) == 2  # A, B は上に逃げる


def test_tracks_are_created_when_missing():
    fake = FakeResolve()
    fake.add_template()
    bridge = ResolveBridge(fake)
    opt = TelopOptions(default_duration_sec=1, video_track=4, auto_free_track=False)
    jobs, _ = plan_telops(bridge, parse_lines("A"), opt)
    run_telops(bridge, jobs, opt)
    assert fake.timeline.GetTrackCount("video") == 4
    assert len(fake.timeline.tracks["video"][4]) == 1


def test_fallback_without_template_uses_insert_fusion_title():
    fake = FakeResolve()
    bridge = ResolveBridge(fake)
    opt = TelopOptions(default_duration_sec=1, video_track=1, template_name="Text+")
    jobs, _ = plan_telops(bridge, parse_lines("[00:05] A"), opt)
    res = run_telops(bridge, jobs, opt)
    assert res.telops == 1 and any("代替" in w for w in res.warnings)
    item = fake.timeline.tracks["video"][1][0]
    assert item.start == fake.timeline.start_frame + 120
    assert item.comp.tool.inputs["StyledText"] == "A"


def test_template_too_short_warns():
    fake = FakeResolve()
    fake.add_template(frames=24)
    bridge = ResolveBridge(fake)
    opt = TelopOptions(default_duration_sec=5, video_track=1)
    jobs, _ = plan_telops(bridge, parse_lines("A"), opt)
    res = run_telops(bridge, jobs, opt)
    assert any("尺" in w for w in res.warnings)
    assert fake.timeline.tracks["video"][1][0].duration == 24


def test_markers_mode_and_marker_sfx(sfx_dir):
    fake = FakeResolve(fps=30, start_tc="00:00:00:00")
    fake.add_template()
    fake.timeline.markers = {30: {"color": "Blue", "name": "Marker 1", "note": "", "duration": 1},
                             90: {"color": "Red", "name": "Marker 2", "note": "", "duration": 1}}
    bridge = ResolveBridge(fake)
    opt = TelopOptions(mode=MODE_MARKERS, default_duration_sec=2, video_track=1, marker_color="すべて")
    jobs, _ = plan_telops(bridge, parse_lines("A\nB"), opt)
    run_telops(bridge, jobs, opt)
    assert [(i.start, i.duration) for i in fake.timeline.tracks["video"][1]] == [(30, 60), (90, 60)]
    res = run_sfx_at_markers(bridge, str(sfx_dir / "ぴこん.wav"), 1, True, "Red")
    assert res.sfx == 1
    assert [i.start for i in fake.timeline.tracks["audio"][1]] == [90]


def test_subtitle_mode():
    fake = FakeResolve()
    fake.add_template()
    fake.timeline.tracks["subtitle"][1] = []
    from fake_resolve import FakeClip
    fake.timeline.add_item("subtitle", 1, FakeClip("こんにちは", ctype="Subtitle"), 86400, 40)
    fake.timeline.add_item("subtitle", 1, FakeClip("さようなら", ctype="Subtitle"), 86450, 30)
    bridge = ResolveBridge(fake)
    opt = TelopOptions(mode=MODE_SUBTITLES, subtitle_track=1, video_track=2)
    jobs, _ = plan_telops(bridge, [], opt)
    run_telops(bridge, jobs, opt)
    items = fake.timeline.tracks["video"][2]
    assert [(i.start, i.duration, i.comp.tool.inputs["StyledText"]) for i in items] == [
        (86400, 40, "こんにちは"), (86450, 30, "さようなら")]


def test_sfx_import_is_cached_in_sfx_bin(sfx_dir):
    fake = FakeResolve()
    bridge = ResolveBridge(fake)
    path = str(sfx_dir / "ぴこん.wav")
    bridge.insert_sfx(path, fake.timeline.start_frame, 1, True)
    bridge2 = ResolveBridge(fake)  # 新しいセッションでもビン内の既存クリップを再利用
    bridge2.insert_sfx(path, fake.timeline.start_frame + 100, 1, True)
    assert fake.media_pool.imported == [path]
    names = [f.GetName() for f in fake.media_pool.root.GetSubFolderList()]
    assert "SFX" in names
    assert fake.media_pool.current is fake.media_pool.root  # カレントフォルダは元に戻る


def test_drop_frame_playhead():
    fake = FakeResolve(fps=29.97, start_tc="01:00:00;00", drop=True)
    bridge = ResolveBridge(fake)
    fake.timeline.playhead = fake.timeline.start_frame + 1800
    assert bridge.playhead_frame() == fake.timeline.start_frame + 1800
    assert bridge.frame_tc(bridge.playhead_frame()) == "01:01:00;02"


def test_errors_when_no_timeline():
    fake = FakeResolve()
    fake.project.timeline = None
    with pytest.raises(ResolveError):
        ResolveBridge(fake)


def test_short_template_does_not_lock_in_end_exclusive():
    fake = FakeResolve(end_exclusive=False)
    tpl = fake.add_template(frames=120)
    bridge = ResolveBridge(fake)
    bridge.ensure_track("video", 2)
    start = bridge.timeline_start
    first = bridge._append(tpl, 121, start, 2, 1)  # テンプレより 1 フレーム長い要求 -> 切り詰め
    assert first.GetDuration() == 120
    assert bridge._end_exclusive is False
    second = bridge._append(tpl, 100, start + 200, 2, 1)
    assert second.GetDuration() == 100
    assert bridge._end_exclusive is False
