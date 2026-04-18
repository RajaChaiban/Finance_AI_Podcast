import os
import time
from datetime import datetime

import streamlit as st
import yaml
from dotenv import load_dotenv

from src.data.categories import (
    PodcastCategory, CATEGORY_LABELS, CATEGORY_DESCRIPTIONS,
    CATEGORY_API_KEYS, API_KEY_LABELS, DEFAULT_CATEGORIES,
)
from src.data.collector_router import CategoryCollectorRouter
from src.data.models import MarketSnapshot
from src.script.generator import ScriptGenerator
from src.audio.kokoro_engine import KokoroEngine
from src.audio.processor import AudioProcessor
from src.utils.email_sender import send_episode_email

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
    config["fred_api_key"] = os.getenv("FRED_API_KEY", "")
    config["gnews_api_key"] = os.getenv("GNEWS_API_KEY", "")
    config["currents_api_key"] = os.getenv("CURRENTS_API_KEY", "")
    config["newsdata_api_key"] = os.getenv("NEWSDATA_API_KEY", "")
    config["email_address"] = os.getenv("EMAIL_ADDRESS", "")
    config["email_app_password"] = os.getenv("EMAIL_APP_PASSWORD", "")
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
st.caption("Automated Multi-Category Podcast Generator")

config = load_config()
date = datetime.now().strftime("%Y-%m-%d")

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.header("Podcast Categories")

    selected_values = st.multiselect(
        "Select topics to cover",
        options=[c.value for c in PodcastCategory],
        default=[c.value for c in DEFAULT_CATEGORIES],
        format_func=lambda x: CATEGORY_LABELS[PodcastCategory(x)],
    )
    selected_categories = [PodcastCategory(v) for v in selected_values]

    for cat in selected_categories:
        st.caption(f"{CATEGORY_LABELS[cat]}: {CATEGORY_DESCRIPTIONS[cat]}")

    st.divider()
    st.header("API Keys")

    # Determine which keys are needed
    required_keys = set()
    required_keys.add("gemini_api_key")  # Always needed for script generation
    for cat in selected_categories:
        for key_name in CATEGORY_API_KEYS.get(cat, []):
            required_keys.add(key_name)

    keys_ok = True
    for key_name in sorted(required_keys):
        label = API_KEY_LABELS.get(key_name, key_name)
        val = config.get(key_name, "")
        placeholder = f"your_{key_name.replace('_api_key', '')}_key_here"
        if val and val != placeholder:
            st.success(f"{label} API key loaded", icon="✓")
        else:
            st.error(f"{label} API key missing", icon="✗")
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

if not selected_categories:
    st.warning("Select at least one category to generate a podcast.")

run_pipeline = st.button(
    "Generate Podcast",
    type="primary",
    use_container_width=True,
    disabled=(not keys_ok) or st.session_state.has_run or (not selected_categories),
)

