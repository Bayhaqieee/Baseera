from flask import Flask, render_template, request, jsonify, abort
from dotenv import load_dotenv
import json
import re
import random
import time
import tiktoken

load_dotenv()

import config
import data_pipeline
import vector_store
import crew_setup
from personality import handle_small_talk

app = Flask(__name__)
crew = None
hadith_data_cache = None 

# --- RATE LIMIT CONFIGURATION ---
# Limit: 2000 tokens per IP per 24 hours
DAILY_TOKEN_LIMIT = 2000
RESET_INTERVAL = 86400 # 24 hours in seconds

# In-memory store: { '127.0.0.1': { 'tokens_used': 0, 'reset_time': 1234567890 } }
ip_token_usage = {}

def get_token_count(text):
    """Counts tokens using tiktoken (cl100k_base is used for GPT-3.5/4)."""
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception as e:
        print(f"Token counting error: {e}")
        # Fallback approximation: ~4 characters per token
        return len(text) // 4

def check_rate_limit(ip_address, input_text):
    """
    Checks if the IP has enough quota for the input text.
    Returns (allowed: bool, message: str)
    """
    current_time = time.time()
    
    # Get or initialize usage record for this IP
    usage_record = ip_token_usage.get(ip_address, {'tokens_used': 0, 'reset_time': current_time + RESET_INTERVAL})
    
    # Check if quota needs reset
    if current_time > usage_record['reset_time']:
        usage_record = {
            'tokens_used': 0, 
            'reset_time': current_time + RESET_INTERVAL
        }
    
    # Calculate tokens for THIS request
    request_tokens = get_token_count(input_text)
    
    # Check if limit would be exceeded
    if usage_record['tokens_used'] + request_tokens > DAILY_TOKEN_LIMIT:
        remaining = max(0, DAILY_TOKEN_LIMIT - usage_record['tokens_used'])
        return False, f"Daily token limit exceeded. You have {remaining} tokens left, but this request requires {request_tokens}."
    
    # Update usage
    usage_record['tokens_used'] += request_tokens
    ip_token_usage[ip_address] = usage_record
    
    return True, None

# --- Qari Data ---
QARI_LIST = {
    "01": {"name": "Abdullah Al-Juhany", "image": "src/image/abdullah-al-juhany.jpg"},
    "02": {"name": "Abdul Muhsin Al-Qasim", "image": "src/image/Abdul_Mohsin_Al-Qasim.jpg"},
    "03": {"name": "Abdurrahman As-Sudais", "image": "src/image/Abdul-Rahman-Al-Sudais.jpg"},
    "04": {"name": "Ibrahim Al-Dossari", "image": "src/image/ibrahim-al-dosari.png"},
    "05": {"name": "Misyari Rasyid Al-Afasy", "image": "src/image/misyari-rasyid-al-afasy.jpeg"}
}

# Mapping IDs to API URL Slugs for Audio
QARI_SLUGS = {
    "01": "Abdullah-Al-Juhany",
    "02": "Abdul-Muhsin-Al-Qasim",
    "03": "Abdurrahman-as-Sudais",
    "04": "Ibrahim-Al-Dossari",
    "05": "Misyari-Rasyid-Al-Afasi"
}

DEFAULT_QARI = "05" 

