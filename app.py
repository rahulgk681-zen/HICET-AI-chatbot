import os
import re
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from streamlit_mic_recorder import speech_to_text

import importlib
import chatbot
importlib.reload(chatbot)

from chatbot import CollegeChatbot, get_available_models
from auth import init_db, authenticate_user, register_user
from video_utils import process_video_request, resolve_video_path


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="HICET AI Assistant",
    page_icon="🎓",
    layout="wide",
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

ENV_FILE = BASE_DIR / ".env"
DEFAULT_KB_FILE = BASE_DIR / "college_knowledge_base.txt"
MEDIA_DIR = BASE_DIR / "media"
VIDEOS_DIR = BASE_DIR / "videos"


# ============================================================
# LOAD ENVIRONMENT VARIABLES & SECRETS
# ============================================================

load_dotenv(ENV_FILE)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    try:
        if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
            GROQ_API_KEY = str(st.secrets["GROQ_API_KEY"]).strip()
    except Exception:
        pass


# ============================================================
# CHECK API KEY
# ============================================================

if not GROQ_API_KEY:

    st.error(
        "❌ GROQ_API_KEY was not found.\n\n"
        "Please configure GROQ_API_KEY in your .env file or Streamlit secrets."
    )

    st.stop()


# ============================================================
# MOBILE & RESPONSIVE STYLING
# ============================================================

