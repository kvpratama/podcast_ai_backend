# app/api/routes.py
from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from pydantic import HttpUrl
from typing import List
# Import the new summarizer function
from app.services.whisper_transcribe import transcribe_audio_from_url
from app.services.summarizer import summarize_transcript_google # <-- Import summarizer
# Import the SummaryResponse model
from app.models.schemas import TranscriptResponse, SummaryResponse # s<-- Make sure SummaryResponse is imported

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
        transcript = await transcribe_audio_from_url(str(audio_url))  # Add await
        print(f"Transcription successful for {audio_url}. Length: {len(transcript)}")

        if not transcript or not transcript.strip():
             raise HTTPException(status_code=400, detail="Transcription resulted in empty text. Cannot summarize.")

        # 2. Summarization
        print(f"Requesting summary for transcript from {audio_url}...")
        summary = await summarize_transcript_google(transcript) # Use await
        print(f"Summarization successful for {audio_url}.")

        # 3. Return Summary
        return {"summary": summary.content}

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
    except Exception as e:
        # Catch any other unexpected errors
        print(f"Unexpected error for URL {audio_url}: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