# --- JUZ MAPPING ---
JUZ_MAPPING = {
    1: [{'surah': 1, 'start': 1, 'end': 7}, {'surah': 2, 'start': 1, 'end': 141}],
    2: [{'surah': 2, 'start': 142, 'end': 252}],
    3: [{'surah': 2, 'start': 253, 'end': 286}, {'surah': 3, 'start': 1, 'end': 92}],
    4: [{'surah': 3, 'start': 93, 'end': 200}, {'surah': 4, 'start': 1, 'end': 23}],
    5: [{'surah': 4, 'start': 24, 'end': 147}],
    6: [{'surah': 4, 'start': 148, 'end': 176}, {'surah': 5, 'start': 1, 'end': 81}],
    7: [{'surah': 5, 'start': 82, 'end': 120}, {'surah': 6, 'start': 1, 'end': 110}],
    8: [{'surah': 6, 'start': 111, 'end': 165}, {'surah': 7, 'start': 1, 'end': 87}],
    9: [{'surah': 7, 'start': 88, 'end': 206}, {'surah': 8, 'start': 1, 'end': 40}],
    10: [{'surah': 8, 'start': 41, 'end': 75}, {'surah': 9, 'start': 1, 'end': 92}],
    11: [{'surah': 9, 'start': 93, 'end': 129}, {'surah': 10, 'start': 1, 'end': 109}, {'surah': 11, 'start': 1, 'end': 5}],
    12: [{'surah': 11, 'start': 6, 'end': 123}, {'surah': 12, 'start': 1, 'end': 52}],
    13: [{'surah': 12, 'start': 53, 'end': 111}, {'surah': 13, 'start': 1, 'end': 43}, {'surah': 14, 'start': 1, 'end': 52}],
    14: [{'surah': 15, 'start': 1, 'end': 99}, {'surah': 16, 'start': 1, 'end': 128}],
    15: [{'surah': 17, 'start': 1, 'end': 111}, {'surah': 18, 'start': 1, 'end': 74}],
    16: [{'surah': 18, 'start': 75, 'end': 110}, {'surah': 19, 'start': 1, 'end': 98}, {'surah': 20, 'start': 1, 'end': 135}],
    17: [{'surah': 21, 'start': 1, 'end': 112}, {'surah': 22, 'start': 1, 'end': 78}],
    18: [{'surah': 23, 'start': 1, 'end': 118}, {'surah': 24, 'start': 1, 'end': 64}, {'surah': 25, 'start': 1, 'end': 20}],
    19: [{'surah': 25, 'start': 21, 'end': 77}, {'surah': 26, 'start': 1, 'end': 227}, {'surah': 27, 'start': 1, 'end': 55}],
    20: [{'surah': 27, 'start': 56, 'end': 93}, {'surah': 28, 'start': 1, 'end': 88}, {'surah': 29, 'start': 1, 'end': 45}],
    21: [{'surah': 29, 'start': 46, 'end': 69}, {'surah': 30, 'start': 1, 'end': 60}, {'surah': 31, 'start': 1, 'end': 34}, {'surah': 32, 'start': 1, 'end': 30}, {'surah': 33, 'start': 1, 'end': 30}],
    22: [{'surah': 33, 'start': 31, 'end': 73}, {'surah': 34, 'start': 1, 'end': 54}, {'surah': 35, 'start': 1, 'end': 45}, {'surah': 36, 'start': 1, 'end': 27}],
    23: [{'surah': 36, 'start': 28, 'end': 83}, {'surah': 37, 'start': 1, 'end': 182}, {'surah': 38, 'start': 1, 'end': 88}, {'surah': 39, 'start': 1, 'end': 31}],
    24: [{'surah': 39, 'start': 32, 'end': 75}, {'surah': 40, 'start': 1, 'end': 85}, {'surah': 41, 'start': 1, 'end': 46}],
    25: [{'surah': 41, 'start': 47, 'end': 54}, {'surah': 42, 'start': 1, 'end': 53}, {'surah': 43, 'start': 1, 'end': 89}, {'surah': 44, 'start': 1, 'end': 59}, {'surah': 45, 'start': 1, 'end': 37}],
    26: [{'surah': 46, 'start': 1, 'end': 35}, {'surah': 47, 'start': 1, 'end': 38}, {'surah': 48, 'start': 1, 'end': 29}, {'surah': 49, 'start': 1, 'end': 18}, {'surah': 50, 'start': 1, 'end': 45}, {'surah': 51, 'start': 1, 'end': 30}],
    27: [{'surah': 51, 'start': 31, 'end': 60}, {'surah': 52, 'start': 1, 'end': 49}, {'surah': 53, 'start': 1, 'end': 62}, {'surah': 54, 'start': 1, 'end': 55}, {'surah': 55, 'start': 1, 'end': 78}, {'surah': 56, 'start': 1, 'end': 96}, {'surah': 57, 'start': 1, 'end': 29}],
    28: [{'surah': 58, 'start': 1, 'end': 22}, {'surah': 59, 'start': 1, 'end': 24}, {'surah': 60, 'start': 1, 'end': 13}, {'surah': 61, 'start': 1, 'end': 14}, {'surah': 62, 'start': 1, 'end': 11}, {'surah': 63, 'start': 1, 'end': 11}, {'surah': 64, 'start': 1, 'end': 18}, {'surah': 65, 'start': 1, 'end': 12}, {'surah': 66, 'start': 1, 'end': 12}],
    29: [{'surah': 67, 'start': 1, 'end': 30}, {'surah': 68, 'start': 1, 'end': 52}, {'surah': 69, 'start': 1, 'end': 52}, {'surah': 70, 'start': 1, 'end': 44}, {'surah': 71, 'start': 1, 'end': 28}, {'surah': 72, 'start': 1, 'end': 28}, {'surah': 73, 'start': 1, 'end': 20}, {'surah': 74, 'start': 1, 'end': 56}, {'surah': 75, 'start': 1, 'end': 40}, {'surah': 76, 'start': 1, 'end': 31}, {'surah': 77, 'start': 1, 'end': 50}],
    30: [{'surah': 78, 'start': 1, 'end': 40}, {'surah': 114, 'start': 1, 'end': 6}]
}

