"""テスト用の最小 Resolve API モック (AppendToTimeline の解釈差もエミュレートできる)."""

import os

from telopsfx.timecode import frame_to_timecode, timecode_to_frame


class FakeTool:
    def __init__(self, tool_id="TextPlus"):
        self.id = tool_id
        self.inputs = {}

    def SetInput(self, name, value):
        self.inputs[name] = value


class FakeComp:
    def __init__(self):
        self.tool = FakeTool()
        self.locked = 0

    def FindToolByID(self, tool_id):
        return self.tool if tool_id == self.tool.id else None

    def Lock(self):
        self.locked += 1

    def Unlock(self):
        self.locked -= 1


class FakeClip:
    def __init__(self, name, frames=120, path="", ctype="Video"):
        self.name = name
        self.props = {"Frames": str(frames), "File Path": path, "Type": ctype}

    def GetName(self):
        return self.name

    def GetClipProperty(self, key=None):
        return self.props.get(key) if key else dict(self.props)


class FakeFolder:
    def __init__(self, name):
        self.name = name
        self.clips = []
        self.subs = []

    def GetName(self):
        return self.name

    def GetClipList(self):
        return list(self.clips)

    def GetSubFolderList(self):
        return list(self.subs)


class FakeItem:
    def __init__(self, clip, start, duration, track_type, track):
        self.clip = clip
        self.start = start
        self.duration = duration
        self.track_type = track_type
        self.track = track
        self.comp = FakeComp() if clip.props.get("Type") in ("Title", "Generator") else None
        self.color = None
        self.name = clip.name

    def GetStart(self):
        return self.start

    def GetEnd(self):
        return self.start + self.duration

    def GetDuration(self):
        return self.duration

    def GetName(self):
        return self.name

    def SetName(self, name):
        self.name = name
        return True

    def GetFusionCompByIndex(self, idx):
        return self.comp

    def SetClipColor(self, color):
        self.color = color
        return True


class FakeTimeline:
    def __init__(self, fps=24.0, start_tc="01:00:00:00", drop=False):
        self.fps = fps
        self.drop = drop
        self.start_frame = timecode_to_frame(start_tc, fps, drop)
        self.playhead = self.start_frame
        self.tracks = {"video": {1: []}, "audio": {1: []}, "subtitle": {}}
        self.markers = {}
        self.name = "Timeline 1"

    def GetName(self):
        return self.name

    def GetSetting(self, key):
        return {"timelineFrameRate": str(self.fps), "timelineDropFrameTimecode": "1" if self.drop else "0"}.get(key, "")

    def GetStartFrame(self):
        return self.start_frame

    def GetCurrentTimecode(self):
        return frame_to_timecode(self.playhead, self.fps, self.drop)

    def SetCurrentTimecode(self, tc):
        self.playhead = timecode_to_frame(tc, self.fps, self.drop)
        return True

    def GetTrackCount(self, track_type):
        return len(self.tracks[track_type])

    def AddTrack(self, track_type, sub=None):
        self.tracks[track_type][len(self.tracks[track_type]) + 1] = []
        return True

    def GetItemListInTrack(self, track_type, index):
        return list(self.tracks[track_type].get(index, []))

    def GetMarkers(self):
        return dict(self.markers)

    def DeleteClips(self, items, ripple=False):
        for it in items:
            self.tracks[it.track_type][it.track].remove(it)
        return True

    def InsertFusionTitleIntoTimeline(self, title):
        clip = FakeClip(title, 120, ctype="Title")
        item = FakeItem(clip, self.playhead, 120, "video", 1)
        self.tracks["video"][1].append(item)
        return item

    def add_item(self, track_type, index, clip, start, duration):
        self.tracks[track_type].setdefault(index, [])
        item = FakeItem(clip, start, duration, track_type, index)
        self.tracks[track_type][index].append(item)
        return item


class FakeMediaPool:
    def __init__(self, timeline, record_relative=False, end_exclusive=False):
        self.root = FakeFolder("Master")
        self.current = self.root
        self.timeline = timeline
        self.record_relative = record_relative
        self.end_exclusive = end_exclusive
        self.imported = []

    def GetRootFolder(self):
        return self.root

    def GetCurrentFolder(self):
        return self.current

    def SetCurrentFolder(self, folder):
        self.current = folder
        return True

    def AddSubFolder(self, parent, name):
        f = FakeFolder(name)
        parent.subs.append(f)
        return f

    def ImportMedia(self, paths):
        out = []
        for p in paths:
            clip = FakeClip(os.path.basename(p), 48, path=p, ctype="Audio")
            self.current.clips.append(clip)
            out.append(clip)
        self.imported.extend(paths)
        return out

    def AppendToTimeline(self, infos):
        out = []
        for info in infos:
            clip = info["mediaPoolItem"]
            length = info["endFrame"] - info["startFrame"] + (0 if self.end_exclusive else 1)
            length = min(length, int(clip.props["Frames"]))
            record = info["recordFrame"] + (self.timeline.start_frame if self.record_relative else 0)
            track_type = "audio" if info.get("mediaType") == 2 else "video"
            index = info["trackIndex"]
            if index > len(self.timeline.tracks[track_type]):
                return []
            out.append(self.timeline.add_item(track_type, index, clip, record, length))
        return out


class FakeProject:
    def __init__(self, timeline, media_pool):
        self.timeline = timeline
        self.media_pool = media_pool

    def GetMediaPool(self):
        return self.media_pool

    def GetCurrentTimeline(self):
        return self.timeline

    def GetSetting(self, key):
        return self.timeline.GetSetting(key)


class FakeResolve:
    def __init__(self, fps=24.0, start_tc="01:00:00:00", drop=False, record_relative=False, end_exclusive=False):
        self.timeline = FakeTimeline(fps, start_tc, drop)
        self.media_pool = FakeMediaPool(self.timeline, record_relative, end_exclusive)
        self.project = FakeProject(self.timeline, self.media_pool)

    def GetProjectManager(self):
        return self

    def GetCurrentProject(self):
        return self.project

    def add_template(self, name="Text+", frames=120):
        clip = FakeClip(name, frames, ctype="Title")
        folder = FakeFolder("Templates")
        folder.clips.append(clip)
        self.media_pool.root.subs.append(folder)
        return clip
