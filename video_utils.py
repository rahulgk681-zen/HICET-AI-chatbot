"""
Video Utilities for HICET Streamlit Chatbot.
============================================
- Automatically discovers video files (.mp4, .webm, .mov, .m4v) in videos/.
- Automatically identifies topic from filename (e.g. campus_tour.mp4 -> Campus Tour).
- Matches natural queries in English, Tamil, and Tanglish.
- Returns friendly messages and avoids duplicate video responses.
- Fully dynamic: adding new videos to videos/ requires zero code changes.
"""

import difflib
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

# ============================================================
# CONFIGURATION & DIRECTORIES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
VIDEOS_DIR = BASE_DIR / "videos"
MEDIA_DIR = BASE_DIR / "media"

SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".m4v"}

ACRONYMS = {
    "cse", "ece", "eee", "it", "mech", "civil", "ai", "aids", "aiml",
    "mba", "mca", "hicet", "ug", "pg", "phd", "rnd", "r&d", "mou", "nba", "naac"
}

# Domain synonyms for intelligent intent and topic mapping
SYNONYMS = {
    "campus": ["campus", "college", "hicet", "grounds", "overview", "infrastructure", "வளாகம்", "கேம்பஸ்"],
    "tour": ["tour", "walkthrough", "visit", "round", "guide", "சுற்றுலா"],
    "cse": ["cse", "computer", "computer science", "cs", "coding", "software", "கணினி", "சிஎஸ்இ"],
    "ece": ["ece", "electronics", "communication", "மின்னணுவியல்"],
    "eee": ["eee", "electrical"],
    "mech": ["mech", "mechanical", "இயந்திரவியல்"],
    "civil": ["civil"],
    "it": ["it", "information technology"],
    "ai": ["ai", "artificial intelligence", "data science", "aiml", "aids"],
    "admission": ["admission", "admissions", "apply", "application", "fees", "joining", "seats", "cutoff", "சேர்க்கை", "அட்மிஷன்"],
    "facilities": ["facilities", "infrastructure", "amenities", "labs", "laboratory", "sports", "cafeteria", "hostel", "gym"],
    "hostel": ["hostel", "rooms", "accommodation", "mess", "விடுதி"],
    "placement": ["placement", "placements", "jobs", "recruitment", "interview", "வேலைவாய்ப்பு"],
    "library": ["library", "books", "நூலகம்"],
}

QUERY_NOISE = {
    "show", "me", "the", "a", "an", "can", "i", "see", "you", "please",
    "video", "videos", "clip", "clips", "play", "watch", "give", "about",
    "of", "for", "any", "in", "to", "want", "like", "do", "have", "with",
    "now", "just", "get", "put", "tell", "details",
    # Tanglish & Tamil noise
    "kaatu", "kaatunga", "kudunga", "kudu", "pannu", "venum", "paakanum",
    "enakku", "podu", "anupu", "paru", "iruka", "irukka", "irukkiradha",
    "vendum", "oru", "காட்டு", "காட்டுங்கள்", "வீடியோ", "படம்", "பார்க்க",
    "போடு", "இருக்கா", "வேண்டும்", "எனக்கு", "ஒரு",
}

NEGATIVE_PATTERNS = [
    r"\bwhat\s+is\s+video\s+editing\b",
    r"\bhow\s+to\s+edit\s+video\b",
    r"\bvideo\s+editing\b",
    r"\bvideo\s+compression\b",
    r"\bvideo\s+game\b",
    r"\bvideo\s+games\b",
    r"\bdefinition\s+of\s+video\b",
]

# ============================================================
# FILENAME & TITLE FORMATTING
# ============================================================

def format_video_title(filename: str) -> str:
    """
    Generate clean, user-friendly title from filename.
    Example: 'campus_tour.mp4' -> 'Campus Tour'
             'cse_department.mp4' -> 'CSE Department'
    """
    stem = Path(filename).stem
    # Handle camelCase
    stem = re.sub(r"([a-z])([A-Z])", r"\1 \2", stem)
    # Replace separators with spaces
    words = stem.replace("_", " ").replace("-", " ").split()
    
    formatted = []
    for w in words:
        if w.lower() in ACRONYMS:
            formatted.append(w.upper())
        else:
            formatted.append(w.capitalize())
    return " ".join(formatted) if formatted else "Video"


