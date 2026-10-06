
"""
HICET Information AI Assistant
Backend chatbot powered by Groq LLM and local knowledge base.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Generator, Union, Any

from dotenv import load_dotenv
from groq import Groq


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

ENV_FILE = BASE_DIR / ".env"

DEFAULT_KNOWLEDGE_BASE = (
    BASE_DIR / "college_knowledge_base.txt"
)


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv(
    dotenv_path=ENV_FILE
)


# ============================================================
# MODEL CONFIGURATION
# ============================================================

PREFERRED_MODELS = [
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]

DEFAULT_MODEL = "openai/gpt-oss-20b"
SUPPORTED_MODELS = PREFERRED_MODELS


MODEL_DISPLAY_NAMES = {

    "openai/gpt-oss-20b":
        "OpenAI GPT-OSS 20B",

    "openai/gpt-oss-120b":
        "OpenAI GPT-OSS 120B",

    "llama-3.3-70b-versatile":
        "Llama 3.3 70B Versatile",

    "llama-3.1-8b-instant":
        "Llama 3.1 8B Instant",
}


EXCLUDED_MODEL_WORDS = [
    "whisper",
    "tts",
    "speech",
    "stt",
    "audio",
    "orpheus",
    "guard",
    "safeguard",
    "compound",
]


# ============================================================
# API KEY
# ============================================================

def get_api_key() -> str:

    api_key = os.getenv(
        "GROQ_API_KEY",
        ""
    ).strip()

    if not api_key:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
                api_key = str(st.secrets["GROQ_API_KEY"]).strip()
        except Exception:
            pass

    if not api_key:

        raise ValueError(
            "GROQ_API_KEY is not configured. "
            "Please add GROQ_API_KEY to your environment variables, .env file, or Streamlit secrets."
        )

    return api_key


# ============================================================
# MODEL DISCOVERY
# ============================================================

def get_available_models(
    api_key: Optional[str] = None
) -> Dict[str, str]:

    """
    Returns:

        {
            "Display Name": "actual-groq-model-id"
        }
    """

    if api_key is None:

        api_key = get_api_key()


    client = Groq(
        api_key=api_key
    )


    try:

        models_response = (
            client.models.list()
        )

    except Exception as exc:

        raise RuntimeError(
            f"Unable to retrieve Groq models: {exc}"
        ) from exc


    models = {}


    for model in models_response.data:

        model_id = getattr(
            model,
            "id",
            None
        )

        if not model_id:
            continue


        model_id_lower = (
            model_id.lower()
        )


        # Ignore speech/audio/safety models

        if any(
            word in model_id_lower
            for word in EXCLUDED_MODEL_WORDS
        ):

            continue


        display_name = (
            MODEL_DISPLAY_NAMES.get(
                model_id,
                model_id
            )
        )


        models[display_name] = model_id


    # ========================================================
    # PREFERRED MODELS FIRST
    # ========================================================

    ordered_models = {}


    for preferred_model in PREFERRED_MODELS:

        if preferred_model in models.values():

            display_name = (
                MODEL_DISPLAY_NAMES.get(
                    preferred_model,
                    preferred_model
                )
            )

            ordered_models[
                display_name
            ] = preferred_model


    # ========================================================
    # OTHER MODELS
    # ========================================================

    for display_name, model_id in models.items():

        if model_id not in ordered_models.values():

            ordered_models[
                display_name
            ] = model_id


    return ordered_models


# ============================================================
# KNOWLEDGE BASE
# ============================================================

def load_knowledge_base(
    knowledge_base_path: Union[str, Path]
    = DEFAULT_KNOWLEDGE_BASE
) -> str:

    """
    Load knowledge base from a text file.

    Accepts both:
        str
        Path
    """

    # IMPORTANT:
    # Always convert to Path.

    knowledge_base_path = Path(
        knowledge_base_path
    )


    if not knowledge_base_path.exists():

        return ""


    try:

        return knowledge_base_path.read_text(
            encoding="utf-8"
        ).strip()


    except Exception as exc:

        raise RuntimeError(
            f"Unable to read knowledge base: {exc}"
        ) from exc


# ============================================================
# COLLEGE CHATBOT
# ============================================================

class CollegeChatbot:

    def __init__(
        self,
        api_key: Optional[str] = None,

        model: str =
            "openai/gpt-oss-20b",

        knowledge_base_path: Union[
            str,
            Path
        ] = DEFAULT_KNOWLEDGE_BASE,

        knowledge_base_content: Optional[str] = None,

        temperature: float = 2.0,

        max_tokens: int = 512,
    ):

        # ====================================================
        # API KEY
        # ====================================================

        if api_key is None:

            api_key = get_api_key()


        if not api_key.strip():

            raise ValueError(
                "Groq API key is missing."
            )


        self.api_key = (
            api_key.strip()
        )


        # ====================================================
        # GROQ CLIENT
        # ====================================================

        self.client = Groq(
            api_key=self.api_key
        )


        # ====================================================
        # MODEL
        # ====================================================

        self.model = model


        # ====================================================
        # GENERATION SETTINGS
        # ====================================================

        self.temperature = (
            temperature
        )

        self.max_tokens = (
            max_tokens
        )


        # ====================================================
        # KNOWLEDGE BASE PATH
        # ====================================================

        # Convert string -> Path

        self.knowledge_base_path = Path(
            knowledge_base_path
        )


        # ====================================================
        # KNOWLEDGE BASE CONTENT
        # ====================================================

        if knowledge_base_content is not None:

            self.knowledge_base = (
                knowledge_base_content
                or ""
            ).strip()

        else:

            self.knowledge_base = (
                load_knowledge_base(
                    self.knowledge_base_path
                )
            )


        # ====================================================
        # CHAT HISTORY
        # ====================================================

        self.history: List[
            Dict[str, str]
        ] = []


    # ========================================================
    # SET MODEL
    # ========================================================

    def set_model(
        self,
        model: str
    ):

        self.model = model


    # ========================================================
    # SET API KEY
    # ========================================================

    def set_api_key(
        self,
        api_key: str
    ):

        if (
            not api_key
            or not api_key.strip()
        ):

            raise ValueError(
                "Groq API key cannot be empty."
            )


        self.api_key = (
            api_key.strip()
        )


        self.client = Groq(
            api_key=self.api_key
        )


    # ========================================================
    # SET KNOWLEDGE BASE
    # ========================================================

    def set_knowledge_base(
        self,
        content: str
    ):

        self.knowledge_base = (
            content or ""
        ).strip()


    # ========================================================
    # LOAD KNOWLEDGE BASE FROM FILE
    # ========================================================

    def load_knowledge_base_from_file(
        self,
        path: Union[str, Path]
    ):

        path = Path(path)

        self.knowledge_base_path = path

        self.knowledge_base = (
            load_knowledge_base(path)
        )

    def load_knowledge_base_file(
        self,
        path: Union[str, Path]
    ):
        self.load_knowledge_base_from_file(path)

    @property
    def knowledge_base_text(self) -> str:
        return self.knowledge_base

    def clear_history(self):
        self.history.clear()


    # ========================================================
    # SYSTEM PROMPT
    # ========================================================

    def _get_system_prompt(self) -> str:

        return f"""
