# app/services/summarizer.py
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
# from langchain.chains.llm import LLMChain
# from langchain.chains.combine_documents.stuff import StuffDocumentsChain
# from langchain.docstore.document import Document
# from langchain.chains.summarize import load_summarize_chain

# Load environment variables (like GOOGLE_API_KEY)
load_dotenv()

# Initialize the Google Generative AI model
# Make sure GOOGLE_API_KEY is set in your environment or .env file
try:
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-thinking-exp-01-21", temperature=0.7)
    print("ChatGoogleGenerativeAI model loaded successfully.")
except Exception as e:
    print(f"Error loading ChatGoogleGenerativeAI model: {e}")
    # Handle error appropriately - maybe raise or set llm to None
    llm = None

async def summarize_transcript_google(transcript: str) -> str:
    """
    Summarizes the provided transcript using Google Generative AI (Gemini Pro).
    """
    if llm is None:
        raise RuntimeError("Google Generative AI model failed to load.")
    if not transcript or not transcript.strip():
        return "Transcript was empty, nothing to summarize."

    try:
        print(f"Starting summarization for transcript of length: {len(transcript)}")

        # Option 1: Simple summarization using a basic prompt (good for shorter texts)
        # prompt_template = """Write a concise summary of the following podcast transcript:

        # "{text}"

        # CONCISE SUMMARY:"""
        # prompt = PromptTemplate.from_template(prompt_template)
        # llm_chain = LLMChain(llm=llm, prompt=prompt)
        # summary = await llm_chain.arun(text=transcript) # Use arun for async

        # Option 2: Using LangChain's summarization chain (more robust for longer texts)
        # It handles splitting text if needed (though 'stuff' doesn't split here)
        # Create a Document object for the chain
        # docs = [Document(page_content=transcript)]

        # Define prompt for the 'stuff' chain
        prompt_template = """Write a concise summary of the provided podcast transcript, excluding all promotions, advertisements, and external links. Focus on the main topic and the primary key takeaway, ensuring clarity and brevity:

        "{text}"

        CONCISE SUMMARY:"""
        prompt = PromptTemplate.from_template(prompt_template)
        summarization_chain = prompt | llm
        summary = await summarization_chain.ainvoke({"text": transcript,})
        # Load the summarization chain (using 'stuff' method for simplicity here)
        # Other methods like 'map_reduce' or 'refine' are better for very long texts
        # that exceed the model's context window.
        # chain = load_summarize_chain(llm, chain_type="stuff", prompt=prompt, verbose=False) # Set verbose=True for debugging

        # Run the chain asynchronously
        # summary_result = await chain.arun(docs) # Use arun for async with chains

        print("Summarization complete.")
        return summary

    except Exception as e:
        print(f"Error during summarization: {e}")
        # Re-raise a more specific error or return an error message
        raise RuntimeError(f"Summarization failed: {e}") from e

# Example Usage (optional, for testing)
# import asyncio
# if __name__ == "__main__":
#     async def main():
#         test_transcript = "This is a test transcript. It talks about various things. We need to summarize this content effectively. Podcasts often cover many topics, so a good summary is helpful. This is just placeholder text to test the summarization function."
#         try:
#             summary = await summarize_transcript_google(test_transcript)
#             print("\n--- Summary ---")
#             print(summary)
#             print("---------------\n")
#         except Exception as e:
#             print(f"An error occurred: {e}")
#     asyncio.run(main())

