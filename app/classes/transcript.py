from typing import List


class AudioSegment:
    def __init__(self, id: int, start_time: str, end_time: str, transcript: str):
        self.id = id
        self.start_time = start_time
        self.end_time = end_time
        self.transcript = transcript

    def to_dict(self):
        return {
            "id": self.id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "transcript": self.transcript
        }

    def __repr__(self):
        return f"AudioSegment(id={self.id}, start_time={self.start_time}, end_time={self.end_time}, transcript={self.transcript})"


class TranscriptResponse:
    def __init__(self, audio_segments: List[AudioSegment]):
        self.audio_segments = audio_segments

    @classmethod
    def from_transcription_data(cls, transcription_data):
        audio_segments = []
        for i, segment in enumerate(transcription_data["audio_segments"]):
            id = segment.get("id")
            start_time = segment.get("start_time")
            end_time = segment.get("end_time")
            transcript = segment.get("transcript")
            audio_segment = AudioSegment(id=id, start_time=start_time, end_time=end_time, transcript=transcript)
            audio_segments.append(audio_segment)
        return cls(audio_segments=audio_segments)

    def to_dict(self):
        return {
            "audio_segments": [segment.to_dict() for segment in self.audio_segments]
        }

    def transcripts_only(self):
        return [segment.transcript for segment in self.audio_segments]

    def __repr__(self):
        return f"TranscriptResponse(audio_segments={self.audio_segments})"
