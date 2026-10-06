# 🎓 HICET Information AI Assistant (Production Web & Android APK)

A production-ready, ultra-fast AI-powered College Information Assistant built with **Python**, **Streamlit**, and **Groq LLMs** (OpenAI GPT-OSS 120B/20B, Llama 3.3 70B, etc.), strictly grounded in the official HICET knowledge base document.

Includes responsive mobile web design and a native **Android Release APK** with runtime microphone support.

---

## 🌟 Key Features

- ⚡ **Ultra-Fast Groq LLM Inference**: Token-streaming responses with low latency.
- 📄 **Knowledge Base Grounding**: Strict anti-hallucination guardrails grounded in `college_knowledge_base.txt`.
- 🌐 **Cross-Platform Access**: Usable on desktop browsers, mobile browsers (iOS/Android), and via a dedicated Android APK.
- 📱 **Native Android Release APK**:
  - Fullscreen WebView wrapper (`com.hicet.informationaiassistant`).
  - Signed production release APK (`HICET-Information-AI-Assistant-release.apk`).
  - Built-in microphone audio permission handling (`RECORD_AUDIO`) for voice input.
  - Native pull-to-refresh (`SwipeRefreshLayout`) and graceful offline error handling with retry.
- 🔐 **Secure Production Configuration**:
  - Works seamlessly with both local `.env` and production cloud secrets (`st.secrets["GROQ_API_KEY"]`).
  - Strict `.gitignore` protecting secrets, keystores, and credentials.
- 🎬 **In-Chat Video & Image Playback**: Campus tours, department overviews, and student queries in English, Tamil, and Tanglish.
- 🎤 **Voice & Speech-to-Text Input**: Integrated voice search across supported browsers and Android app.
- 👥 **User Authentication**: Secure SQLite login and registration with bcrypt password hashing.

---

## 📁 Project Architecture & Structure

```
chatbot-01/
├── app.py                                        # Streamlit Web Application (Desktop & Mobile)
├── chatbot.py                                    # Core Groq LLM chatbot engine
├── auth.py                                       # SQLite + bcrypt user authentication
├── cli_chat.py                                   # Terminal CLI chat interface
├── video_utils.py                                # Dynamic video topic matching & playback
├── video_library.py                              # Video library interface
├── college_knowledge_base.txt                    # Comprehensive HICET knowledge base
├── media/                                        # College imagery and branding assets
├── videos/                                       # Local college video media
├── requirements.txt                              # Production Python dependencies
├── .env.example                                  # Safe environment variable template
├── .gitignore                                    # Production exclusion rules
├── Dockerfile                                    # Cloud container deployment configuration
├── .dockerignore                                 # Container build exclusions
├── .streamlit/
│   └── config.toml                               # Production Streamlit server & theme config
├── android/                                      # Android native project
│   ├── app/
│   │   ├── build.gradle                          # App build & release signing configuration
│   │   ├── release-keystore.jks                  # Release signing keystore
│   │   └── src/main/
│   │       ├── AndroidManifest.xml               # App permissions & activity declaration
│   │       ├── java/.../MainActivity.java       # WebView, mic permissions, back button handling
│   │       └── res/                              # Adaptive icons, layouts, colors, strings
│   ├── build.gradle                              # Root Gradle build script
│   ├── settings.gradle                           # Android project settings
│   └── gradle.properties                         # JVM & AndroidX optimization flags
└── HICET-Information-AI-Assistant-release.apk    # Signed Production Android Release APK
```

---

## 🚀 Local Development Setup

### 1. Prerequisites
- Python 3.9+ installed
- Free Groq API Key from [Groq Console](https://console.groq.com/keys)

### 2. Installation
```bash
# Clone or navigate to the project directory
cd chatbot-01

# Install required dependencies
pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env` and configure your Groq API key:
```bash
copy .env.example .env
```
Inside `.env`:
```env
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
```

### 4. Run Locally
```bash
streamlit run app.py
```
Open `http://localhost:8501` in your browser.

---

## ☁️ Production Web Deployment (HTTPS)

### Option A: Streamlit Community Cloud (Recommended)
1. Push the code to your GitHub repository (e.g. `https://github.com/rahulgk681-zen/HICET-AI-chatbot`).
2. Go to [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
3. Click **"New app"**:
   - **Repository**: `rahulgk681-zen/HICET-AI-chatbot`
   - **Branch**: `main`
   - **Main file path**: `app.py`
4. In **Advanced settings** -> **Secrets**, paste:
   ```toml
   GROQ_API_KEY = "your_actual_groq_api_key_here"
   ```
5. Click **"Deploy"**. Your application will be live at a public HTTPS URL (e.g., `https://hicet-ai-assistant.streamlit.app`).

### Option B: Docker / Cloud Container (Render, Hugging Face Spaces, Railway)
1. Build the Docker container:
   ```bash
   docker build -t hicet-ai-assistant .
   ```
2. Run with environment variable:
   ```bash
   docker run -p 8501:8501 -e GROQ_API_KEY="your_api_key" hicet-ai-assistant
   ```

---

## 📱 Android Release APK

### Output Location
The signed Release APK is available at:
`c:\Users\acer\OneDrive\Documents\chatbot-01\HICET-Information-AI-Assistant-release.apk`
(Also under `android/app/build/outputs/apk/release/app-release.apk`).

### App Specifications
- **App Name**: HICET Information AI Assistant
- **Package ID**: `com.hicet.informationaiassistant`
- **Build Type**: Release (Signed with v2 signature scheme)
- **Target SDK**: Android 14 (API 34)
- **Minimum SDK**: Android 7.0 (API 24)
- **Requested Permissions**:
  - `android.permission.INTERNET`: Connect to production HTTPS application
  - `android.permission.ACCESS_NETWORK_STATE`: Detect connection status
  - `android.permission.RECORD_AUDIO`: Speech-to-text / microphone input
  - `android.permission.MODIFY_AUDIO_SETTINGS`: Optimize audio recording

### How to Install on Android Devices
1. Transfer `HICET-Information-AI-Assistant-release.apk` to your Android device (via USB, Google Drive, WhatsApp, or Bluetooth).
2. Tap the downloaded APK on your Android device to install.
3. If prompted with *"Install unknown apps"*, enable permission for your browser or file manager.
4. Launch **HICET Information AI Assistant** from your home screen or app drawer.
5. Grant microphone permission when prompted if you wish to use voice search.

---

## 🔒 Security Best Practices
- Never commit `.env` or files containing secret API keys to public repositories.
- The Android APK connects exclusively to the deployed web server over HTTPS and contains **zero API keys**. The Groq API key remains securely guarded on the server side.