You are the HICET Information AI Assistant.

HICET means Hindusthan College of Engineering and Technology.

Your job is to answer questions about HICET using the
provided college knowledge base.

IMPORTANT RULES:

1. Use the knowledge base as your primary source of truth.

2. Do NOT invent or fabricate college information.

3. If requested information is not available in the
   knowledge base, clearly state that it is not available. Do not guess or speculate.

4. Do not make up:
   - Fees
   - Cutoffs
   - Admission requirements
   - Departments
   - Seats
   - Placements
   - Contact details
   - Dates
   - Rankings
   - Other official information

5. Answer the user's question directly and concisely.

6. Keep answers clear and easy for students.

7. Use headings and bullet points when useful.

8. Use previous conversation context when relevant.

9. Understand:
   - English
   - Tamil
   - Tanglish

10. Reply in the language that best matches the
    user's question.

11. Never reveal the Groq API key.

12. Never reveal internal credentials.

13. Do not tell users to modify the API key.

14. You are an information assistant and not an
    official admissions decision-maker.

CURRENT COLLEGE KNOWLEDGE BASE:

================ BEGIN KNOWLEDGE BASE ================

{self.knowledge_base}

================= END KNOWLEDGE BASE =================

"""


    # ========================================================
    # BUILD MESSAGES
    # ========================================================

    def _build_messages(
        self,
        user_message: str
    ) -> List[Dict[str, str]]:

        messages = []


        # ----------------------------------------------------
        # SYSTEM MESSAGE
        # ----------------------------------------------------

        messages.append(
            {
                "role": "system",
                "content": self._get_system_prompt(),
            }
        )


        # ----------------------------------------------------
        # LIMITED CHAT HISTORY
        # ----------------------------------------------------
        #
        # Only use recent history.
        #
        # This helps prevent:
        #
        # context_length_exceeded
        #
        # errors.
        # ----------------------------------------------------

        MAX_HISTORY_MESSAGES = 10

        recent_history = (
            self.history[
                -MAX_HISTORY_MESSAGES:
            ]
        )


        messages.extend(
            recent_history
        )


        # ----------------------------------------------------
        # CURRENT USER QUESTION
        # ----------------------------------------------------

        messages.append(
            {
                "role": "user",
                "content": user_message,
            }
        )


        return messages


    # ========================================================
    # ASK
    # ========================================================

    def ask(
        self,
        user_message: str
    ) -> str:

        if not user_message.strip():

            return (
                "Please enter a question."
            )


        messages = (
            self._build_messages(
                user_message
            )
        )


        response = (
            self.client
            .chat
            .completions
            .create(

                model=self.model,

                messages=messages,

                temperature=self.temperature,

                max_tokens=self.max_tokens,

            )
        )


        answer = (
            response.choices[0]
            .message.content
        )


        if answer is None:

            answer = ""


        answer = answer.strip()


        # Save conversation

        self.history.append(
            {
                "role": "user",
                "content": user_message,
            }
        )


        self.history.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )


        return answer


    # ========================================================
    # STREAM CHAT
    # ========================================================

    def stream_chat(
        self,
        user_message: str
    ) -> Generator[str, None, None]:

        if not user_message.strip():

            yield (
                "Please enter a question."
            )

            return


        messages = (
            self._build_messages(
                user_message
            )
        )


        stream = (
            self.client
            .chat
            .completions
            .create(

                model=self.model,

                messages=messages,

                temperature=self.temperature,

                max_tokens=self.max_tokens,

                stream=True,

            )
        )


        complete_response = ""


        for chunk in stream:

            try:

                token = (
                    chunk
                    .choices[0]
                    .delta
                    .content
                )

            except (
                AttributeError,
                IndexError
            ):

                token = None


            if token:

                complete_response += token

                yield token


        # Save conversation

        self.history.append(
            {
                "role": "user",
                "content": user_message,
            }
        )


        self.history.append(
            {
                "role": "assistant",
                "content": (
                    complete_response.strip()
                ),
            }
        )


# ============================================================
# COMMAND LINE TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)

    print(
        "HICET Information AI Assistant"
    )

    print("=" * 60)


    try:

        api_key = get_api_key()


        models = get_available_models(
            api_key
        )


        if not models:

            print(
                "No chat models are available."
            )

            raise SystemExit


        model_list = list(
            models.items()
        )


        print(
            "\nAvailable models:"
        )


        for index, (
            name,
            model_id
        ) in enumerate(
            model_list,
            start=1
        ):

            print(
                f"{index}. "
                f"{name} "
                f"({model_id})"
            )


        try:

            choice = int(
                input(
                    "\nSelect model number: "
                )
            )

            selected_name, selected_model = (
                model_list[
                    choice - 1
                ]
            )

        except (
            ValueError,
            IndexError
        ):

            print(
                "Invalid selection. "
                "Using first model."
            )

            selected_name, selected_model = (
                model_list[0]
            )


        print(
            f"\nSelected model: "
            f"{selected_model}"
        )


        bot = CollegeChatbot(

            api_key=api_key,

            model=selected_model,

        )


        print(
            "\nType 'exit' to quit."
        )


        while True:

            question = input(
                "\nYou: "
            ).strip()


            if question.lower() == "exit":

                break


            if not question:

                continue


            try:

                answer = bot.ask(
                    question
                )

                print(
                    "\nAI:",
                    answer
                )

            except Exception as exc:

                print(
                    f"\nError: {exc}"
                )


    except Exception as exc:

        print(
            f"\nStartup error: {exc}"
        )

