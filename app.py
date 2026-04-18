import os
import time
from datetime import datetime

import streamlit as st
import yaml
from dotenv import load_dotenv

from src.data.finnhub_collector import FinnhubCollector
from src.data.marketaux_collector import MarketAuxCollector
from src.data.models import MarketSnapshot
from src.script.generator import ScriptGenerator
from src.audio.kokoro_engine import KokoroEngine
from src.audio.processor import AudioProcessor

# ── Page config ──────────────────────────────────────────────
st.set_page_config(page_title="Market Pulse", page_icon="🎙️", layout="wide")


@st.cache_data
def load_config():
    load_dotenv()
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    config["finnhub_api_key"] = os.getenv("FINNHUB_API_KEY", "")
    config["marketaux_api_key"] = os.getenv("MARKETAUX_API_KEY", "")
    config["gemini_api_key"] = os.getenv("GEMINI_API_KEY", "")
    return config


# ── Session state ────────────────────────────────────────────
for key, val in [
    ("snapshot", None), ("script", None), ("mp3_path", None),
    ("stage_times", {}), ("has_run", False),
]:
    if key not in st.session_state:
        st.session_state[key] = val


# ── Header ───────────────────────────────────────────────────
st.title("Market Pulse")
st.caption("Automated Finance Podcast Generator")

config = load_config()
date = datetime.now().strftime("%Y-%m-%d")

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.header("Configuration")
    keys_ok = True
    for name, env_var, placeholder in [
        ("Finnhub", "finnhub_api_key", "your_finnhub_key_here"),
        ("MarketAux", "marketaux_api_key", "your_marketaux_key_here"),
        ("Gemini", "gemini_api_key", "your_gemini_key_here"),
    ]:
        val = config.get(env_var, "")
        if val and val != placeholder:
            st.success(f"{name} API key loaded", icon="✓")
        else:
            st.error(f"{name} API key missing", icon="✗")
            keys_ok = False

    st.divider()
    st.subheader("Podcast Settings")
    st.text(f"Name: {config.get('podcast_name', 'Market Pulse')}")
    st.text(f"Voice S1: {config.get('speaker_1_voice', 'am_adam')}")
    st.text(f"Voice S2: {config.get('speaker_2_voice', 'af_bella')}")
    st.text(f"LLM: {config.get('gemini_model', 'gemini-2.5-flash')}")
    st.text(f"Date: {date}")

    st.divider()
    if st.button("Reset", use_container_width=True):
        for k in ["snapshot", "script", "mp3_path", "stage_times", "has_run"]:
            st.session_state[k] = None if k != "stage_times" else {}
        st.session_state.has_run = False
        st.rerun()

# ── Generate button ──────────────────────────────────────────
st.divider()
run_pipeline = st.button(
    "Generate Podcast",
    type="primary",
    use_container_width=True,
    disabled=(not keys_ok) or st.session_state.has_run,
)

