from fastapi import FastAPI, HTTPException
import yt_dlp as youtube_dl
import boto3
import time
import os
import aiohttp
import asyncio

app = FastAPI()

bucket_name = 'videos-20241122232253111200000001'


def download_youtube_video(youtube_url, download_path):
    ydl_opts = {
        'format': 'best[ext=mp4]',
        'outtmpl': f'{download_path}/%(title)s.%(ext)s',
        'noplaylist': True,
    }
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            result = ydl.download([youtube_url])
            if result != 0:
                raise HTTPException(status_code=500, detail="Download failed")
        # Return the path to the downloaded video
        return next(f for f in os.listdir(download_path) if f.endswith('.mp4'))
    except youtube_dl.utils.DownloadError as e:
        print(f"Download error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred with yt-dlp")
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


def upload_to_s3(file_path, s3_key):
    s3_client = boto3.client('s3')
    s3_client.upload_file(file_path, bucket_name, s3_key)
    return f"s3://{bucket_name}/{s3_key}"


def start_transcription_job(job_name, media_uri):
    transcribe_client = boto3.client('transcribe')
    transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': media_uri},
        MediaFormat='mp4',
        IdentifyLanguage=True,
        OutputBucketName=bucket_name
    )


def get_transcription_result(job_name):
    transcribe_client = boto3.client('transcribe')

    while True:
        result = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
        status = result['TranscriptionJob']['TranscriptionJobStatus']

        if status == 'COMPLETED':
            break
        elif status == 'FAILED':
            raise HTTPException(status_code=500, detail="Transcription job failed")

@app.post("/transcribe/")
async def transcribe_youtube_video(youtube_url: str):
    try:
        job_name = f"transcription-{int(time.time())}"

        # Download YouTube video
        download_path = 'tmp'
        video_file = download_youtube_video(youtube_url, download_path)
        video_path = os.path.join(download_path, video_file)

        # Upload video to S3
        s3_key = f"uploaded_videos/{os.path.basename(video_path)}"
        media_uri = upload_to_s3(video_path, s3_key)

        # Start transcription job
        start_transcription_job(job_name, media_uri,)

        # Get transcription result
        get_transcription_result(job_name)

        # Clean up downloaded video
        os.remove(video_path)

        return "success motherfoka"

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
