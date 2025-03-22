# Final Dictation App PRD (macOS-First Implementation)

## Product Summary

Dictation App is a lightweight macOS utility that enables quick, accurate speech-to-text transcription directly into any text field through a simple keyboard shortcut, with intelligent text cleaning via LLM processing.

## Target Users

- Knowledge workers who regularly write documents, emails, and messages
- Users with repetitive strain injuries who prefer speech to typing
- Students taking notes during lectures
- Professionals drafting correspondence on the go

## Features and Implementation Plan

### Phase 1: macOS MVP (Weekend Project)

#### 1. Platform Support

- **macOS-only** initial implementation with native macOS integrations
- Distributed as .dmg installer for macOS
- **Auto-updates**: App will periodically check for updates in the background and notify users when updates are available

#### 2. Visual Indicator

- A small, always-on-top floating window:
  - **Idle State**: 4 px height, 24 px width, rounded edges, dark gray background, positioned in the top-right corner
  - **Recording State**: Expands to 8 px height, 36 px width, showing a moving sound wave pattern
  - **Processing State**: Same size as recording state, sound wave stops moving, with a processing icon
  - **Error State**: Same size as idle state but with red color and distinct pattern, showing error icon
- Implemented using PyQt/PySide with transparent, frameless window styling
- Tooltips on hover showing current status/error details

#### 3. Dictation Functionality

- **Hold-to-Talk**: Press and hold Fn key (configurable) to start recording
- **Release to Transcribe**: Release the key to trigger transcription and text insertion
- **Timeout**: Automatically stop recording after 30 seconds
- **Language Selection**: Support for auto-detection with option to manually select preferred language

#### 4. Transcription

- Audio transcribed using DeepGram API for superior accuracy
- Fast, reliable speech-to-text with punctuation support
- Multiple language support with configurable language selection

#### 5. Text Cleaning

- Transcribed text processed by GPT-4o mini to remove filler words and repetitions
- Simple fallback for API failures: insert raw transcription with notification

#### 6. Text Insertion

- Direct text insertion at cursor using macOS accessibility APIs
- Multi-tiered insertion strategy:
  - **Primary**: AXUIElement API via PyObjC for most reliable insertion
  - **Secondary**: Apple Events for keystroke simulation
  - **Fallback**: Clipboard with notification (only if other methods fail)
- Permissions assistant to guide users through required accessibility permissions
- "Test Insertion" feature in settings to verify functionality

#### 7. Dashboard and Statistics

- Accessible from menu bar showing:
  - Usage statistics (words dictated, average speed)
  - Current streak and consistency metrics
  - Quick access to language selection and settings
- First-run experience with guided setup steps
- Visual feedback on progress and achievements

#### 8. Error Handling

- Comprehensive error detection and user feedback for:
  - Audio recording issues (device access, format problems)
  - Network connectivity (timeout, DNS failures)
  - API errors (authentication, rate limits, service outages)
  - Text insertion failures (permission issues, app compatibility)
- Clear visual indicators and guidance for resolving issues
- Auto-retry for transient failures
- Detailed logging for troubleshooting

#### 9. Transcription History and Data Storage

- **Word Count Tracking**:
  - Persistent counter stored in SQLite database
  - Statistics for daily, weekly, and all-time usage
  - Visible in dashboard and system tray menu
- **Transcription History**:
  - Store all transcriptions with metadata (timestamp, length, language)
  - Search and filter capabilities in history view
  - Quick access to recent transcriptions
  - Option to clear history or set retention period
- **Data Storage**:
  - Local SQLite database for efficiency and reliability
  - Regular database cleanup to manage storage footprint
  - Optional data export for backup

#### 10. System Tray Menu

- Comprehensive menu including:
  - **Open Dashboard**: Access the main statistics and settings dashboard
  - **Paste Last Transcript**: Quick access to reuse the most recent transcription
  - **Words Dictated**: Counter showing total words dictated
  - **Select Microphone**: Choose input device from available options
  - **Select Language**: Choose transcription language or auto-detect
  - **Add Word to Dictionary**: Quick access to add custom terminology
  - **Check for Updates**: Manual update check with current version displayed
  - **Settings**: Access to full app settings
  - **Share Feedback**: Link to provide feedback
  - **About**: App information
  - **Quit**: Exit the application
- Visual indicator in system tray icon showing current app state

#### 11. Auto-Update System

- Periodic check for new versions against a GitHub releases endpoint
- User notification when updates are available
- Option to download and install updates automatically
- Verification of update package integrity before installation

### Phase 2: Expansion (Post-Weekend)

#### 1. Windows Support

- Extend functionality to Windows using the same architecture
- Windows-native text insertion via UI Automation or SendInput

#### 2. Advanced Features

- Custom dictionary for specialized terminology
- Command mode for text editing commands
- Enhanced multi-language support
- Mobile companion app

## Technical Implementation

### Architecture Design

