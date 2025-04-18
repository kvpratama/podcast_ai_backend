# app/services/whisper_transcribe.py
# import whisper
import tempfile
import aiohttp  # Replace requests with aiohttp for async operations
import os
import asyncio  # For async file operations
import functools
import pydub  # Add this import
# from openai import OpenAI
# import requests
# import base64
# from dotenv import load_dotenv

# Load the model once when the module is imported
# Consider making the model choice configurable (e.g., "tiny", "base", "small", "medium", "large")
# Using "base" is a good balance for speed and accuracy on CPU.
# try:
#     model = whisper.load_model("tiny")
#     print("Whisper model 'tiny' loaded successfully.")
# except Exception as e:
#     print(f"Error loading Whisper model: {e}")
#     # Handle the error appropriately - maybe raise it or set model to None
#     model = None

# async def transcribe_audio_file(file):
#     """
#     Asynchronously transcribes an audio file object (like FastAPI's UploadFile).
#     """
#     if model is None:
#         raise RuntimeError("Whisper model failed to load.")

#     tmp_path = None
#     try:
#         # Use a temporary file for the audio
#         with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
#             content = await file.read()  # Use await for async file read
#             tmp.write(content)
#             tmp_path = tmp.name

#         print(f"Transcribing temporary file: {tmp_path}")
#         loop = asyncio.get_event_loop()
#         result = await loop.run_in_executor(
#             None,
#             functools.partial(model.transcribe, tmp_path, fp16=False)
#         )
#         print("Transcription complete.")
#         return result['text']
#     except Exception as e:
#         print(f"Error during transcription: {e}")
#         raise e
#     finally:
#         if tmp_path and os.path.exists(tmp_path):
#             try:
#                 os.remove(tmp_path)
#                 print(f"Temporary file {tmp_path} deleted.")
#             except OSError as e:
#                 print(f"Error deleting temporary file {tmp_path}: {e}")

# def invoke_chute(audio_b64):
# 	api_token = os.environ['CHUTES_API_TOKEN']

# 	headers = {
# 		"Authorization": "Bearer " + api_token,
#         "Content-Type": "application/json"
# 	}
	
# 	body =     {
#       "language": None,
#       "audio_b64": audio_b64,
#     }

# 	response = requests.post(
# 		"https://chutes-whisper-large-v3.chutes.ai/transcribe",
# 		headers=headers,
# 		json=body
# 	)

# 	# Print status code and response
# 	print(f"Status code: {response.status_code}")
# 	print(response.json())



async def transcribe_audio_from_url(audio_url: str):
    """
    Asynchronously downloads an audio file from a URL and transcribes it.
    If the audio is longer than 10 minutes, only the first 10 minutes are transcribed.
    """

    model = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

    # if model is None:
    #     raise RuntimeError("Whisper model failed to load.")

    tmp_path = None
    trimmed_path = None
    try:
        print(f"Attempting to download audio from: {audio_url}")
        async with aiohttp.ClientSession() as session:
            async with session.get(audio_url) as response:
                response.raise_for_status()
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                    async for chunk in response.content.iter_chunked(8192):
                        tmp.write(chunk)
                    tmp_path = tmp.name

        print(f"Audio downloaded successfully to temporary file: {tmp_path}")

        # Load and trim audio if longer than 5 minutes
        audio = pydub.AudioSegment.from_file(tmp_path)
        five_minutes_ms = 5 * 60 * 1000
        if len(audio) > five_minutes_ms:
            print("Audio is longer than 5 minutes. Trimming to first 5 minutes.")
            audio = audio[:five_minutes_ms]
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as trimmed_tmp:
                audio.export(trimmed_tmp.name, format="mp3")
                trimmed_path = trimmed_tmp.name
            transcribe_path = trimmed_path
        else:
            transcribe_path = tmp_path

        loop = asyncio.get_event_loop()
        # Open the file in binary mode for OpenAI API
        with open(transcribe_path, "rb") as audio_file:

            # Read the file content and convert to base64
            # file_content = audio_file.read()
            # audio_base64 = base64.b64encode(file_content).decode('utf-8')

            result = await loop.run_in_executor(
                None,
                functools.partial(
                    model.audio.transcriptions.create,
                    model="whisper-1",
                    file=audio_file,
                    # invoke_chute,
                    # audio_b64=audio_base64,
                )
            )
        print("Transcription complete.")
        print(result)
        print(result.json())
        return result.json()
    except aiohttp.ClientError as e:
        print(f"Error downloading audio from URL {audio_url}: {e}")
        raise ConnectionError(f"Failed to download audio from URL: {e}") from e
    except Exception as e:
        print(f"Error during transcription process: {e}")
        raise RuntimeError(f"Transcription failed: {e}") from e
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

# Example Usage (you wouldn't typically run this directly in the service file)
# if __name__ == "__main__":
#     # Replace with a real MP3 URL for testing
#     test_url = "https://traffic.libsyn.com/secure/lexfridman/Lex_Fridman_Podcast_393.mp3?dest-id=1942778" # Example URL
#     try:
#         print(f"Starting transcription for URL: {test_url}")
#         transcript = transcribe_audio_from_url(test_url)
#         print("\n--- Transcription ---")
#         print(transcript)
#         print("---------------------\n")
#     except Exception as e:
#         print(f"An error occurred: {e}")

