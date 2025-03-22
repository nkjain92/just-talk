#!/usr/bin/env python3
# core/audio_manager.py
# This file handles audio recording functionality for the Just-Talk app.
# It provides a class that listens for keyboard events, records audio when the Option/Alt key is pressed,
# and saves the recorded audio to a WAV file when the key is released.

import sounddevice as sd
from pynput import keyboard
import numpy as np
import wave
import threading
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioManager:
    def __init__(self, on_audio_saved_callback=None):
        # Sample rate for audio recording (CD quality)
        self.fs = 44100
        # Flag to track recording state
        self.recording = False
        # List to store audio data chunks
        self.audio_data = []
        # Thread for recording process
        self.thread = None
        # Audio input stream
        self.stream = None
        # Callback function for when audio is saved
        self.on_audio_saved_callback = on_audio_saved_callback
        # Keyboard listener for hotkey detection
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()

        logger.info("AudioManager initialized")

    def on_press(self, key):
        # Start recording when Option/Alt key is pressed and not already recording
        if key == keyboard.Key.alt and not self.recording:
            logger.info("Recording started...")
            print("Recording started...")
            self.recording = True
            self.audio_data = []
            # Create a new input stream for each recording session
            self.stream = sd.InputStream(samplerate=self.fs, channels=1, dtype='int16')
            self.stream.start()
            # Start recording in a separate thread to keep UI responsive
            self.thread = threading.Thread(target=self.record)
            self.thread.start()

    def on_release(self, key):
        # Stop recording when Option/Alt key is released and currently recording
        if key == keyboard.Key.alt and self.recording:
            logger.info("Recording stopped...")
            print("Recording stopped...")
            self.recording = False
            if self.thread:
                self.thread.join()
            if self.stream:
                self.stream.stop()
                self.stream.close()
            self._save_audio()

            # Call the callback function if it exists
            if self.on_audio_saved_callback:
                logger.info("Calling on_audio_saved_callback")
                self.on_audio_saved_callback()

    def record(self):
        # Record audio in small chunks until key is released or timeout occurs
        start_time = time.time()
        while self.recording and (time.time() - start_time) < 30:  # 30-second timeout
            # Read in small chunks (100ms) for smoother recording
            data, overflowed = self.stream.read(int(self.fs * 0.1))
            if overflowed:
                logger.warning("Audio buffer overflowed")
                print("Warning: Audio buffer overflowed")
            self.audio_data.append(data)
        # If we're here because of timeout
        if self.recording:
            logger.info("Recording timed out after 30 seconds")
            print("Recording timed out after 30 seconds")
            self.recording = False

    def _save_audio(self):
        # Save recorded audio to a WAV file
        if not self.audio_data:
            logger.warning("No audio data to save")
            print("No audio data to save")
            return

        try:
            # Combine all audio chunks and flatten to 1D array
            audio = np.concatenate(self.audio_data, axis=0).flatten()
            # Save as WAV file
            with wave.open("temp_audio.wav", "wb") as wf:
                wf.setnchannels(1)  # Mono
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.fs)
                wf.writeframes(audio.tobytes())
            logger.info(f"Audio saved to temp_audio.wav ({len(audio)} samples)")
            print(f"Audio saved to temp_audio.wav ({len(audio)} samples)")
        except Exception as e:
            logger.error(f"Error saving audio: {e}")
            print(f"Error saving audio: {e}")