# --- HELPER FUNCTIONS ---
def to_eastern_arabic_numerals(number):
    """Converts a standard integer to Eastern Arabic numerals."""
    eastern_numerals = '٠١٢٣٤٥٦٧٨٩'
    return ''.join(eastern_numerals[int(digit)] for digit in str(number))

def initialize_crew():
    global crew
    if crew is None:
        print("--- Initializing Crew for the first time ---")
        retrievers = vector_store.get_milvus_retrievers()
        if retrievers and all(retrievers):
            crew = crew_setup.create_crew(*retrievers)
            print("--- Crew Initialized Successfully ---")
        else:
            print("--- Crew Initialization Failed: Retrievers not available. Run /ingest first. ---")

def get_hadith_df():
    global hadith_data_cache
    if hadith_data_cache is None:
        print("Loading Hadith data for dictionary...")
        hadith_data_cache = data_pipeline.load_hadith_for_dictionary()
    return hadith_data_cache

# --- ROUTES ---

@app.route('/')
def chat_page():
    return render_template('chat.html')

@app.route('/quran')
def quran_page():
    quran_data = data_pipeline.get_quran_surah_list()
    return render_template('quran.html', quran_data=quran_data)

@app.route('/quran/<int:surah_id>')
def quran_detail_page(surah_id):
    surah_data = data_pipeline.get_quran_surah_detail(surah_id)
    if surah_data is None:
        abort(404)
    return render_template('quran_detail.html', surah=surah_data)

@app.route('/hadith')
def hadith_page():
    hadith_df = get_hadith_df()
    sources = data_pipeline.get_hadith_sources(hadith_df)
    return render_template('hadith.html', sources=sources)

@app.route('/hadith/<source_slug>')
def hadith_chapters_page(source_slug):
    hadith_df = get_hadith_df()
    chapters, source_name = data_pipeline.get_chapters_for_source(hadith_df, source_slug)
    if not chapters and source_name == "Unknown":
        abort(404)
    return render_template('hadith_chapters.html', chapters=chapters, source_name=source_name, source_slug=source_slug)

@app.route('/hadith/<source_slug>/<chapter_slug>')
def hadith_list_page(source_slug, chapter_slug):
    hadith_df = get_hadith_df()
    hadiths, source_name, chapter_name = data_pipeline.get_hadiths_for_chapter(hadith_df, source_slug, chapter_slug)
    if not hadiths and source_name == "Unknown":
        abort(404)
    return render_template('hadith_list.html', hadith_data=hadiths, source_name=source_name, chapter_name=chapter_name, source_slug=source_slug)