def normalize_text(text: str) -> str:
    """Lowercase and normalize punctuation/spaces."""
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"[?!.,;:'\"/\\()[\]{}~`@#$%^&*_\-+=<>|]", " ", text)
    return " ".join(text.split())

# ============================================================
# DYNAMIC VIDEO DISCOVERY
# ============================================================

def get_available_videos() -> List[Dict]:
    """
    Scan videos/ folder for all supported video formats.
    Automatically detects new videos immediately without code changes.
    """
    if not VIDEOS_DIR.exists():
        return []

    videos = []
    seen = set()
    for item in sorted(VIDEOS_DIR.iterdir()):
        if item.is_file() and item.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS:
            fname = item.name
            if fname.lower() not in seen:
                title = format_video_title(fname)
                stem_clean = normalize_text(item.stem.replace("_", " ").replace("-", " "))
                stem_words = stem_clean.split()
                
                # Expand keywords for matching
                keywords = set(stem_words)
                keywords.add(stem_clean)
                for w in stem_words:
                    for key, syns in SYNONYMS.items():
                        if w == key or w in syns:
                            keywords.update(syns)

                rel_path = f"videos/{fname}"
                videos.append({
                    "id": item.stem.lower(),
                    "filename": fname,
                    "title": title,
                    "path": rel_path,
                    "file": rel_path,
                    "abs_path": item.resolve(),
                    "stem_words": stem_words,
                    "keywords": sorted(list(keywords)),
                })
                seen.add(fname.lower())
    return videos


def get_available_video_titles() -> List[str]:
    """Return user-friendly titles of all existing videos."""
    return [v["title"] for v in get_available_videos()]

# ============================================================
# PATH SECURITY & RESOLUTION
# ============================================================

def resolve_video_path(file_path_str: Union[str, Path]) -> Path:
    """Safely resolve video file path inside videos/ or BASE_DIR."""
    path = Path(file_path_str)
    if (VIDEOS_DIR / path.name).exists():
        return (VIDEOS_DIR / path.name).resolve()
    if not path.is_absolute():
        path = (BASE_DIR / path).resolve()
    else:
        path = path.resolve()
    return path


def is_safe_video_path(file_path: Path) -> bool:
    """Validate path has allowed extension and is inside project root."""
    try:
        resolved = file_path.resolve()
        base_resolved = BASE_DIR.resolve()
        is_inside = (resolved == base_resolved or base_resolved in resolved.parents)
        has_ext = resolved.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS
        return is_inside and has_ext
    except Exception:
        return False

# ============================================================
# INTENT DETECTION
# ============================================================

VIDEO_WORDS = {"video", "videos", "clip", "clips", "footage", "வீடியோ", "காணொளி", "காணொலி"}
ACTION_WORDS = {
    "show", "play", "watch", "see", "view", "display", "give", "stream", "send",
    "kaatu", "kaatunga", "kudunga", "podu", "paakanum", "venum", "anupu", "paru",
    "காட்டு", "காட்டுங்கள்", "பார்க்க", "போடு", "அனுப்பு"
}


def is_video_request(query: str) -> bool:
    """Detect if user query is asking to see or play a video."""
    if not query or not query.strip():
        return False

    q = normalize_text(query)

    # 1. Reject informational questions about video technology
    for pattern in NEGATIVE_PATTERNS:
        if re.search(pattern, q):
            return False

    has_video_word = any(w in q.split() or w in q for w in VIDEO_WORDS)
    has_action = any(w in q.split() for w in ACTION_WORDS)

    # 2. Contains explicit video word
    if has_video_word:
        return True

    # 3. Action + known video topic (e.g. "play campus tour", "campus tour kaatu")
    if has_action:
        for v in get_available_videos():
            for w in v["stem_words"]:
                if len(w) >= 3 and w in q.split():
                    return True

    return False

# ============================================================
# MATCHING & SCORING
# ============================================================