if run_pipeline:
    output_dir = config.get("output_dir", "output")
    os.makedirs(output_dir, exist_ok=True)

    # ── STAGE 1: Data Collection ─────────────────────────────
    with st.status("**Stage 1/3 -- Collecting market data...**", expanded=True) as status:
        t0 = time.time()

        st.write("Connecting to Finnhub API...")
        finnhub = FinnhubCollector(api_key=config["finnhub_api_key"])
        finnhub_data = finnhub.collect_all()
        st.write("Finnhub data received: indices, crypto, forex, commodities, earnings")

        st.write("Connecting to MarketAux API...")
        marketaux = MarketAuxCollector(api_key=config["marketaux_api_key"])
        marketaux_data = marketaux.collect_all()
        st.write(f"MarketAux data received: {len(marketaux_data.get('news', []))} articles")

        snapshot = MarketSnapshot(
            date=date,
            indices=finnhub_data.get("indices", {}),
            top_gainers=finnhub_data.get("top_gainers", []),
            top_losers=finnhub_data.get("top_losers", []),
            earnings=finnhub_data.get("earnings", []),
            economic_events=finnhub_data.get("economic_events", []),
            crypto=finnhub_data.get("crypto", {}),
            forex=finnhub_data.get("forex", {}),
            commodities=finnhub_data.get("commodities", {}),
            news=marketaux_data.get("news", []),
            market_sentiment=marketaux_data.get("market_sentiment", "neutral"),
        )
        snapshot.save(os.path.join(output_dir, f"{date}-snapshot.json"))
        st.session_state.snapshot = snapshot

        elapsed = time.time() - t0
        st.session_state.stage_times["data"] = elapsed
        status.update(label=f"**Stage 1/3 -- Data collected** ({elapsed:.1f}s)", state="complete", expanded=False)

    # ── STAGE 2: Script Generation ───────────────────────────
    with st.status("**Stage 2/3 -- Generating podcast script...**", expanded=True) as status:
        t0 = time.time()

        st.write(f"Sending market snapshot to Gemini ({config.get('gemini_model', 'gemini-2.5-flash')})...")
        generator = ScriptGenerator(
            api_key=config["gemini_api_key"],
            model=config.get("gemini_model", "gemini-2.5-flash"),
        )
        script = generator.generate(snapshot)

        word_count = len(script.split())
        st.write(f"Script generated: {word_count} words (~{word_count // 150} min episode)")

        script_path = os.path.join(output_dir, f"{date}-script.txt")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)
        st.session_state.script = script

        elapsed = time.time() - t0
        st.session_state.stage_times["script"] = elapsed
        status.update(label=f"**Stage 2/3 -- Script generated** ({elapsed:.1f}s, {word_count} words)", state="complete", expanded=False)

    # ── STAGE 3: Audio Generation ────────────────────────────
    with st.status("**Stage 3/3 -- Generating audio...**", expanded=True) as status:
        t0 = time.time()

        st.write("Loading Kokoro-82M TTS model...")
        engine = KokoroEngine(
            voice_s1=config.get("speaker_1_voice", "am_adam"),
            voice_s2=config.get("speaker_2_voice", "af_bella"),
        )

        progress_bar = st.progress(0, text="Starting synthesis...")
        segment_log = st.empty()

        def on_progress(i, total, speaker, preview):
            pct = (i + 1) / total
            voice_name = "Alex" if speaker == "S1" else "Sam"
            progress_bar.progress(pct, text=f"Segment {i+1}/{total} ({voice_name})")
            segment_log.caption(f'"{preview}..."')

        audio, sample_rate = engine.generate_audio(
            script,
            sample_rate=config.get("sample_rate", 24000),
            on_progress=on_progress,
        )
        progress_bar.progress(1.0, text="Synthesis complete!")

        st.write("Encoding MP3...")
        processor = AudioProcessor(output_dir=output_dir)
        mp3_path = processor.save_mp3(
            audio=audio,
            sample_rate=sample_rate,
            date=date,
            podcast_name=config.get("podcast_name", "Market Pulse"),
        )
        st.session_state.mp3_path = mp3_path

        duration = len(audio) / sample_rate
        elapsed = time.time() - t0
        st.session_state.stage_times["audio"] = elapsed
        status.update(label=f"**Stage 3/3 -- Audio generated** ({elapsed:.1f}s, {duration/60:.1f} min episode)", state="complete", expanded=False)

    st.session_state.has_run = True
    st.balloons()
    st.rerun()