st.markdown(
    """
    <style>
    /* Responsive styling for desktop and mobile viewports */
    @media (max-width: 768px) {
        .block-container {
            padding: 1rem 0.75rem 5rem 0.75rem !important;
        }
        .stButton > button {
            min-height: 44px !important;
            font-size: 0.92rem !important;
            border-radius: 8px !important;
        }
        [data-testid="stChatMessage"] {
            padding: 0.65rem !important;
            margin-bottom: 0.5rem !important;
        }
        [data-testid="stChatMessage"] [data-testid="stVideo"],
        .stChatMessage .stVideo {
            width: 100% !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "knowledge_base" not in st.session_state:

    if DEFAULT_KB_FILE.exists():

        try:
            st.session_state.knowledge_base = (
                DEFAULT_KB_FILE.read_text(
                    encoding="utf-8"
                )
            )

        except Exception:
            st.session_state.knowledge_base = ""

    else:
        st.session_state.knowledge_base = ""

if "kb_source" not in st.session_state:
    st.session_state.kb_source = "Default knowledge base"

if "voice_language" not in st.session_state:
    st.session_state.voice_language = "en"

# Authentication state
init_db()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user" not in st.session_state:
    st.session_state.user = None

if "auth_page" not in st.session_state:
    st.session_state.auth_page = "login"

if "auth_success_msg" not in st.session_state:
    st.session_state.auth_success_msg = ""


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text):
    """Normalize text for easier matching."""

    text = text.lower().strip()

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text


# ============================================================
# FIND MEDIA FILES
# ============================================================

def get_media_images():
    """Find all supported image files inside media folder."""

    images = []

    if not MEDIA_DIR.exists():
        return images

    supported_extensions = {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp"
    }

    try:

        for path in MEDIA_DIR.rglob("*"):

            if (
                path.is_file()
                and path.suffix.lower()
                in supported_extensions
            ):
                images.append(path)

    except Exception:
        pass

    return sorted(
        images,
        key=lambda x: x.name.lower()
    )


# ============================================================
# IMAGE ALIASES
# ============================================================

IMAGE_ALIASES = {

    "campus": [
        "campus",
        "college campus",
        "college",
        "hicet campus",
        "campus image",
        "college image",
    ],

    "hicet": [
        "hicet",
        "hicet image",
        "hicet college",
        "college image",
    ],
}


# ============================================================
# IMAGE REQUEST WORDS
# ============================================================

IMAGE_REQUEST_WORDS = [

    # English
    "image",
    "images",
    "photo",
    "photos",
    "picture",
    "pictures",
    "show",
    "display",
    "view",
    "pic",

    # Tamil
    "படம்",
    "புகைப்படம்",
    "காட்டு",
    "காட்டுங்கள்",
    "படத்தைக்",
    "படத்தை",
]


# ============================================================
# CHECK WHETHER USER REQUESTED AN IMAGE
# ============================================================

def is_image_request(query):
    """Check whether the user is asking for an image."""

    query = normalize_text(query)

    for word in IMAGE_REQUEST_WORDS:

        if word in query:
            return True

    return False


# ============================================================
# FIND MATCHING IMAGES
# ============================================================

def find_matching_images(query):
    """
    Find images based on:
    1. Known aliases
    2. Automatic filename matching
    """

    query_normalized = normalize_text(query)

    images = get_media_images()

    if not images:
        return []

    # --------------------------------------------------------
    # Only search images when the user asks for one
    # --------------------------------------------------------

    if not is_image_request(query_normalized):
        return []

    matched_images = []

    # --------------------------------------------------------
    # FIRST: Check known aliases
    # --------------------------------------------------------

    for image_path in images:

        filename = normalize_text(
            image_path.stem
            .replace("_", " ")
            .replace("-", " ")
        )

        for alias_key, aliases in IMAGE_ALIASES.items():

            if alias_key not in filename:
                continue

            for alias in aliases:

                if alias in query_normalized:

                    if image_path not in matched_images:

                        matched_images.append(
                            image_path
                        )

                    break

    # --------------------------------------------------------
    # SECOND: Automatic filename matching
    # --------------------------------------------------------

    query_words = set(
        re.findall(
            r"[a-zA-Z0-9]+",
            query_normalized
        )
    )

    for image_path in images:

        filename = normalize_text(
            image_path.stem
            .replace("_", " ")
            .replace("-", " ")
        )

        filename_words = set(
            re.findall(
                r"[a-zA-Z0-9]+",
                filename
            )
        )

        if query_words.intersection(
            filename_words
        ):

            if image_path not in matched_images:

                matched_images.append(
                    image_path
                )

    return matched_images


# ============================================================
# DISPLAY IMAGES
# ============================================================

def display_images(images):
    """Display requested images at a smaller size."""

    if not images:
        return

    st.markdown("### 🖼️ Image")

    for image_path in images:

        image_path = Path(image_path)

        if not image_path.exists():

            st.warning(
                f"Image not found: {image_path.name}"
            )

            continue

        try:

            caption = (
                image_path
                .stem
                .replace("_", " ")
                .replace("-", " ")
                .title()
            )

            # ------------------------------------------------
            # IMAGE DISPLAY SIZE
            # ------------------------------------------------
            # Change 500 to 400 or 350 if you want smaller.
            # This changes only the displayed size.
            # It does NOT reduce the actual image file size.
            # ------------------------------------------------

            st.image(
                image_path,
                caption=caption,
                width=500,
            )

        except Exception as e:

            st.error(
                f"Could not display "
                f"{image_path.name}: {e}"
            )


# ============================================================
# DISPLAY VIDEOS
# ============================================================

def display_videos(videos):
    """
    Display requested existing videos inside the chat message.
    Renders the video player at approximately 55% chat width, neatly aligned,
    preserving original aspect ratio and full video quality.
    """
    if not videos:
        return

    # Subtle modern styling for in-chat video player
    st.markdown(
        """
        <style>
        [data-testid="stChatMessage"] [data-testid="stVideo"],
        .stChatMessage .stVideo {
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.12);
            margin: 0.4rem 0;
        }
        [data-testid="stChatMessage"] [data-testid="stVideo"] video,
        .stChatMessage .stVideo video {
            border-radius: 12px;
            display: block;
            width: 100% !important;
            height: auto !important;
            aspect-ratio: auto !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    seen_paths = set()
    for video_item in videos:
        if isinstance(video_item, dict):
            title = video_item.get("title", "Video")
            description = video_item.get("description", "")
            file_path_str = video_item.get("path") or video_item.get("file", "")
            path = resolve_video_path(file_path_str)
        else:
            path = resolve_video_path(str(video_item))
            title = f"{path.stem.replace('_', ' ').replace('-', ' ').title()}"
            description = ""

        canonical_path = str(path.resolve())
        if canonical_path in seen_paths:
            continue
        seen_paths.add(canonical_path)

        if not path.exists():
            st.warning(f"⚠️ Video file '{path.name}' is currently unavailable.")
            continue

        if description:
            st.caption(description)

        try:
            # Video player occupies ~55% of chat width, neatly aligned with assistant message
            col_video, _ = st.columns([55, 45])
            with col_video:
                st.video(str(path))
        except Exception as e:
            st.error(f"Error loading video: {e}")





# ============================================================
# AUTHENTICATION UI
# ============================================================

def render_auth_page():
    """Render a modern, responsive, centered login and registration page."""

    st.markdown(
        """
        <style>
        .auth-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 9999px;
            background: rgba(13, 71, 161, 0.2);
            border: 1px solid rgba(0, 188, 212, 0.35);
            color: #38bdf8;
            font-size: 0.8rem;
            font-weight: 600;
            letter-spacing: 0.5px;
            margin-bottom: 0.6rem;
            text-transform: uppercase;
        }
        .auth-title {
            font-size: 1.7rem;
            font-weight: 700;
            margin: 0.2rem 0;
            background: linear-gradient(90deg, #3b82f6, #06b6d4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .auth-subtitle {
            font-size: 0.92rem;
            color: #94a3b8;
            margin-bottom: 1.2rem;
            line-height: 1.5;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _, center_col, _ = st.columns([1, 2.2, 1])

    with center_col:
        # Header with Logo & Branding
        logo_file = MEDIA_DIR / "logo.png"
        col_logo, col_head = st.columns([1, 3.5])
        with col_logo:
            if logo_file.exists():
                st.image(str(logo_file), width=75)
            else:
                st.markdown("<h1 style='margin:0;'>🎓</h1>", unsafe_allow_html=True)
        with col_head:
            st.markdown(
                """
                <span class="auth-badge">HICET AI Campus Portal</span>
                <div class="auth-title">HICET AI Assistant</div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            """
            <div class="auth-subtitle">
                Official AI Assistant for Hindusthan College of Engineering and Technology. Please sign in or create an account to get started.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Show pending status message (e.g., after successful registration)
        if st.session_state.auth_success_msg:
            st.success(f"✅ {st.session_state.auth_success_msg}")
            st.session_state.auth_success_msg = ""

        # Login View
        if st.session_state.auth_page == "login":
            st.markdown("### 🔐 Sign In")

            with st.form(key="login_form", clear_on_submit=False):
                identifier = st.text_input(
                    "Email or Username",
                    placeholder="Enter your username or email address",
                    key="login_user_input",
                )
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                    key="login_pwd_input",
                )

                submit_login = st.form_submit_button(
                    "🚀 Sign In",
                    use_container_width=True,
                    type="primary",
                )

                if submit_login:
                    user_data, msg = authenticate_user(identifier, password)
                    if user_data:
                        st.session_state.authenticated = True
                        st.session_state.user = user_data
                        st.session_state.auth_success_msg = ""
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

            st.write("")
            col_hint, col_btn = st.columns([3, 2])
            with col_hint:
                st.write("Don't have an account?")
            with col_btn:
                if st.button("✨ Create Account", use_container_width=True):
                    st.session_state.auth_page = "register"
                    st.rerun()

        # Registration View
        elif st.session_state.auth_page == "register":
            st.markdown("### ✨ Create an Account")

            with st.form(key="register_form", clear_on_submit=False):
                full_name = st.text_input(
                    "Full Name",
                    placeholder="e.g. Rahul Sharma",
                    key="reg_name_input",
                )
                email = st.text_input(
                    "Email Address",
                    placeholder="e.g. rahul@hicet.ac.in",
                    key="reg_email_input",
                )
                username = st.text_input(
                    "Username",
                    placeholder="Choose a username (letters, numbers, _)",
                    key="reg_user_input",
                )
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Minimum 6 characters",
                    key="reg_pwd_input",
                )
                confirm_password = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="Re-enter your password",
                    key="reg_cpwd_input",
                )

                submit_register = st.form_submit_button(
                    "📝 Register Account",
                    use_container_width=True,
                    type="primary",
                )

                if submit_register:
                    success, msg = register_user(
                        full_name=full_name,
                        username=username,
                        email=email,
                        password=password,
                        confirm_password=confirm_password,
                    )
                    if success:
                        st.session_state.auth_success_msg = msg
                        st.session_state.auth_page = "login"
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

            st.write("")
            col_hint, col_btn = st.columns([3, 2])
            with col_hint:
                st.write("Already have an account?")
            with col_btn:
                if st.button("🔐 Sign In", use_container_width=True):
                    st.session_state.auth_page = "login"
                    st.rerun()


# ============================================================
# AUTHENTICATION GATE
# ============================================================

if not st.session_state.authenticated:
    render_auth_page()
    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    # --------------------------------------------------------
    # USER PROFILE & LOGOUT
    # --------------------------------------------------------
    current_user = st.session_state.get("user") or {}
    user_name = current_user.get("full_name", "Student")
    user_uname = current_user.get("username", "user")
    user_mail = current_user.get("email", "")

    st.markdown(
        f"""
        <div style="background: rgba(13, 71, 161, 0.1); border: 1px solid rgba(13, 71, 161, 0.3); border-radius: 12px; padding: 12px 14px; margin-bottom: 12px;">
            <div style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.7;">Logged in as</div>
            <div style="font-weight: 700; font-size: 1.05rem; margin-top: 2px;">👤 {user_name}</div>
            <div style="font-size: 0.8rem; opacity: 0.75; word-break: break-all;">@{user_uname} • {user_mail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.session_state.messages = []
        st.session_state.auth_page = "login"
        st.session_state.auth_success_msg = "You have been logged out successfully."
        st.rerun()

    st.divider()

    st.title("⚙️ Settings")

    st.divider()

    # --------------------------------------------------------
    # MODEL SELECTION
    # --------------------------------------------------------

    st.subheader("🤖 AI Model")

    try:

        available_models = get_available_models(
            api_key=GROQ_API_KEY
        )

    except Exception:

        available_models = {}


    # Fallback models

    if not available_models:

        available_models = {

            "OpenAI GPT-OSS 20B":
                "openai/gpt-oss-20b",

            "OpenAI GPT-OSS 120B":
                "openai/gpt-oss-120b",

            "Llama 3.3 70B Versatile":
                "llama-3.3-70b-versatile",

            "Llama 3.1 8B Instant":
                "llama-3.1-8b-instant",
        }


    if isinstance(
        available_models,
        dict
    ):

        model_names = list(
            available_models.keys()
        )

        selected_model_name = st.selectbox(
            "Select model",
            model_names,
        )

        selected_model = available_models[
            selected_model_name
        ]

    else:

        selected_model = st.selectbox(
            "Select model",
            available_models,
        )


    # --------------------------------------------------------
    # FIXED MODEL PARAMETERS (NOT EDITABLE BY USERS)
    # --------------------------------------------------------

    temperature = 2.0
    max_tokens = 512


    st.divider()


    # --------------------------------------------------------
    # VOICE LANGUAGE
    # --------------------------------------------------------

    st.subheader("🎤 Voice Search")

    voice_language_name = st.selectbox(
        "Voice language",
        [
            "English",
            "Tamil",
            "Tanglish",
        ],
    )

    if voice_language_name == "English":

        st.session_state.voice_language = "en"

    elif voice_language_name == "Tamil":

        st.session_state.voice_language = "ta"

    else:

        st.session_state.voice_language = "en"


    # --------------------------------------------------------
    # KNOWLEDGE BASE
    # --------------------------------------------------------

    st.divider()

    st.subheader("📚 Knowledge Base")

    kb_option = st.radio(
        "Knowledge source",
        [
            "Default knowledge base",
            "Upload text file",
            "Enter manually",
        ],
    )


    # --------------------------------------------------------
    # DEFAULT KNOWLEDGE BASE
    # --------------------------------------------------------

    if kb_option == "Default knowledge base":

        if DEFAULT_KB_FILE.exists():

            try:

                st.session_state.knowledge_base = (
                    DEFAULT_KB_FILE.read_text(
                        encoding="utf-8"
                    )
                )

                st.session_state.kb_source = (
                    "Default knowledge base"
                )

                st.success(
                    "✅ Default knowledge base loaded"
                )

            except Exception as e:

                st.error(
                    f"Could not read knowledge base: {e}"
                )

        else:

            st.warning(
                "college_knowledge_base.txt not found."
            )


    # --------------------------------------------------------
    # UPLOAD KNOWLEDGE BASE
    # --------------------------------------------------------

    elif kb_option == "Upload text file":

        uploaded_file = st.file_uploader(
            "Upload knowledge base",
            type=["txt"],
        )

        if uploaded_file:

            try:

                uploaded_text = (
                    uploaded_file
                    .read()
                    .decode("utf-8")
                )

                st.session_state.knowledge_base = (
                    uploaded_text
                )

                st.session_state.kb_source = (
                    uploaded_file.name
                )

                st.success(
                    "✅ Knowledge base uploaded"
                )

            except Exception as e:

                st.error(
                    f"Could not read file: {e}"
                )


    # --------------------------------------------------------
    # MANUAL KNOWLEDGE BASE
    # --------------------------------------------------------

    elif kb_option == "Enter manually":

        manual_text = st.text_area(
            "Enter knowledge base",
            value=st.session_state.knowledge_base,
            height=250,
        )

        if st.button(
            "💾 Save knowledge base"
        ):

            st.session_state.knowledge_base = (
                manual_text
            )

            st.session_state.kb_source = (
                "Manual knowledge base"
            )

            st.success(
                "✅ Knowledge base saved"
            )





    # --------------------------------------------------------
    # CLEAR CHAT
    # --------------------------------------------------------

    st.divider()

    if st.button(
        "🗑️ Clear chat",
        use_container_width=True,
    ):

        st.session_state.messages = []

        st.rerun()


    # --------------------------------------------------------
    # EXPORT CHAT
    # --------------------------------------------------------

    if st.session_state.messages:

        export_text = ""

        for message in st.session_state.messages:

            role = message.get(
                "role",
                "unknown"
            )

            content = message.get(
                "content",
                ""
            )

            export_text += (
                f"{role.upper()}:\n"
                f"{content}\n\n"
            )

        st.download_button(
            "📥 Export chat",
            data=export_text,
            file_name="hicet_chat_history.txt",
            mime="text/plain",
            use_container_width=True,
        )


# ============================================================
# MAIN HEADER
# ============================================================

st.title("🎓 HICET AI Assistant")

st.markdown(
    """
Ask questions about **HICET**, courses, departments,
admission, facilities, campus information and more.
"""
)


# ============================================================
# KNOWLEDGE BASE STATUS
# ============================================================

with st.expander(
    "📚 Knowledge Base Information"
):
    st.markdown("**College Knowledge Base (Text):**")
    st.write(
        f"• **Source:** {st.session_state.kb_source}"
    )
    st.write(
        f"• **Characters:** {len(st.session_state.knowledge_base):,}"
    )


# ============================================================
# QUICK QUESTIONS
# ============================================================

st.subheader("💡 Quick Questions")

quick_questions = [

    "What departments are available?",

    "What are the admission requirements?",

    "Show me the college campus image.",

    "What facilities are available?",

]


cols = st.columns(4)

for index, question in enumerate(
    quick_questions
):

    with cols[index]:

        if st.button(
            question,
            use_container_width=True,
        ):

            st.session_state.quick_question = (
                question
            )

            st.rerun()


# ============================================================
# CHAT HISTORY
# ============================================================

for message in st.session_state.messages:

    role = message.get(
        "role",
        "assistant"
    )

    content = message.get(
        "content",
        ""
    )

    images = message.get(
        "images",
        []
    )

    videos = message.get(
        "videos",
        []
    )

    if role not in [
        "user",
        "assistant"
    ]:

        continue

    with st.chat_message(role):

        if content:

            st.markdown(content)



        if images:

            display_images(images)

        if videos:

            display_videos(videos)


# ============================================================
# VOICE SEARCH
# ============================================================

st.divider()

st.subheader("💬 Ask HICET AI")


# ============================================================
# TEXT + VOICE INPUT
# ============================================================

col1, col2 = st.columns(
    [8, 1]
)


with col1:

    typed_prompt = st.chat_input(
        "Type your question here..."
    )


with col2:

    voice_prompt = speech_to_text(
        language=st.session_state.voice_language,
        start_prompt="🎤",
        stop_prompt="⏹️",
        just_once=True,
        use_container_width=True,
        key="voice_input",
    )


# ============================================================
# DETERMINE USER PROMPT
# ============================================================

prompt = None


if typed_prompt:

    prompt = typed_prompt


elif voice_prompt:

    prompt = voice_prompt


elif (
    "quick_question"
    in st.session_state
):

    prompt = st.session_state.quick_question

    del st.session_state.quick_question


# ============================================================
# PROCESS USER PROMPT
# ============================================================

if prompt:

    prompt = prompt.strip()

    if not prompt:
        st.stop()


    # ========================================================
    # SAVE USER MESSAGE
    # ========================================================

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
            "images": [],
            "videos": [],
            "sources": [],
        }
    )


    # ========================================================
    # SHOW USER MESSAGE
    # ========================================================

    with st.chat_message("user"):

        st.markdown(prompt)


    # ========================================================
    # CHECK FOR VIDEO REQUEST
    # ========================================================

    video_result = process_video_request(
        prompt,
        api_key=GROQ_API_KEY,
        model=selected_model,
    )

    if video_result.get("is_video_request"):

        with st.chat_message("assistant"):

            msg = video_result.get("message", "")
            videos_to_show = video_result.get("videos_to_display", [])

            if msg:
                st.markdown(msg)

            if videos_to_show:
                display_videos(videos_to_show)

        # ----------------------------------------------------
        # Save video response in session state
        # ----------------------------------------------------

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": video_result.get("message", ""),
                "images": [],
                "videos": [
                    {
                        "id": v.get("id"),
                        "title": v.get("title"),
                        "description": v.get("description", ""),
                        "file": str(v.get("file") or v.get("path")),
                        "path": str(v.get("path") or v.get("file")),
                    }
                    for v in video_result.get("videos_to_display", [])
                ],
                "sources": [],
            }
        )

        # ----------------------------------------------------
        # Stop here so Groq does NOT generate an extra or
        # duplicate response
        # ----------------------------------------------------

        st.stop()


    # ========================================================
    # CHECK FOR IMAGE REQUEST
    # ========================================================

    matched_images = find_matching_images(
        prompt
    )


    # ========================================================
    # IMAGE RESPONSE
    # ========================================================

    if matched_images:

        with st.chat_message("assistant"):

            display_images(
                matched_images
            )


        # ----------------------------------------------------
        # Save image response
        # ----------------------------------------------------

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": "",
                "images": [
                    str(path)
                    for path in matched_images
                ],
                "videos": [],
                "sources": [],
            }
        )


        # ----------------------------------------------------
        # IMPORTANT:
        # Stop here so Groq does NOT generate another
        # response such as "I cannot display images."
        # ----------------------------------------------------

        st.stop()


    # ========================================================
    # CREATE CHATBOT
    # ========================================================

    try:

        bot = CollegeChatbot(

            api_key=GROQ_API_KEY,

            model=selected_model,

            knowledge_base_path=DEFAULT_KB_FILE,

            knowledge_base_content=(
                st.session_state.knowledge_base
            ),

            temperature=temperature,

            max_tokens=max_tokens,
        )


    except Exception as e:

        with st.chat_message("assistant"):

            st.error(
                f"❌ Could not initialize chatbot:\n\n{e}"
            )

        st.stop()


    # ========================================================
    # GENERATE AI RESPONSE
    # ========================================================

    with st.chat_message("assistant"):

        response_placeholder = st.empty()

        full_response = ""


        try:

            # ------------------------------------------------
            # Build conversation history
            # ------------------------------------------------

            history = []

            for message in (
                st.session_state.messages[:-1]
            ):

                if message.get("role") in [
                    "user",
                    "assistant",
                ]:

                    content = message.get(
                        "content",
                        ""
                    )

                    if content:

                        history.append(
                            {
                                "role": message[
                                    "role"
                                ],
                                "content": content,
                            }
                        )


            # ------------------------------------------------
            # Generate response
            # ------------------------------------------------

            response = bot.stream_chat(prompt)
        
            # ------------------------------------------------
            # Streaming response
            # ------------------------------------------------

            if isinstance(
                response,
                str
            ):

                full_response = response

                response_placeholder.markdown(
                    full_response
                )

            else:

                for chunk in response:

                    if chunk:

                        full_response += str(
                            chunk
                        )

                        response_placeholder.markdown(
                            full_response
                        )


            # ------------------------------------------------
            # Save assistant response
            # ------------------------------------------------

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": full_response,
                    "images": [],
                    "videos": [],
                }
            )


        except Exception as e:

            error_message = (
                "❌ Sorry, something went wrong.\n\n"
                f"`{e}`"
            )

            response_placeholder.error(
                error_message
            )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": error_message,
                    "images": [],
                    "videos": [],
                    "sources": [],
                }
            )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🎓 HICET AI Assistant • Powered by Groq"
)