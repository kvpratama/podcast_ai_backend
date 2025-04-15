# app/api/routes.py
from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from pydantic import HttpUrl
from typing import List
# Import the new summarizer function
from app.services.whisper_transcribe import transcribe_audio_file, transcribe_audio_from_url
from app.services.summarizer import summarize_transcript_google # <-- Import summarizer
# Import the SummaryResponse model
from app.models.schemas import TranscriptResponse, SummaryResponse # s<-- Make sure SummaryResponse is imported

router = APIRouter()

@router.post("/upload", response_model=TranscriptResponse)
async def upload_audio(file: UploadFile = File(...)):
    """
    Receives an audio file upload and transcribes it.
    """
    try:
        transcript = await transcribe_audio_file(file)  # Add await
        return {"transcript": transcript}
    except Exception as e:
        print(f"Error during file transcription: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to transcribe audio file: {e}")


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


# --- Keep other endpoints like /search ---

# Mock podcast data (Keep or remove as needed)
mock_episodes = [
     {
        "id": "1",
        "title": "Dilmun - The Ancient Paradise of Mesopotamia",
        "description": "Discussion about Dilmun - The Ancient Paradise of Mesopotamia.",
        "audio_url": "https://mcdn.podbean.com/mf/download/bwxretxdg8fjmxju/Dilmun_-_The_Ancient_Paradise_of_Mesopotamia78kbq.mp3"
    },
    {
        "id": "2",
        "title": "Boosting Brain Performance with Braintap",
        "description": "Nurse Doza explores how BrainTap harnesses sound, light, and vibration therapy to optimize brain function.",
        "audio_url": "https://mcdn.podbean.com/mf/download/wvpfi2dbv7u9rwtp/braintap2.mp3"
    },
    {
        "id": "3",
        "title": "Should Kids Learn to Code?",
        "description":  "Jonathan Schor joins us to discuss why coding may be the next essential skill for kids in our tech-driven world.",
        "audio_url": "https://mcdn.podbean.com/mf/download/q7ny3uyxt9fbv3b7/362_-_Should_Kids_Learn_to_Code_With_Jonathan_Schor.mp3"
    },
    {
        "id": "4",
        "title": "Careless People by Sarah Wynn-Williams",
        "description":  "Careless People is a riveting exposé that uncovers how ambition and entitlement at the highest levels of power can erode truth, ethics, and democracy itself. ",
        "audio_url": "https://mcdn.podbean.com/mf/download/9q5262e2hdx5ia9x/PUBLIC_Careless_People_mixdown_0170zq4.mp3"
    },
]


@router.get("/search")
def search_podcasts(q: str = Query(..., description="Search query")) -> List[dict]:
    # Very basic "search" that just checks if query is in the title
    return [ep for ep in mock_episodes if q.lower() in ep["title"].lower()]

# You might want to keep the original /transcribe-url endpoint if needed,
# or rename this one if it completely replaces the old functionality.
# I've renamed it to /transcribe-and-summarize-url for clarity.