@app.route('/murajaah')
def murajaah_page():
    if not data_pipeline.check_connectivity():
        return render_template('murajaah.html', is_offline=True)
    
    surah_list = data_pipeline.get_quran_surah_list()
    return render_template('murajaah.html', 
                           is_offline=False, 
                           qari_list=QARI_LIST, 
                           default_qari=DEFAULT_QARI, 
                           surah_list=surah_list)

@app.route('/murajaah/surat/<int:surah_id>')
def murajaah_detail_page(surah_id):
    if not data_pipeline.check_connectivity():
        return render_template('murajaah.html', is_offline=True)
    
    qari_key = request.args.get('qari', DEFAULT_QARI)
    if qari_key not in QARI_LIST:
        qari_key = DEFAULT_QARI

    surah_data = data_pipeline.get_quran_surah_detail(surah_id)
    if surah_data is None:
        abort(404)
        
    qari_name = QARI_LIST.get(qari_key, {}).get("name", "Unknown Qari")
    next_surah_id = surah_id + 1 if surah_id < 114 else 1
    
    full_arabic_text = ""
    for ayat in surah_data.get('ayat', []):
        audio_src = ayat.get('audio', {}).get(qari_key, '')
        ayat_number = ayat.get('nomorAyat')
        arabic_number = to_eastern_arabic_numerals(ayat_number)
        
        full_arabic_text += (
            f"<span class='ayat-span' "
            f"data-ayat-number='{ayat_number}' "
            f"data-audio-src='{audio_src}'>"
            f"{ayat.get('teksArab')}" 
            f"</span>"
            f" <span class='murajaah-separator'>\u06dd{arabic_number}</span> "
        )

    return render_template('murajaah_detail.html', 
                           surah=surah_data, 
                           qari_name=qari_name,
                           full_arabic_text=full_arabic_text,
                           next_surah_id=next_surah_id,
                           current_qari=qari_key)

@app.route('/game')
def game_page():
    """Renders the Game menu page."""
    if not data_pipeline.check_connectivity():
         return render_template('game.html', is_offline=True)
    
    surah_list = data_pipeline.get_quran_surah_list()
    return render_template('game.html', 
                           is_offline=False,
                           surah_list=surah_list,
                           qari_list=QARI_LIST,
                           default_qari=DEFAULT_QARI)

@app.route('/game/ayat/play')
def game_ayat_play():
    """Renders the gameplay interface."""
    if not data_pipeline.check_connectivity():
        return render_template('game.html', is_offline=True)
    return render_template('game_play.html')

