import streamlit as st
import requests
import pandas as pd

# 🔧 Official channels list (expandable)
OFFICIAL_CHANNEL_KEYWORDS = [
    "T-Series", "Sony Music India", "Zee Music Company", "Tips Official", "YRF", "Speed Records",
    "EMI Music", "Universal Music India", "Universal Music Group", "Warner Music India", "Warner Music Group",
    "Vevo", "Atlantic Records", "Saregama Music", "BBC Music", "MTV India", "MTV UK", "SME", "BigHit Labels",
    "HYBE LABELS", "B4U Music", "Aditya Music", "Ultra Music", "Eros Now Music", "Mass Appeal", "Rolling Stone",
    "Sony Music South", "Sony Music Tamil", "Think Music India", "Lahari Music", "TeluguOne Music", "Manorama Music",
    "Shemaroo Filmi Gaane", "T-Series Apna Punjab", "Pagalworld", "Hungama Music", "Gaana Originals", "Wynk Music",
    "Kpop", "JYP Entertainment", "YG Entertainment", "SMTOWN", "Roc Nation", "Republic Records",
    "Interscope Records", "Capitol Records", "Columbia Records", "Epic Records", "Island Records",
    "NCS", "NoCopyrightSounds", "Trap Nation", "Chill Nation", "House Nation"
]

# 🔍 YouTube search endpoint (no API key version using `ytsearch` and `yt-dlp`)
def search_youtube(query, max_results=50):
    from yt_dlp import YoutubeDL
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True,
        'dump_single_json': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
    return result.get('entries', [])

# 🔍 Check if upload is official
def is_official(channel_name):
    return any(kw.lower() in channel_name.lower() for kw in OFFICIAL_CHANNEL_KEYWORDS)

# 🎵 Playlist state
if "playlist" not in st.session_state:
    st.session_state.playlist = []
if "current_page" not in st.session_state:
    st.session_state.current_page = 1

# 🌟 Layout
st.set_page_config(page_title="YouTube Music Recommender", layout="wide")
st.title("🎶 YouTube Music Recommender")

# 🔀 Tabs for discovery vs playlist
tab1, tab2 = st.tabs(["🔎 Discover Songs", "📂 My Playlist"])

# --- DISCOVER TAB ---
with tab1:
    st.subheader("Search for Songs")

    with st.form("search_form"):
        singer = st.text_input("Singer Name", placeholder="e.g., Arijit Singh")
        genre = st.selectbox("Genre/Mood", ["", "Romantic", "Pop", "Rock", "Classical", "Hip Hop", "Jazz", "Chill", "Party", "Sad", "Energetic"])
        year = st.selectbox("Year / Era", ["", "1980s", "1990s", "2000s", "2010s", "2020s"])
        language = st.selectbox("Language", ["", "Hindi", "English", "Punjabi", "Tamil", "Telugu", "Spanish"])
        max_results = st.slider("Total results to fetch", 10, 100, 50, step=10)
        official_only = st.toggle("Show only official uploads", value=True)
        per_page = st.selectbox("Results per page", [10, 20, 30], index=0)
        submitted = st.form_submit_button("Search")

    if submitted:
        query_parts = [singer, genre, year, language]
        query = " ".join([q for q in query_parts if q])
        with st.spinner("Fetching results..."):
            raw_results = search_youtube(query, max_results)

            filtered = []
            for vid in raw_results:
                if 'duration' not in vid or not vid.get('url'):
                    continue
                duration_sec = vid['duration']
                if not (60 <= duration_sec <= 420):
                    continue
                if official_only and not is_official(vid.get("channel", "")):
                    continue
                filtered.append({
                    'title': vid['title'],
                    'channel': vid['channel'],
                    'video_url': f"https://www.youtube.com/watch?v={vid['id']}",
                    'views': vid.get("view_count", 0),
                    'duration': duration_sec,
                })

            st.session_state.results = filtered
            st.session_state.query = query
            st.session_state.current_page = 1  # reset to first page
            st.success(f"Found {len(filtered)} results")

    if "results" in st.session_state:
        results = st.session_state.results
        total_pages = (len(results) - 1) // per_page + 1

        st.write("### Pages")
        page_count = max(1, min(total_pages, 10))
        page_buttons = st.columns([1] * page_count)

        for i in range(page_count):
            if page_buttons[i].button(str(i + 1)):
                st.session_state.current_page = i + 1

        start = (st.session_state.current_page - 1) * per_page
        end = start + per_page
        paginated = results[start:end]

        for idx, video in enumerate(paginated, start=1):
            col1, col2 = st.columns([2, 6])
            with col1:
                st.video(video['video_url'])
            with col2:
                st.markdown(f"**{video['title']}**")
                duration_minutes = int(video['duration']) // 60
                duration_seconds = int(video['duration']) % 60
                st.markdown(f"👤 **{video['channel']}**  \n📺 {video['views']:,} views  \n⏱ {duration_minutes}:{duration_seconds:02d} min")
                if st.button(f"➕ Add to Playlist", key=f"add_{idx}_{video['video_url']}"):
                    if video['title'] in [s['title'] for s in st.session_state.playlist]:
                        st.warning(f"'{video['title']}' is already in your playlist.")
                    else:
                        st.session_state.playlist.append(video)
                        st.success(f"Added: {video['title']}")

# --- PLAYLIST TAB ---
with tab2:
    st.subheader("📂 Your Playlist")

    if st.session_state.playlist:
        for i, song in enumerate(st.session_state.playlist):
            col1, col2 = st.columns([2, 6])
            with col1:
                st.video(song['video_url'])
            with col2:
                st.markdown(f"**{song['title']}**")
                duration_minutes = int(song['duration']) // 60
                duration_seconds = int(song['duration']) % 60
                st.markdown(f"👤 **{song['channel']}**  \n📺 {song['views']:,} views  \n⏱ {duration_minutes}:{duration_seconds:02d} min")
                if st.button(f"❌ Remove", key=f"remove_{i}"):
                    st.session_state.playlist.pop(i)
                    st.rerun()

        if st.button("💾 Save Playlist as Text File"):
            urls = [s['video_url'] for s in st.session_state.playlist]
            with open("playlist.txt", "w") as f:
                f.write("\n".join(urls))
            st.success("✅ Playlist saved as `playlist.txt`")
    else:
        st.info("Your playlist is empty.")