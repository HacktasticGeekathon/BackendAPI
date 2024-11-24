import os
import re
import boto3
import requests
import uuid
import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from yt_dlp import YoutubeDL

from app.classes.fact_check import FactCheck
from app.classes.fallacy import Fallacy
from app.classes.transcript import TranscriptResponse
from app.clients.fallacy_detector import FallacyDetectionClient, Mode

app = FastAPI()

bucket_name = 'videos-20241122232253111200000001'
bucket_url = 'https://d2yom3r6s9mhn3.cloudfront.net/'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('app.test')

transcribe_client = boto3.client('transcribe')
s3_client = boto3.client('s3')
fallacy_detection_client = FallacyDetectionClient()

YT_VIDEO_ID_PATTERN = re.compile(
    r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')


class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    logger.info("WebSocket client connected")

    try:
        while True:
            youtube_url = await websocket.receive_text()
            youtube_thumbnail = get_youtube_thumbnail(youtube_url)
            filename = await download_video(youtube_url)
            s3 = await upload_to_s3(filename)
            await manager.broadcast({"video": bucket_url + s3.get("key"), "thumbnail": youtube_thumbnail})

            transcription = await transcribe_audio(s3.get("url"))
            transcript_response = TranscriptResponse.from_transcription_data(transcription)
            transcripts_list = transcript_response.transcripts_only()
            timestamps_list = [(seg.start_time, seg.end_time) for seg in transcript_response.audio_segments]

            await process_fallacies_and_facts(transcripts_list, timestamps_list)
            # facts = await process_facts(transcripts_list, timestamps_list)
            # await manager.broadcast({"fallacies": fallacies, "facts": facts})

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
        manager.disconnect(websocket)

async def process_fallacies_and_facts(transcripts_list, timestamps_list):
    await update_status("Processing fallacies and fact checking...")

    fallacy_detection_response = fallacy_detection_client.analyze(transcripts_list, Mode.FALLACY_DETECTION)
    fallacies_list = Fallacy.from_json(fallacy_detection_response.get("fallacies"), timestamps_list)
    facts_list = FactCheck.from_json(fallacy_detection_response.get("facts"), timestamps_list)

    fallacies_dict = [fallacy.to_dict() for fallacy in fallacies_list]
    facts_dict = [fact.to_dict() for fact in facts_list]

    await manager.broadcast({"fallacies": fallacies_dict, "facts": facts_dict})

async def process_facts(transcripts_list, timestamps_list):
    await update_status("Processing fallacies...")

    facts_response = fallacy_detection_client.analyze(transcripts_list, Mode.FACT_CHECKING)
    fallacies_list = FactCheck.from_json(facts_response, timestamps_list)

    return [fact.to_dict() for fact in fallacies_list]


async def download_video(youtube_url: str):
    await update_status("Downloading video...")

    ydl_opts = {
        "format": "best",
        "outtmpl": "%(title)s.%(ext)s"
    }

    logger.info(f"Starting to download video from {youtube_url}")
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)
        filename = ydl.prepare_filename(info)
        return filename


async def upload_to_s3(filename):
    await update_status("Uploading video...")
    s3_key = f"{uuid.uuid4()}.mp4"
    s3_client.upload_file(filename, bucket_name, s3_key)
    s3_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
    os.remove(filename)
    return {'url': s3_url, 'key': s3_key}


async def transcribe_audio(s3_url):
    await update_status("Transcribing audio...")

    job_name = f"transcribe-job-{uuid.uuid4()}"
    media_format = "mp4"

    transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={"MediaFileUri": s3_url},
        MediaFormat=media_format,
        IdentifyLanguage=True
    )

    while True:
        status = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
        job_status = status["TranscriptionJob"]["TranscriptionJobStatus"]
        if job_status in ["COMPLETED", "FAILED"]:
            break
        await asyncio.sleep(1)

    if job_status == "COMPLETED":
        transcript_url = status["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
        response = requests.get(transcript_url)
        response.raise_for_status()

        transcription_data = response.json()["results"]

        return transcription_data
    else:
        return None

async def update_status(status):
        await manager.broadcast({"status": status})

def get_youtube_id(url):
    match = YT_VIDEO_ID_PATTERN.match(url)
    return match.group(6) if match else None

def get_youtube_thumbnail(youtube_url):
    video_id = get_youtube_id(youtube_url)
    if not video_id:
        return None

    return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

@app.get("/health")
def read_health():
    return {"status": "healthy"}