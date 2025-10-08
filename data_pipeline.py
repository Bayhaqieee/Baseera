import os
from langchain_community.document_loaders import CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import kaggle
import pandas as pd
import re
import requests
import socket

# --- Internet Connectivity Check ---
IS_ONLINE = None

def check_connectivity():
    """Checks for a stable internet connection and caches the result."""
    global IS_ONLINE
    if IS_ONLINE is not None:
        return IS_ONLINE
    
    try:
        # Try to connect to the API host and a reliable DNS
        socket.create_connection(("equran.id", 443), timeout=3)
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        print("--- Internet connection detected. Using ONLINE API. ---")
        IS_ONLINE = True
    except (socket.timeout, OSError):
        print("--- No internet connection. Using OFFLINE local files. ---")
        IS_ONLINE = False
    return IS_ONLINE

# --- Slugify Helper ---
def slugify(s):
    """Simple function to create a URL-friendly slug from a string."""
    s = s.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_-]+', '-', s)
    s = re.sub(r'^-+|-+$', '', s)
    return s

# --- Dataset Download ---
def check_kaggle_api():
    kaggle_dir = os.path.expanduser('~/.kaggle')
    api_key_path = os.path.join(kaggle_dir, 'kaggle.json')
    if not os.path.exists(api_key_path):
        raise FileNotFoundError(f"Kaggle API key not found. Please place 'kaggle.json' in '{kaggle_dir}'.")

def download_and_extract_datasets():
    datasets_dir = 'datasets'
    os.makedirs(datasets_dir, exist_ok=True)
    hadith_path = os.path.join(datasets_dir, 'all_hadiths_clean.csv')
    quran_path = os.path.join(datasets_dir, 'main_df.csv')
    quran_meta_path = os.path.join(datasets_dir, 'quran.csv')

    if not os.path.exists(hadith_path):
        print("Downloading Hadith dataset...")
        kaggle.api.dataset_download_files('fahd09/hadith-dataset', path=datasets_dir, unzip=True)
    if not os.path.exists(quran_path) or not os.path.exists(quran_meta_path):
        print("Downloading Quran dataset...")
        kaggle.api.dataset_download_files('alizahidraja/quran-nlp', path=datasets_dir, unzip=True)
        if os.path.exists(os.path.join(datasets_dir, 'data', 'main_df.csv')):
            os.rename(os.path.join(datasets_dir, 'data', 'main_df.csv'), quran_path)
        if os.path.exists(os.path.join(datasets_dir, 'data', 'quran', 'quran.csv')):
            os.rename(os.path.join(datasets_dir, 'data', 'quran', 'quran.csv'), quran_meta_path)

# --- AI Ingestion ---
def load_and_chunk_data():
    print("--- Loading and Processing Data for AI ---")
    check_kaggle_api()
    download_and_extract_datasets()
    quran_loader = CSVLoader(file_path='datasets/main_df.csv', encoding='utf-8')
    hadith_loader = CSVLoader(file_path='datasets/all_hadiths_clean.csv', encoding='utf-8')
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    quran_chunks = text_splitter.split_documents(quran_loader.load())
    hadith_chunks = text_splitter.split_documents(hadith_loader.load())
    return quran_chunks, hadith_chunks

# --- QURAN DATA LOGIC ---

def get_quran_surah_list():
    """Fetches the list of all Surahs, from API or local files."""
    if check_connectivity():
        try:
            response = requests.get("https://equran.id/api/v2/surat", timeout=5)
            response.raise_for_status()
            return response.json().get('data', [])
        except requests.RequestException as e:
            print(f"API Error (surah list): {e}. Falling back to offline data.")
            return get_quran_surah_list_offline()
    else:
        return get_quran_surah_list_offline()

def get_quran_surah_detail(surah_id):
    """Fetches the detail of a specific Surah, from API or local files."""
    if check_connectivity():
        try:
            response = requests.get(f"https://equran.id/api/v2/surat/{surah_id}", timeout=5)
            response.raise_for_status()
            data = response.json().get('data', None)
            if data:
                # API returns 'suratSelanjutnya' and 'suratSebelumnya' which we can map
                next_surah = data.get('suratSelanjutnya')
                prev_surah = data.get('suratSebelumnya')

                # Ensure consistent format or None
                if next_surah is False: next_surah = None
                if prev_surah is False: prev_surah = None
                
                # Standardize naming for template
                data['next_surah'] = next_surah
                data['prev_surah'] = prev_surah

            return data
        except requests.RequestException as e:
            print(f"API Error (surah {surah_id}): {e}. Falling back to offline data.")
            return get_quran_surah_detail_offline(surah_id)
    else:
        return get_quran_surah_detail_offline(surah_id)