def _score_match(query_norm: str, video: Dict) -> float:
    """Score relevance of video to user query."""
    score = 0.0
    q_words = set(query_norm.split())
    stem_words = set(video.get("stem_words", []))
    meaningful_q = q_words - QUERY_NOISE

    # Exact stem phrase match (e.g. 'campus tour')
    stem_phrase = " ".join(video.get("stem_words", []))
    if stem_phrase and stem_phrase in query_norm:
        score += 20.0

    # Token overlap with stem words
    overlap = meaningful_q.intersection(stem_words)
    score += len(overlap) * 8.0

    # Match against keywords and synonyms
    for kw in video.get("keywords", []):
        kw_norm = normalize_text(kw)
        if kw_norm and kw_norm in query_norm:
            score += 5.0

    # Fuzzy match for typos (e.g. 'campuss', 'addmission')
    for qw in meaningful_q:
        if len(qw) >= 4:
            for sw in stem_words:
                if len(sw) >= 4 and difflib.SequenceMatcher(None, qw, sw).ratio() >= 0.8:
                    score += 6.0

    return score


def extract_topic_from_query(query: str) -> str:
    """Extract topic name from query for friendly messages."""
    q_norm = normalize_text(query)
    meaningful = [w for w in q_norm.split() if w not in QUERY_NOISE and len(w) > 1]
    if meaningful:
        return " ".join(meaningful).title()
    return "requested"


def find_matching_videos(
    query: str,
    available_videos: Optional[List[Dict]] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> Tuple[str, List[Dict], str]:
    """
    Match query to existing videos.
    Returns: (status, matched_videos, topic)
    status: 'found' | 'general' | 'unavailable'
    """
    if available_videos is None:
        available_videos = get_available_videos()

    if not available_videos:
        topic = extract_topic_from_query(query)
        return "unavailable", [], topic

    q_norm = normalize_text(query)
    meaningful = [w for w in q_norm.split() if w not in QUERY_NOISE and len(w) > 1]

    # General video request (e.g. "show video", "video kaatu", "available videos")
    if not meaningful:
        return "general", available_videos, "HICET Videos"

    scored = []
    for v in available_videos:
        s = _score_match(q_norm, v)
        if s > 0:
            scored.append((s, v))

    if scored:
        scored.sort(key=lambda x: x[0], reverse=True)
        top_score, best_video = scored[0]
        if top_score >= 4.0:
            # Single best match to prevent duplicate videos in chat
            return "found", [best_video], best_video["title"]

    topic = extract_topic_from_query(query)
    return "unavailable", [], topic

# ============================================================
# MAIN REQUEST PROCESSOR (API COMPATIBLE WITH APP.PY)
# ============================================================

def process_video_request(
    query: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict:
    """
    Process user query and return video response payload for app.py.
    """
    if not is_video_request(query):
        return {
            "is_video_request": False,
            "status": "not_a_video",
            "message": "",
            "videos_to_display": [],
            "requested_topic": "",
        }

    available = get_available_videos()
    status, matched_videos, topic = find_matching_videos(query, available_videos=available)

    # 1. Video topic not found
    if status == "unavailable" or not matched_videos:
        if available:
            titles = "\n".join(f"• {v['title']}" for v in available)
            msg = (
                f"Sorry, I couldn't find a video for **{topic}**. 🎬\n\n"
                f"**Available videos you can watch:**\n{titles}\n\n"
                f"You can ask: *\"Show me the {available[0]['title']} video\"*"
            )
        else:
            msg = (
                "Sorry, no videos are currently available.\n"
                "Please upload video files (`.mp4`, `.webm`, `.mov`, `.m4v`) into the `videos/` folder."
            )
        return {
            "is_video_request": True,
            "status": "unavailable",
            "message": msg,
            "videos_to_display": [],
            "requested_topic": topic,
        }

    # 2. General video request
    if status == "general":
        titles = "\n".join(f"• {v['title']}" for v in available)
        # Display first video as featured and list all
        return {
            "is_video_request": True,
            "status": "general",
            "message": f"🎬 Here are our available campus videos:\n\n{titles}",
            "videos_to_display": [available[0]],
            "requested_topic": "HICET Videos",
        }

    # 3. Matching video found
    video = matched_videos[0]
    return {
        "is_video_request": True,
        "status": "found",
        "message": f"🎬 Here is the **{video['title']}** video:",
        "videos_to_display": [video],
        "requested_topic": video["title"],
    }
