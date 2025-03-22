#!/usr/bin/env python3
# main.py
# This is the entry point for the Just-Talk app.
# It initializes the application window and creates an AudioManager instance to handle recording.

import sys
import logging
import os
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QObject, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont
from core.audio_manager import AudioManager
from core.transcription import transcribe_audio
import threading

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TranscriptionSignals(QObject):
    """Signals for thread-safe communication between threads"""
    started = pyqtSignal()
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

class TestApp(QObject):
    def __init__(self):
        super().__init__()

        # Create the Qt application
        self.app = QApplication(sys.argv)

        # Create the main window
        self.window = QWidget()
        self.window.setWindowTitle("Just-Talk Setup Test")
        self.window.resize(500, 300)

        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Create instruction label
        self.status_label = QLabel("Press Option/Alt key to record, release to transcribe")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("Arial", 14))
        self.status_label.setStyleSheet("color: #333; margin-bottom: 20px;")
        main_layout.addWidget(self.status_label)

        # Create transcription result label
        self.result_label = QLabel("Transcription will appear here")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.result_label.setWordWrap(True)
        self.result_label.setFont(QFont("Arial", 14))
        self.result_label.setStyleSheet("""
            background-color: #f5f5f5;
            padding: 15px;
            border-radius: 8px;
            min-height: 150px;
            border: 1px solid #ccc;
        """)
        self.result_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        main_layout.addWidget(self.result_label)

        # Set layout
        self.window.setLayout(main_layout)
        self.window.show()

        # Set up signals for thread-safe UI updates
        self.signals = TranscriptionSignals()
        self.signals.started.connect(self.on_transcription_started)
        self.signals.finished.connect(self.on_transcription_finished)
        self.signals.error.connect(self.on_transcription_error)

        # Initialize audio manager with callback
        self.audio_manager = AudioManager(on_audio_saved_callback=self.on_audio_saved)

        logger.info("Application started")

    def on_audio_saved(self):
        """Callback from AudioManager - runs in AudioManager's thread"""
        # Check if audio file exists
        if not os.path.exists("temp_audio.wav"):
            self.signals.error.emit("Audio file not found")
            return

        # Signal that transcription is starting
        self.signals.started.emit()

        # Start transcription in a separate thread
        threading.Thread(target=self._transcribe_audio_thread).start()

    def _transcribe_audio_thread(self):
        """Transcription worker thread function"""
        try:
            # Log that we're starting transcription
            logger.info("Starting transcription in worker thread")

            # Attempt to transcribe the audio
            text = transcribe_audio("temp_audio.wav")

            # Signal completion with the result
            self.signals.finished.emit(text)

        except Exception as e:
            # Signal error
            error_message = str(e)
            logger.error(f"Transcription error: {error_message}")
            self.signals.error.emit(error_message)

    @pyqtSlot()
    def on_transcription_started(self):
        """Slot for transcription started signal - runs in main thread"""
        self.status_label.setText("Transcribing audio...")
        self.status_label.setStyleSheet("color: blue;")

    @pyqtSlot(str)
    def on_transcription_finished(self, text):
        """Slot for transcription finished signal - runs in main thread"""
        self.result_label.setText(f"Transcription Result:\n\n{text}")
        self.status_label.setText("Transcription complete ✓")
        self.status_label.setStyleSheet("color: green;")
        logger.info(f"Transcription displayed: {text[:50]}...")

    @pyqtSlot(str)
    def on_transcription_error(self, error_message):
        """Slot for transcription error signal - runs in main thread"""
        self.result_label.setText(f"ERROR: {error_message}")
        self.status_label.setText("Transcription failed ✗")
        self.status_label.setStyleSheet("color: red;")

    def run(self):
        # Start the application event loop
        sys.exit(self.app.exec())

if __name__ == "__main__":
    app = TestApp()
    app.run()