@app.route('/api/game/generate', methods=['POST'])
def generate_game_data():
    """Generates random questions for the Ayat Guesser game."""
    try:
        data = request.json
        mode = data.get('mode', 'surah') # 'surah' or 'juz'
        target_id = data.get('target') # surah_id or juz_id
        qari_id = data.get('qari')
        amount = int(data.get('amount', 5))

        surah_list = data_pipeline.get_quran_surah_list()
        questions = []

        for _ in range(amount):
            target_surah_info = None
            target_ayat_no = 0
            
            if mode == 'juz':
                juz_id = int(target_id)
                juz_ranges = JUZ_MAPPING.get(juz_id, [])
                if juz_id == 30:
                     rand_surah_id = random.randint(78, 114)
                     target_surah_info = next((s for s in surah_list if s['nomor'] == rand_surah_id), None)
                     target_ayat_no = random.randint(1, target_surah_info['jumlahAyat'])
                elif juz_ranges:
                    selected_range = random.choice(juz_ranges)
                    target_surah_id = selected_range['surah']
                    target_surah_info = next((s for s in surah_list if s['nomor'] == target_surah_id), None)
                    target_ayat_no = random.randint(selected_range['start'], selected_range['end'])
                else:
                    target_surah_info = random.choice(surah_list)
                    target_ayat_no = random.randint(1, target_surah_info['jumlahAyat'])

            else: # mode == 'surah'
                if target_id == 'all':
                    target_surah_info = random.choice(surah_list)
                    target_ayat_no = random.randint(1, target_surah_info['jumlahAyat'])
                else:
                    target_surah_info = next((s for s in surah_list if str(s['nomor']) == str(target_id)), None)
                    target_ayat_no = random.randint(1, target_surah_info['jumlahAyat'])

            if not target_surah_info: continue

            target_surah_no = target_surah_info['nomor']
            qari_slug = QARI_SLUGS.get(qari_id, "Misyari-Rasyid-Al-Afasi")
            surah_pad = f"{target_surah_no:03d}"
            ayat_pad = f"{target_ayat_no:03d}"
            audio_url = f"https://cdn.equran.id/audio-partial/{qari_slug}/{surah_pad}{ayat_pad}.mp3"

            correct_answer = f"{target_surah_info['namaLatin']} : {target_ayat_no}"
            options = [correct_answer]
            
            while len(options) < 4:
                if mode == 'juz':
                     if juz_id == 30:
                         wrong_surah_id = random.randint(78, 114)
                         wrong_surah = next((s for s in surah_list if s['nomor'] == wrong_surah_id), None)
                         wrong_ayat = random.randint(1, wrong_surah['jumlahAyat'])
                     else:
                         wrong_range = random.choice(juz_ranges)
                         wrong_surah_id = wrong_range['surah']
                         wrong_surah = next((s for s in surah_list if s['nomor'] == wrong_surah_id), None)
                         wrong_ayat = random.randint(wrong_range['start'], wrong_range['end'])
                     
                     wrong_option = f"{wrong_surah['namaLatin']} : {wrong_ayat}"

                elif mode == 'surah' and target_id != 'all':
                     wrong_ayat = random.randint(1, target_surah_info['jumlahAyat'])
                     while wrong_ayat == target_ayat_no:
                        wrong_ayat = random.randint(1, target_surah_info['jumlahAyat'])
                     wrong_option = f"{target_surah_info['namaLatin']} : {wrong_ayat}"
                else:
                     wrong_surah = random.choice(surah_list)
                     wrong_ayat = random.randint(1, wrong_surah['jumlahAyat'])
                     wrong_option = f"{wrong_surah['namaLatin']} : {wrong_ayat}"

                if wrong_option not in options:
                    options.append(wrong_option)
            
            random.shuffle(options)
            
            questions.append({
                "audio": audio_url,
                "correct": correct_answer,
                "options": options,
                "surah_name": target_surah_info['namaLatin'],
                "ayat_number": target_ayat_no
            })
            
        return jsonify(questions)

    except Exception as e:
        print(f"Game Generation Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/ask', methods=['POST'])
def ask_question():
    # RATE LIMIT CHECK
    topic = request.json.get('topic', '')
    ip = request.remote_addr
    is_allowed, used, requested = check_rate_limit(ip, topic)
    if not is_allowed:
        return jsonify({
            "status": "error", 
            "answer": f"Rate limit exceeded. You have used {used}/{DAILY_TOKEN_LIMIT} tokens. Request requires {requested}."
        }), 429

    initialize_crew() 
    if not topic:
        return jsonify({"error": "'topic' is required."}), 400

    small_talk_response = handle_small_talk(topic)
    if small_talk_response:
        return jsonify(small_talk_response)
    
    if not crew:
        return jsonify({"status": "error", "answer": "Crew not initialized."}), 500
        
    try:
        result = crew.kickoff(inputs={'topic': topic})
        raw_output = result.raw
        cleaned_output = raw_output.strip().replace('```json', '').replace('```', '').strip()
        answer_dict = json.loads(cleaned_output)
        return jsonify(answer_dict)
    except Exception as e:
        return jsonify({"status": "error", "answer": f"An unexpected error occurred: {e}"}), 500

@app.route('/ingest')
def ingest():
    try:
        quran_chunks, hadith_chunks = data_pipeline.load_and_chunk_data()
        vector_store.ingest_data_to_milvus(config.QURAN_COLLECTION, quran_chunks)
        vector_store.ingest_data_to_milvus(config.HADITH_COLLECTION, hadith_chunks)
        return "Data ingestion complete!", 200
    except Exception as e:
        return f"An error occurred during ingestion: {e}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)