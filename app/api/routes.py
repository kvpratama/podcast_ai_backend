# app/api/routes.py
from fastapi import APIRouter, Query, HTTPException
from pydantic import HttpUrl
from app.models.schemas import SummaryResponse
from google import genai
import aiohttp
import pydub
import tempfile
import os

router = APIRouter()

# @router.post("/upload", response_model=TranscriptResponse)
# async def upload_audio(file: UploadFile = File(...)):
#     """
#     Receives an audio file upload and transcribes it.
#     """
#     try:
#         transcript = await transcribe_audio_file(file)  # Add await
#         return {"transcript": transcript}
#     except Exception as e:
#         print(f"Error during file transcription: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to transcribe audio file: {e}")


# --- Modified Endpoint for Transcribing and Summarizing from URL ---
# Note: Changed response_model to SummaryResponse
@router.get("/transcribe-and-summarize-url", response_model=SummaryResponse)
async def transcribe_and_summarize_from_url(audio_url: HttpUrl = Query(..., description="URL of the audio file to transcribe and summarize")):
    """
    Downloads audio from URL, transcribes it, and returns a summary.
    """
    transcript = "" # Initialize transcript
    try:
        print(f"Received request to transcribe/summarize URL: {audio_url}")

        # 1. Transcription
        # transcript = await transcribe_audio_from_url(str(audio_url))  # Add await
        # print(f"Transcription successful for {audio_url}. Length: {len(transcript)}")

        # if not transcript or not transcript.strip():
        #      raise HTTPException(status_code=400, detail="Transcription resulted in empty text. Cannot summarize.")

        # 2. Summarization
        # print(f"Requesting summary for transcript from {audio_url}...")
        # summary = await summarize_transcript_google(transcript) # Use await
        # print(f"Summarization successful for {audio_url}.")

        ####### Google Generative AI (Gemini Pro) for Summarization ###
        client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

        tmp_path = None
        trimmed_path = None
        print(f"Attempting to download audio from: {audio_url}")

        # Download only the first 10 minutes (approximate, assumes 128kbps MP3)
        target_minutes = 10
        bitrate_kbps = 128  # Adjust if you know the actual bitrate
        bytes_per_second = (bitrate_kbps * 1000) // 8
        max_bytes = bytes_per_second * 60 * target_minutes

        async with aiohttp.ClientSession() as session:
            async with session.get(str(audio_url)) as response:
                response.raise_for_status()
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                    downloaded = 0
                    async for chunk in response.content.iter_chunked(8192):
                        if downloaded + len(chunk) > max_bytes:
                            chunk = chunk[:max_bytes - downloaded]
                        tmp.write(chunk)
                        downloaded += len(chunk)
                        if downloaded >= max_bytes:
                            print(downloaded)
                            break
                    tmp_path = tmp.name

        print(f"Audio downloaded successfully to temporary file: {tmp_path}")

        # Load and trim audio if longer than 5 minutes
        audio = pydub.AudioSegment.from_file(tmp_path)
        ten_minutes_ms = 10 * 60 * 1000
        if len(audio) > ten_minutes_ms:
            print("Audio is longer than 10 minutes. Trimming to first 10 minutes.")
            audio = audio[:ten_minutes_ms]
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as trimmed_tmp:
                audio.export(trimmed_tmp.name, format="mp3")
                trimmed_path = trimmed_tmp.name
            transcribe_path = trimmed_path
        else:
            transcribe_path = tmp_path

        myfile = client.files.upload(file=transcribe_path)

        response = client.models.generate_content(
            model="gemini-2.0-flash-lite", contents=["Summarize the core argument and central conclusion of the provided podcast episode, excluding all promotional content, advertisements, sponsor mentions, and external references (websites, social media, etc.). Focus on extracting the substantive discussion, distilling its essence into a concise, easily understandable summary that highlights the primary subject matter and its ultimate conclusion, even if the provided episode represents a truncated or edited version of the original broadcast. Prioritize clarity and conciseness, ensuring the summary accurately reflects the central thesis and final takeaway.", myfile]
        )
        

        print(response.text)

        # 3. Return Summary
        return {"summary": response.text}

    except ConnectionError as e:
        print(f"Connection error for URL {audio_url}: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to download audio from URL: {e}")
    except RuntimeError as e:
        # Catch errors from both transcription and summarization services
        print(f"Runtime error during processing for URL {audio_url}: {e}")
        # Distinguish between model loading and processing errors if needed
        if "model failed to load" in str(e):
             raise HTTPException(status_code=503, detail=f"Service unavailable: {e}") # Service unavailable
        else:
             raise HTTPException(status_code=500, detail=f"Processing failed: {e}")
    except HTTPException as e:
         # Re-raise HTTPExceptions (like the one for empty transcript)
         raise e
    except aiohttp.ClientError as e:
        print(f"Error downloading audio from URL {audio_url}: {e}")
        raise ConnectionError(f"Failed to download audio from URL: {e}") from e
    except Exception as e:
        # Catch any other unexpected errors
        print(f"Unexpected error for URL {audio_url}: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
    finally:
        # Clean up temporary files
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
                print(f"Temporary file {tmp_path} deleted.")
            except OSError as e:
                print(f"Error deleting temporary file {tmp_path}: {e}")
        if trimmed_path and os.path.exists(trimmed_path):
            try:
                os.remove(trimmed_path)
                print(f"Temporary file {trimmed_path} deleted.")
            except OSError as e:
                print(f"Error deleting temporary file {trimmed_path}: {e}")
