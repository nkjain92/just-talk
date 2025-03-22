#!/usr/bin/env python3
# core/transcription.py
# This file handles speech-to-text transcription for the Just-Talk app.
# It uses the DeepGram SDK to transcribe audio recordings.

import os
import logging
import json
from dotenv import load_dotenv
from deepgram import Deepgram

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

def transcribe_audio(audio_file):
    """
    Transcribe audio using DeepGram's SDK.

    Args:
        audio_file (str): Path to the audio file to transcribe

    Returns:
        str: The transcribed text
    """
    # Get API key from the environment (loaded from .env)
    api_key = os.getenv("DEEPGRAM_API_KEY")

    if not api_key:
        logger.error("No API key found")
        raise ValueError("DeepGram API key not found in environment or .env file")

    # Log API key details for debugging (safely)
    logger.info(f"API key loaded: {api_key[:4]}...{api_key[-4:]} (length: {len(api_key)})")

    try:
        # Create a Deepgram client using the API key
        deepgram = Deepgram(api_key)

        # Read the audio file
        logger.info(f"Reading audio file: {audio_file}")
        with open(audio_file, 'rb') as audio:
            # Configure source and options for standard transcription
            source = {'buffer': audio, 'mimetype': 'audio/wav'}
            options = {
                'punctuate': True,
                'smart_format': True
            }

            logger.info("Sending request to DeepGram API")
            # Use the sync_prerecorded method for synchronous processing
            response = deepgram.transcription.sync_prerecorded(source, options)

            # Parse the response to get the transcript
            transcript = response['results']['channels'][0]['alternatives'][0]['transcript']

            logger.info(f"Successfully transcribed audio: {transcript[:50]}...")
            return transcript

    except Exception as e:
        logger.error(f"Error in transcribe_audio: {str(e)}")
        raise