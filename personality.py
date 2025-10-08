import re
import json

BOT_NAME = "Baseera"

# Bilingual Personality Definitions
PERSONALITY = {
    "greeting": {
        "patterns": [r"^\s*(hi|hello|hey|halo|as-salamu alaykum|assalamualaikum)\b"],
        "response": {
            "en": f"Wa'alaikumussalam! I am {BOT_NAME}, your companion on the journey of seeking knowledge. How can I assist you today?",
            "id": f"Wa'alaikumussalam! Saya {BOT_NAME}, pendamping Anda dalam perjalanan mencari ilmu. Ada yang bisa saya bantu hari ini?"
        }
    },
    "identity": {
        "patterns": [r"\b(who are you|what are you|siapa kamu|kamu siapa)\b", r"introduce yourself"],
        "response": {
            "en": f"I am {BOT_NAME}. My purpose is to be a friendly guide, helping you find light and understanding from the Qur'an and Sunnah in a modern, accessible way.",
            "id": f"Saya {BOT_NAME}. Tujuan saya adalah menjadi pemandu yang ramah, membantu Anda menemukan cahaya dan pemahaman dari Al-Qur'an dan Sunnah dengan cara yang modern dan mudah diakses."
        }
    },
    "capability": {
        "patterns": [r"\b(what can you do|help|bantuan|bisa apa saja)\b"],
        "response": {
            "en": "You can ask me questions about the Qur'an, Hadith, and Islamic knowledge. I will do my best to provide a comprehensive answer by consulting religious texts and contemporary sources.",
            "id": "Anda bisa bertanya kepada saya mengenai Al-Qur'an, Hadis, dan pengetahuan Islam. Saya akan berusaha sebaik mungkin untuk memberikan jawaban yang komprehensif dengan merujuk pada teks-teks agama dan sumber-sumber kontemporer."
        }
    },
    "how_are_you": {
        "patterns": [r"\b(how are you|apa kabar)\b"],
        "response": {
            "en": "Alhamdulillah, I am functioning as intended and ready to assist you in your quest for knowledge.",
            "id": "Alhamdulillah, saya berfungsi sebagaimana mestinya dan siap membantu Anda dalam pencarian ilmu."
        }
    },
    "thanks": {
        "patterns": [r"\b(thank you|thanks|syukran|terima kasih)\b"],
        "response": {
            "en": "You are most welcome. It is my pleasure to help. May your knowledge be beneficial.",
            "id": "Sama-sama. Dengan senang hati saya membantu. Semoga ilmunya bermanfaat."
        }
    },
    "apology": {
        "patterns": [r"\b(sorry|maaf)\b"],
        "response": {
            "en": "No problem at all.",
            "id": "Tidak masalah."
        }
    },
    "compliment": {
        "patterns": [r"\b(good bot|you are smart|pintar sekali|keren)\b"],
        "response": {
            "en": "Thank you! I am here to serve and assist you with the knowledge I have been provided.",
            "id": "Terima kasih! Saya di sini untuk melayani dan membantu Anda dengan pengetahuan yang telah diberikan kepada saya."
        }
    },
    "bye": {
        "patterns": [r"\b(bye|goodbye|sampai jumpa)\b"],
        "response": {
            "en": "Ma'a as-salam. Feel free to return whenever you have more questions.",
            "id": "Ma'as-salam. Silakan kembali lagi jika ada pertanyaan lain."
        }
    }
}

# Bilingual Follow-up Questions
FOLLOW_UP_QUESTIONS = {
    "en": [
        "What is the story of Prophet Yusuf (Joseph)?",
        "Explain the importance of Surah Al-Fatiha."
    ],
    "id": [
        "Bagaimana kisah Nabi Yusuf?",
        "Jelaskan tentang keutamaan Surah Al-Fatihah."
    ]
}

def detect_language(query: str) -> str:
    """Detects if the query is likely Indonesian based on keywords."""
    indonesian_keywords = [
        'apa', 'siapa', 'kapan', 'dimana', 'mengapa', 'bagaimana',
        'terima kasih', 'maaf', 'halo', 'kamu'
    ]
    if any(keyword in query.lower() for keyword in indonesian_keywords):
        return "id"
    return "en"

def handle_small_talk(query: str):
    """
    Checks if a query matches any small talk patterns and responds in the detected language.
    """
    query_lower = query.lower()
    lang = detect_language(query) # Detect language first

    for intent, data in PERSONALITY.items():
        for pattern in data["patterns"]:
            if re.search(pattern, query_lower, re.IGNORECASE):
                # Format the response in the detected language
                response_json = {
                    "status": "ok",
                    "language": lang,
                    "answer": data["response"][lang],
                    "chain_of_thought": "This is a direct response based on my programmed personality.",
                    "sources": [],
                    "web_sources": [],
                    "follow_up_questions": FOLLOW_UP_QUESTIONS[lang]
                }
                return response_json
    return None