if run_pipeline:
    output_dir = config.get("output_dir", "output")
    os.makedirs(output_dir, exist_ok=True)

    cat_names = ", ".join(CATEGORY_LABELS[c] for c in selected_categories)

    # ── STAGE 1: Data Collection ─────────────────────────────
    with st.status(f"**Stage 1/3 -- Collecting data for: {cat_names}...**", expanded=True) as status:
        t0 = time.time()

        router = CategoryCollectorRouter(config, selected_categories)

        def on_status(msg):
            st.write(msg)

        snapshot = router.collect_all(status_callback=on_status)
        snapshot.save(os.path.join(output_dir, f"{date}-snapshot.json"))
        st.session_state.snapshot = snapshot

        elapsed = time.time() - t0
        st.session_state.stage_times["data"] = elapsed
        status.update(label=f"**Stage 1/3 -- Data collected** ({elapsed:.1f}s)", state="complete", expanded=False)

    # ── STAGE 2: Script Generation ───────────────────────────
    with st.status("**Stage 2/3 -- Generating podcast script...**", expanded=True) as status:
        t0 = time.time()

        st.write(f"Sending data to Gemini ({config.get('gemini_model', 'gemini-2.5-flash')})...")
        generator = ScriptGenerator(
            api_key=config["gemini_api_key"],
            model=config.get("gemini_model", "gemini-2.5-flash"),
        )
        script = generator.generate(snapshot, selected_categories)

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

            # ── Email delivery ───────────────────────────────
            st.divider()
            st.subheader("Send via Email")
            email_configured = (config.get("email_address", "") and
                                config.get("email_app_password", ""))

            if not email_configured:
                st.caption("Set EMAIL_ADDRESS and EMAIL_APP_PASSWORD in .env to enable.")

            email_col1, email_col2 = st.columns([3, 1])
            with email_col1:
                recipient = st.text_input("Recipient email", placeholder="recipient@example.com",
                                          disabled=not email_configured)
            with email_col2:
                st.markdown("<br>", unsafe_allow_html=True)
                send_clicked = st.button("Send", type="primary", use_container_width=True,
                                         disabled=not email_configured or not recipient)

            if send_clicked and recipient:
                with st.spinner("Sending email..."):
                    snapshot = st.session_state.snapshot
                    cat_names = snapshot.categories if snapshot else []
                    cat_labels = [c.replace("_", " ").title() for c in cat_names]
                    sent = send_episode_email(
                        mp3_path=mp3_path,
                        recipient=recipient,
                        categories=cat_labels,
                        sender_email=config.get("email_address"),
                        sender_password=config.get("email_app_password"),
                    )
                if sent:
                    st.success(f"Episode sent to {recipient}!")
                else:
                    st.error("Failed to send. Check EMAIL_ADDRESS and EMAIL_APP_PASSWORD in .env.")

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
            active_cats = [PodcastCategory(c) for c in snapshot.categories] if snapshot.categories else DEFAULT_CATEGORIES
            col1, col2 = st.columns(2)

            with col1:
                # ── Finance Macro sections ───────────────────
                if PodcastCategory.FINANCE_MACRO in active_cats:
                    if snapshot.indices:
                        st.subheader("Market Indices")
                        for name, data in snapshot.indices.items():
                            cp = data.get("change_percent", 0)
                            arrow = "▲" if cp >= 0 else "▼"
                            color = "green" if cp >= 0 else "red"
                            st.markdown(f"**{name}**: {data.get('current', 0):,.2f} "
                                        f"<span style='color:{color}'>{arrow} {cp:+.2f}%</span>",
                                        unsafe_allow_html=True)

                    if snapshot.fear_greed:
                        fg = snapshot.fear_greed
                        score = fg.get("score", 0)
                        label = fg.get("label", "")
                        fg_color = "green" if score >= 60 else ("red" if score <= 40 else "orange")
                        st.markdown(f"**Fear & Greed Index**: <span style='color:{fg_color};font-size:1.3em'>"
                                    f"{score:.0f} ({label})</span>", unsafe_allow_html=True)

                    if snapshot.macro_signals:
                        ms = snapshot.macro_signals
                        verdict = ms.get("verdict", "")
                        v_color = "green" if verdict == "BUY" else ("red" if verdict == "SELL" else "orange")
                        st.markdown(f"**Macro Signal**: <span style='color:{v_color};font-weight:bold'>"
                                    f"{verdict}</span> ({ms.get('bullish_count', 0)}/{ms.get('total_count', 0)} bullish)",
                                    unsafe_allow_html=True)

                    if snapshot.commodities:
                        st.subheader("Commodities")
                        for name, data in snapshot.commodities.items():
                            cp = data.get("change_percent", 0)
                            arrow = "▲" if cp >= 0 else "▼"
                            color = "green" if cp >= 0 else "red"
                            st.markdown(f"**{name}**: ${data.get('price', 0):,.2f} "
                                        f"<span style='color:{color}'>{arrow} {cp:+.2f}%</span>",
                                        unsafe_allow_html=True)

                    if snapshot.sectors:
                        st.subheader("Sector Performance")
                        for s in snapshot.sectors[:8]:
                            cp = s.get("change", 0)
                            arrow = "▲" if cp >= 0 else "▼"
                            color = "green" if cp >= 0 else "red"
                            st.markdown(f"**{s.get('name', s.get('symbol', ''))}**: "
                                        f"<span style='color:{color}'>{arrow} {cp:+.2f}%</span>",
                                        unsafe_allow_html=True)

                    if snapshot.etf_flows:
                        summary = snapshot.etf_flows.get("summary", {})
                        if summary:
                            direction = summary.get("netDirection", "")
                            d_color = "green" if "INFLOW" in direction else "red"
                            total_flow = summary.get("totalEstFlow", 0) / 1e6
                            st.subheader("ETF Flows")
                            st.markdown(f"**{direction}**: ${total_flow:,.0f}M estimated "
                                        f"({summary.get('inflowCount', 0)} inflows, "
                                        f"{summary.get('outflowCount', 0)} outflows)")

                # ── Crypto sections ──────────────────────────
                if PodcastCategory.CRYPTO in active_cats:
                    if snapshot.crypto_extended:
                        st.subheader("Crypto Prices")
                        for coin in snapshot.crypto_extended[:10]:
                            cp = coin.change_percent_24h
                            arrow = "▲" if cp >= 0 else "▼"
                            color = "green" if cp >= 0 else "red"
                            st.markdown(
                                f"**{coin.symbol}** ({coin.name}): ${coin.price:,.2f} "
                                f"<span style='color:{color}'>{arrow} {cp:+.2f}%</span>",
                                unsafe_allow_html=True,
                            )
                    elif snapshot.crypto:
                        st.subheader("Crypto Prices")
                        for name, data in snapshot.crypto.items():
                            cp = data.get("change_percent", 0)
                            arrow = "▲" if cp >= 0 else "▼"
                            color = "green" if cp >= 0 else "red"
                            st.markdown(f"**{name}**: ${data.get('price', 0):,.2f} "
                                        f"<span style='color:{color}'>{arrow} {cp:+.2f}%</span>",
                                        unsafe_allow_html=True)

            with col2:
                # ── Finance Micro sections ───────────────────
                if PodcastCategory.FINANCE_MICRO in active_cats:
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

                # ── Geopolitics section ──────────────────────
                if PodcastCategory.GEOPOLITICS in active_cats:
                    if snapshot.conflict_events:
                        st.subheader(f"Armed Conflicts ({len(snapshot.conflict_events)})")
                        for e in snapshot.conflict_events[:5]:
                            st.markdown(f"- **{e.get('country', '')}**: {e.get('side_a', '')} vs {e.get('side_b', '')}")

                    if snapshot.unrest_events:
                        st.subheader(f"Unrest & Protests ({len(snapshot.unrest_events)})")
                        for e in snapshot.unrest_events[:5]:
                            st.markdown(f"- **{e.get('title', '')}** ({e.get('country', '')})")

                    if snapshot.sanctions:
                        st.subheader("Sanctions Pressure")
                        st.markdown(f"Total: **{snapshot.sanctions.get('total_count', 0):,}** entries | "
                                    f"Vessels: {snapshot.sanctions.get('vessel_count', 0):,} | "
                                    f"Aircraft: {snapshot.sanctions.get('aircraft_count', 0):,}")
                        for c in snapshot.sanctions.get("top_countries", [])[:5]:
                            st.markdown(f"- {c.get('country', '')}: {c.get('count', 0):,} entities")

                    if snapshot.predictions:
                        geo_preds = [p for p in snapshot.predictions if p.get("category") == "geopolitical"]
                        if geo_preds:
                            st.subheader("Prediction Markets")
                            for p in geo_preds[:5]:
                                st.markdown(f"- **{p.get('title', '')}** — Yes: {p.get('yes_price', 0):.0f}%")

                    if snapshot.geopolitics:
                        st.subheader(f"Intelligence ({len(snapshot.geopolitics)} stories)")
                        for item in snapshot.geopolitics[:8]:
                            st.markdown(f"- **{item.title}** ({item.source})")

                # ── AI Updates section ───────────────────────
                if PodcastCategory.AI_UPDATES in active_cats and snapshot.ai_updates:
                    st.subheader(f"AI Updates ({len(snapshot.ai_updates)} stories)")
                    for item in snapshot.ai_updates[:10]:
                        badge = item.subcategory.replace("_", " ").title()
                        st.markdown(f"- [{badge}] **{item.title}** ({item.source})")
                        if item.description:
                            st.caption(item.description[:200])

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
