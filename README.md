# 🎓 College Information AI Chatbot (Groq LLM + Text Knowledge Base)

A powerful, blazingly fast AI-powered College Information Chatbot built with **Python**, **Groq LLMs** (OpenAI GPT-OSS 120B, GPT-OSS 20B, Llama 3.3 70B, etc.), and grounded in a **plain text document knowledge base** (`.txt`).

---

## 🌟 Key Features

- ⚡ **Ultra-Fast Groq Inference**: Powered by Groq's LPU technology with real-time token streaming.
- 📄 **Text Document Knowledge Base Grounding**: Provide any college info document (`.txt`) as the ground truth.
- 🛡️ **Anti-Hallucination Guardrails**: Adheres strictly to the supplied knowledge base and provides verified contact/helpline information when details are not found in the documents.
- 🎨 **Modern Streamlit Web UI**:
  - Interactive chat with live streaming responses.
  - Model switcher (`OpenAI GPT-OSS 120B`, `OpenAI GPT-OSS 20B`, `Llama 3.3 70B`, `Llama 3.1 8B`).
  - Drag-and-drop custom `.txt` file uploader.
  - One-click quick question suggestions (Admissions, Fees, Hostels, Placements).
  - Export chat transcripts.
- 🎬 **In-Chat Existing Video Player**:
  - Automatically identifies video playback requests in English, Tamil, and Tanglish.
  - Plays existing college videos directly within chat using native `st.video()`.
  - Supports configurable video catalog (`video_library.py`) and storage (`media/videos/`).
- 💻 **Terminal CLI Interface**: Lightweight interactive terminal REPL with live token streaming and slash commands (`/clear`, `/reload`, `/exit`).

---

## 📁 Project Structure

```
chatbot-01/
├── app.py                      # Streamlit interactive Web Application
├── chatbot.py                  # Core CollegeChatbot engine & Groq LLM integration
├── cli_chat.py                 # Terminal CLI chat interface
├── video_library.py            # Video catalog configuration and metadata
├── video_utils.py              # Video intent detection, topic matching & validation
├── college_knowledge_base.txt  # Comprehensive college knowledge base
├── media/
│   ├── videos/                 # Local directory for existing video files (.mp4, etc.)
│   └── logo.png                # Campus branding assets
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
└── README.md                   # Documentation & Setup Guide
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.8 or higher installed on your system.
- A free Groq API key from [Groq Console](https://console.groq.com/keys).

### 2. Installation

1. Open your terminal or PowerShell in this directory:
   ```bash
   cd c:\Users\acer\OneDrive\Documents\chatbot-01
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) Set up your Groq API Key in a `.env` file:
   - Copy `.env.example` to `.env`:
     ```bash
     copy .env.example .env
     ```
   - Open `.env` and paste your Groq API Key:
     ```env
     GROQ_API_KEY=gsk_your_actual_groq_api_key_here
     ```
   *(Note: You can also enter the API key directly into the Streamlit Web UI sidebar).*

---

## 🖥️ Running the Chatbot

### Option A: Web Application (Streamlit) — *Recommended*

Run the following command:
```bash
streamlit run app.py
```
This opens the web interface in your default browser at `http://localhost:8501`.

**In the Web UI, you can:**
- Select between the default sample knowledge base, uploading your own `.txt` file, or pasting raw text.
- Click any quick-prompt button or type custom questions.
- Watch responses stream in real-time.

---

### Option B: Terminal CLI

Run the following command:
```bash
python cli_chat.py
```

**CLI Commands:**
- Type any question and press Enter.
- `/clear` — Clears the conversation history.
- `/reload` — Reloads the `.txt` document from disk after you make changes.
- `/exit` — Closes the CLI.

---

## 📝 Customizing the Knowledge Base

To use your own college's details:
1. **Direct Edit**: Open [`college_knowledge_base.txt`](college_knowledge_base.txt) and edit the text with your institution's departments, eligibility criteria, fee structures, hostels, placement records, and contact details.
2. **Upload in Web UI**: Drag and drop any custom `.txt` file into the sidebar in the Streamlit app.
3. **Specify in CLI**: Pass the path to your custom `.txt` file when prompted by `cli_chat.py`.

---

## ⚙️ Supported Models on Groq
 
| Model Name | ID | Best For |
| :--- | :--- | :--- |
| **OpenAI GPT-OSS 120B (Flagship)** | `openai/gpt-oss-120b` | Flagship reasoning, complex college queries & comparisons *(Default)* |
| **OpenAI GPT-OSS 20B** | `openai/gpt-oss-20b` | High-speed, efficient responses with strong reasoning (~1,000 tps) |
| **Llama 3.3 70B (Versatile)** | `llama-3.3-70b-versatile` | General purpose reasoning & detailed answers |
| **Llama 3.1 8B (Instant)** | `llama-3.1-8b-instant` | Blazingly fast, lightweight queries |
