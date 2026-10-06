"""
Command-Line Interface (CLI) for College Information Chatbot
Powered by Groq LLM & Text Document Knowledge Base.
"""

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from chatbot import CollegeChatbot, SUPPORTED_MODELS, DEFAULT_MODEL
from dotenv import load_dotenv, set_key

ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=ENV_FILE)


def print_banner():
    print("=" * 70)
    print("       🎓 HICET COLLEGE INFORMATION AI ASSISTANT (GROQ LLM)       ")
    print("=" * 70)
    print("Commands:")
    print("  /help    - Show available commands")
    print("  /clear   - Clear conversation history")
    print("  /reload  - Reload knowledge base document from disk")
    print("  /exit    - Exit the chatbot")
    print("=" * 70)


def main():
    print_banner()

    # 1. Check API Key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or "your_actual_groq_api_key" in api_key:
        api_key = input("\n🔑 Enter your Groq API Key (or press Ctrl+C to exit): ").strip()
        if not api_key:
            print("❌ Error: Groq API Key is required to run the chatbot.")
            sys.exit(1)
        save_choice = input("💾 Save this key permanently to .env? (y/n): ").strip().lower()
        if save_choice in ["y", "yes"]:
            set_key(ENV_FILE, "GROQ_API_KEY", api_key)
            print("✅ API Key permanently saved to .env!")


    # 2. Knowledge Base Path
    default_kb_file = os.path.join(os.path.dirname(__file__), "college_knowledge_base.txt")
    kb_input = input("\n📄 Enter path to custom text file [Default: college_knowledge_base.txt]: ").strip()
    kb_path = kb_input if kb_input else default_kb_file

    print(f"\n⏳ Initializing Groq LLM ({DEFAULT_MODEL})...")
    try:
        if kb_input:
            if not os.path.exists(kb_input):
                print(f"❌ Error: Knowledge base file not found at: {kb_input}")
                sys.exit(1)
            bot = CollegeChatbot(
                api_key=api_key,
                model=DEFAULT_MODEL,
                knowledge_base_path=kb_input,
            )
            print(f"✅ Loaded custom knowledge base from '{os.path.basename(kb_input)}' ({len(bot.knowledge_base_text):,} characters).")
        else:
            bot = CollegeChatbot(
                api_key=api_key,
                model=DEFAULT_MODEL,
                knowledge_base_path=default_kb_file,
            )
            print(f"✅ Loaded permanent college knowledge base ({len(bot.knowledge_base_text):,} characters).")
        print("✅ Ready! Ask your questions about the college below.\n")
    except Exception as e:
        print(f"❌ Failed to initialize chatbot: {e}")
        sys.exit(1)

    # 3. Interactive REPL Loop
    while True:
        try:
            user_input = input("\n🧑‍🎓 You: ").strip()

            if not user_input:
                continue

            # Special commands
            if user_input.lower() in ["/exit", "exit", "quit", "/quit"]:
                print("\n👋 Thank you for using the College Assistant! Goodbye!\n")
                break

            if user_input.lower() in ["/clear", "clear"]:
                bot.clear_history()
                print("🧹 Conversation history cleared.")
                continue

            if user_input.lower() in ["/reload", "reload"]:
                bot.load_knowledge_base_file(kb_path)
                print(f"🔄 Knowledge base reloaded from '{kb_path}'.")
                continue

            if user_input.lower() in ["/help", "help"]:
                print("\nAvailable commands:")
                print("  /clear   - Clear conversation history")
                print("  /reload  - Reload knowledge base document")
                print("  /exit    - Quit the application\n")
                continue

            # Stream response
            print("\n🤖 Assistant: ", end="", flush=True)
            for token in bot.stream_chat(user_input):
                print(token, end="", flush=True)
            print("\n")

        except KeyboardInterrupt:
            print("\n\n👋 Session interrupted. Exiting...")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