def get_quran_surah_list_offline():
    """Builds a Surah list from local CSV files."""
    try:
        df_main = pd.read_csv('datasets/main_df.csv')
        df_meta = pd.read_csv('datasets/quran.csv')

        # Add PlaceOfRevelation to the offline data pull
        surah_names = df_main[['Surah', 'EnglishTitle', 'PlaceOfRevelation']].drop_duplicates().set_index('Surah')
        surah_meta = df_meta[['surah_no', 'surah_name', 'total_ayah_surah']].drop_duplicates().set_index('surah_no')
        
        merged = surah_names.join(surah_meta)
        
        surah_list = []
        for surah_num, row in merged.iterrows():
            surah_list.append({
                "nomor": surah_num,
                "nama": row['surah_name'],
                "namaLatin": row['EnglishTitle'],
                "jumlahAyat": row['total_ayah_surah'],
                "tempatTurun": row['PlaceOfRevelation'] # Map offline column to API key
            })
        return surah_list
    except FileNotFoundError as e:
        print(f"Offline Error (surah list): {e}")
        return []

def get_quran_surah_detail_offline(surah_id):
    """Builds a Surah detail object from local CSV files."""
    try:
        df_main = pd.read_csv('datasets/main_df.csv')
        df_meta = pd.read_csv('datasets/quran.csv')

        surah_main = df_main[df_main['Surah'] == surah_id]
        surah_meta = df_meta[df_meta['surah_no'] == surah_id]
        
        if surah_main.empty or surah_meta.empty:
            return None

        # Get base info
        info = surah_main.iloc[0]
        meta_info = surah_meta.iloc[0]
        
        # Determine Next/Prev
        next_surah = None
        prev_surah = None
        
        if surah_id < 114:
            next_id = surah_id + 1
            next_info = df_main[df_main['Surah'] == next_id].iloc[0]
            next_surah = {"nomor": next_id, "namaLatin": next_info['EnglishTitle']}
            
        if surah_id > 1:
            prev_id = surah_id - 1
            prev_info = df_main[df_main['Surah'] == prev_id].iloc[0]
            prev_surah = {"nomor": prev_id, "namaLatin": prev_info['EnglishTitle']}

        surah_data = {
            "nomor": surah_id,
            "nama": meta_info['surah_name'],
            "namaLatin": info['EnglishTitle'],
            "jumlahAyat": meta_info['total_ayah_surah'],
            "tempatTurun": info['PlaceOfRevelation'], # Map offline column to API key
            "arti": None, # Not in our offline data
            "deskripsi": "Deskripsi tidak tersedia dalam mode offline.",
            "audioFull": {}, # Not in our offline data
            "ayat": [],
            "next_surah": next_surah,
            "prev_surah": prev_surah
        }
        
        # Build ayat list
        for _, row in surah_main.iterrows():
            surah_data['ayat'].append({
                "nomorAyat": row['Ayat'],
                "teksArab": row['Arabic'],
                "teksLatin": "Teks latin tidak tersedia dalam mode offline.",
                "teksIndonesia": row['Translation - Arthur J'],
                "audio": {}
            })
        
        return surah_data
    except FileNotFoundError as e:
        print(f"Offline Error (surah detail): {e}")
        return None

# --- HADITH DATA LOGIC ---

def load_hadith_for_dictionary():
    """Loads and prepares the Hadith dataset as a DataFrame for efficient querying."""
    try:
        df = pd.read_csv('datasets/all_hadiths_clean.csv')
        hadith_data = df[['source', 'chapter_no', 'hadith_no', 'chapter', 'text_ar', 'text_en']].rename(columns={
            'chapter_no': 'chapter_number', 'hadith_no': 'hadith_number', 'text_ar': 'arabic_text', 'text_en': 'english_text'
        }).fillna('Not Available')
        
        hadith_data['source_slug'] = hadith_data['source'].apply(slugify)
        hadith_data['chapter_slug'] = hadith_data['chapter'].apply(slugify)
        
        return hadith_data
    except FileNotFoundError:
        return pd.DataFrame() 

def get_hadith_sources(df):
    """Returns a list of unique hadith sources with their slugs."""
    if df.empty:
        return []
    sources = df[['source', 'source_slug']].drop_duplicates().sort_values('source')
    return sources.to_dict('records')

def get_chapters_for_source(df, source_slug):
    """Returns a list of chapters for a given source_slug."""
    if df.empty:
        return [], "Unknown"
    
    source_df = df[df['source_slug'] == source_slug]
    if source_df.empty:
        return [], "Unknown"
        
    source_name = source_df.iloc[0]['source']
    chapters = source_df[['chapter', 'chapter_slug', 'chapter_number']].drop_duplicates().sort_values('chapter_number')
    
    return chapters.to_dict('records'), source_name

def get_hadiths_for_chapter(df, source_slug, chapter_slug):
    """Returns all hadiths for a given source and chapter slug."""
    if df.empty:
        return [], "Unknown", "Unknown"
        
    hadiths_df = df[(df['source_slug'] == source_slug) & (df['chapter_slug'] == chapter_slug)]
    if hadiths_df.empty:
        return [], "Unknown", "Unknown"
        
    source_name = hadiths_df.iloc[0]['source']
    chapter_name = hadiths_df.iloc[0]['chapter']
    hadiths = hadiths_df.to_dict('records')
    
    return hadiths, source_name, chapter_name