```python
dictation_app/
├── core/                  # Platform-agnostic code
│   ├── audio_manager.py   # Audio recording abstraction
│   ├── transcription.py   # DeepGram API interface
│   ├── text_processing.py # LLM-based cleaning
│   └── error_handling.py  # Error detection and handling
├── data/
│   ├── database.py        # SQLite database manager
│   ├── history.py         # Transcription history management
│   └── statistics.py      # User statistics tracking
├── platforms/
│   ├── macos/             # macOS implementation
│   └── windows/           # Future Windows implementation
├── ui/                    # Shared UI components
│   ├── indicator.py       # Visual indicator
│   ├── dashboard.py       # Statistics dashboard
│   ├── history_view.py    # Transcription history viewer
│   └── system_tray.py     # System tray menu
└── services/
    ├── updater.py         # Auto-update functionality
    └── analytics.py       # Optional usage statistics
```

### Technology Stack (Phase 1)

#### Core Framework

- **Python 3.9+**: Primary development language
- **PyQt6/PySide6**: For floating indicator and UI
- **PyObjC**: For macOS-native functionality
- **SQLite**: For local data storage

#### Key Python Libraries

- **pynput**: Global hotkey registration
- **sounddevice/pyaudio**: Audio recording
- **requests/httpx**: API communication with DeepGram and OpenAI
- **pyinstaller**: Application packaging
- **AppKit/Cocoa**: Through PyObjC for text insertion at cursor
- **py-github-update**: For auto-update functionality (GitHub based)
- **sqlite3**: Database for statistics and history

#### Packaging

- **PyInstaller**: Create .app bundle
- **create-dmg**: Generate .dmg installer
- **Code signing**: Using Apple Developer certificate (if available)

### Key Technical Components

#### Data Storage Implementation

```python
# Database schema for transcription history and statistics
def initialize_database():
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # Create transcriptions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transcriptions (
        id INTEGER PRIMARY KEY,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        raw_text TEXT,
        cleaned_text TEXT,
        word_count INTEGER,
        language TEXT,
        app_name TEXT
    )
    ''')

    # Create statistics table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS statistics (
        date DATE PRIMARY KEY,
        word_count INTEGER DEFAULT 0,
        transcription_count INTEGER DEFAULT 0,
        avg_words_per_minute REAL DEFAULT 0
    )
    ''')

    conn.commit()
    conn.close()
```

#### Audio Pipeline

- Record audio using sounddevice/pyaudio
- Transmit to DeepGram for transcription
- Process received text through OpenAI API (GPT-4o mini)

#### Text Insertion Implementation

```python
# Multi-tiered text insertion strategy
def insert_text_at_cursor(text):
    # Primary: AXUIElement API for reliable insertion
    if insert_via_accessibility_api(text):
        return True

    # Secondary: Apple Events for keystroke simulation
    if insert_via_apple_events(text):
        return True

    # Fallback: Clipboard with notification
    return insert_via_clipboard_with_notification(text)
```

#### Permissions Management

```python
# Guide users through required permissions
def setup_accessibility_permissions():
    # Check if accessibility permissions are granted
    if not has_accessibility_permissions():
        # Show permission request dialog with visual guide
        show_permission_guide()
        # Open System Preferences to Security & Privacy
        open_system_preferences_accessibility()
```

#### Auto-Update Implementation

```python
# Using GitHub as the update server
def check_for_updates():
    # Check in background thread
    current_version = app_version()
    latest_version = fetch_latest_version_from_github()

    if latest_version > current_version:
        # Show update notification
        show_update_notification(latest_version)
        # Download update if auto-updates enabled
        if settings.auto_update_enabled:
            download_update_in_background()
```

#### User Interface

- Floating indicator implemented with transparent Qt window
- System menu bar item for accessing dashboard and settings
- Permissions assistant for guiding through setup
- Update notification via standard macOS notification system
- System tray menu providing quick access to all key functions
- History view with search and filter capabilities

### Error Handling Strategy

- All operations wrapped in try/except blocks with specific error types
- User-friendly error messages with actionable guidance
- Automatic diagnostics for common issues (e.g., microphone access, network connectivity)
- Tiered fallback mechanisms for critical functions
- Detailed logging for troubleshooting

## Performance Requirements

- Recording start delay: <100ms from key press
- Transcription processing time: <3 seconds for 30-second audio clip
- Memory usage: <150MB RAM
- Update check: Non-blocking, performed in background thread
- CPU usage: <5% during idle, <15% during processing
- Database performance: <50ms for common queries

## Deployment

- Initial release as .dmg download
- GitHub repository for distribution and update hosting
- Basic error reporting via logs
- Versioning using semantic versioning (MAJOR.MINOR.PATCH)

## First Run Experience

- Welcome screen with app overview
- Guided setup for necessary permissions
- Quick tutorial on using the dictation feature
- Language selection guidance
- Test transcription and insertion functionality

## Data Privacy and Security

- All data stored locally on user's device
- No cloud storage of transcriptions
- Clear data retention policy with user controls
- Option to disable statistics collection
- Secure storage of API keys using keychain

This comprehensive PRD addresses all the technical concerns while maintaining the focus on delivering a high-quality macOS experience in Phase 1, with a clear path to Windows support in Phase 2. The addition of robust data storage and history management ensures users can track their usage and access past transcriptions easily.