# ── Results (shown after pipeline or from session state) ─────
if st.session_state.has_run:
    st.success("Pipeline complete!")

    tab_audio, tab_data, tab_script = st.tabs(["Audio Player", "Market Data", "Podcast Script"])

    # ── Audio tab ────────────────────────────────────────────
    with tab_audio:
        mp3_path = st.session_state.mp3_path
        if mp3_path and os.path.exists(mp3_path):
            file_size = os.path.getsize(mp3_path) / (1024 * 1024)
            st.markdown(f"**{os.path.basename(mp3_path)}** ({file_size:.1f} MB)")
            st.audio(mp3_path, format="audio/mp3")

            with open(mp3_path, "rb") as f:
                st.download_button("Download MP3", data=f, file_name=os.path.basename(mp3_path),
                                   mime="audio/mpeg", use_container_width=True)

            st.divider()
            st.subheader("Pipeline Timing")
            times = st.session_state.stage_times
            total = sum(times.values())
            labels = {"data": "Data Collection", "script": "Script Generation", "audio": "Audio Generation"}
            for key, elapsed in times.items():
                pct = elapsed / total
                st.progress(pct, text=f"{labels.get(key, key)}: {elapsed:.1f}s ({pct*100:.0f}%)")
            st.metric("Total Time", f"{total/60:.1f} min")

    # ── Market Data tab ──────────────────────────────────────
    with tab_data:
        snapshot = st.session_state.snapshot
        if snapshot:
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Market Indices")
                for name, data in snapshot.indices.items():
                    cp = data.get("change_percent", 0)
                    arrow = "▲" if cp >= 0 else "▼"
                    color = "green" if cp >= 0 else "red"
                    st.markdown(f"**{name}**: {data.get('current', 0):,.2f} "
                                f"<span style='color:{color}'>{arrow} {cp:+.2f}%</span>",
                                unsafe_allow_html=True)

                st.subheader("Crypto")
                for name, data in snapshot.crypto.items():
                    cp = data.get("change_percent", 0)
                    arrow = "▲" if cp >= 0 else "▼"
                    color = "green" if cp >= 0 else "red"
                    st.markdown(f"**{name}**: ${data.get('price', 0):,.2f} "
                                f"<span style='color:{color}'>{arrow} {cp:+.2f}%</span>",
                                unsafe_allow_html=True)

                st.subheader("Forex")
                for name, data in snapshot.forex.items():
                    cp = data.get("change_percent", 0)
                    arrow = "▲" if cp >= 0 else "▼"
                    color = "green" if cp >= 0 else "red"
                    st.markdown(f"**{name}**: {data.get('rate', 0):.4f} "
                                f"<span style='color:{color}'>{arrow} {cp:+.2f}%</span>",
                                unsafe_allow_html=True)

                st.subheader("Commodities")
                for name, data in snapshot.commodities.items():
                    cp = data.get("change_percent", 0)
                    arrow = "▲" if cp >= 0 else "▼"
                    color = "green" if cp >= 0 else "red"
                    st.markdown(f"**{name}**: ${data.get('price', 0):,.2f} "
                                f"<span style='color:{color}'>{arrow} {cp:+.2f}%</span>",
                                unsafe_allow_html=True)

            with col2:
                st.subheader(f"Sentiment: {snapshot.market_sentiment.upper()}")

                if snapshot.top_gainers:
                    st.subheader("Top Gainers")
                    for m in snapshot.top_gainers[:5]:
                        st.markdown(f"**{m.symbol}**: ${m.price:.2f} "
                                    f"<span style='color:green'>▲ {m.change_percent:+.2f}%</span>",
                                    unsafe_allow_html=True)

                if snapshot.top_losers:
                    st.subheader("Top Losers")
                    for m in snapshot.top_losers[:5]:
                        st.markdown(f"**{m.symbol}**: ${m.price:.2f} "
                                    f"<span style='color:red'>▼ {m.change_percent:+.2f}%</span>",
                                    unsafe_allow_html=True)

                if snapshot.news:
                    st.subheader(f"News ({len(snapshot.news)} articles)")
                    for n in snapshot.news[:8]:
                        sc = "green" if n.sentiment > 0.1 else ("red" if n.sentiment < -0.1 else "gray")
                        st.markdown(f"- **{n.title}** ({n.source}) "
                                    f"<span style='color:{sc}'>{n.sentiment:+.2f}</span>",
                                    unsafe_allow_html=True)

                if snapshot.earnings:
                    st.subheader("Earnings")
                    for e in snapshot.earnings[:5]:
                        beat = ""
                        if e.surprise_percent is not None:
                            beat = f" ({'beat' if e.surprise_percent > 0 else 'miss'}: {e.surprise_percent:+.1f}%)"
                        st.markdown(f"- **{e.symbol}**: EPS ${e.eps_actual or 'N/A'} vs ${e.eps_estimate or 'N/A'}{beat}")

    # ── Script tab ───────────────────────────────────────────
    with tab_script:
        script = st.session_state.script
        if script:
            word_count = len(script.split())
            st.metric("Word Count", f"{word_count:,}", delta=f"~{word_count // 150} min")
            st.divider()
            for line in script.split("\n"):
                line = line.strip()
                if not line:
                    continue
                if line.startswith("[S1]"):
                    text = line.replace("[S1]", "").strip()
                    st.markdown(f'<div style="margin:6px 0; padding:8px 12px; border-left:3px solid #4A90D9; '
                                f'background:rgba(74,144,217,0.08);"><strong style="color:#4A90D9;">Alex:</strong> {text}</div>',
                                unsafe_allow_html=True)
                elif line.startswith("[S2]"):
                    text = line.replace("[S2]", "").strip()
                    st.markdown(f'<div style="margin:6px 0; padding:8px 12px; border-left:3px solid #D94A8A; '
                                f'background:rgba(217,74,138,0.08);"><strong style="color:#D94A8A;">Sam:</strong> {text}</div>',
                                unsafe_allow_html=True)
