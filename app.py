import os
import time
from datetime import datetime

import streamlit as st
import yaml
from dotenv import load_dotenv

from src.data.categories import (
    PodcastCategory, CATEGORY_LABELS,
    CATEGORY_API_KEYS, API_KEY_LABELS, DEFAULT_CATEGORIES,
)
from src.data.collector_router import CategoryCollectorRouter
from src.script.generator import ScriptGenerator
from src.audio.kokoro_engine import KokoroEngine
from src.audio.processor import AudioProcessor
from src.audio.voice_blender import VOICE_CATALOG, voice_label
from src.utils.email_sender import send_episode_email

from src.ui import inject_theme, render_background
from src.ui.components import (
    render_hero, render_category_chips, render_category_descriptions,
    render_api_status, render_stage_card, render_metric,
    render_speaker_line, render_warning_card, render_success_card,
    render_error_card,
)


# ── Page config + theme (must run first) ─────────────────────
st.set_page_config(page_title="Market Pulse", page_icon="🎙️", layout="wide")
inject_theme()


@st.cache_resource
def load_config():
    load_dotenv()
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    for env_key, cfg_key in [
        ("GEMINI_API_KEY", "gemini_api_key"),
        ("FRED_API_KEY", "fred_api_key"),
        ("GNEWS_API_KEY", "gnews_api_key"),
        ("CURRENTS_API_KEY", "currents_api_key"),
        ("NEWSDATA_API_KEY", "newsdata_api_key"),
        ("EMAIL_ADDRESS", "email_address"),
        ("EMAIL_APP_PASSWORD", "email_app_password"),
    ]:
        config[cfg_key] = os.getenv(env_key, "")
    return config


# ── Session state defaults ───────────────────────────────────
for key, val in [
    ("snapshot", None), ("script", None), ("mp3_path", None),
    ("stage_times", {}), ("has_run", False),
]:
    if key not in st.session_state:
        st.session_state[key] = val

if "selected_categories" not in st.session_state:
    st.session_state["selected_categories"] = [c.value for c in DEFAULT_CATEGORIES]


config = load_config()
date = datetime.now().strftime("%Y-%m-%d")


# ── Background (reads live selection) ────────────────────────
current_selection_enums = [
    PodcastCategory(v) for v in st.session_state["selected_categories"]
]
render_background(current_selection_enums)


# ── Hero ─────────────────────────────────────────────────────
render_hero(date)


# ── Category chips (main column, replaces multiselect) ───────
selected_categories = render_category_chips()
render_category_descriptions(selected_categories)


# ── Sidebar: Control Deck ────────────────────────────────────
with st.sidebar:
    st.markdown("### Control Deck")

    required_keys = {"gemini_api_key"}
    for cat in selected_categories:
        for key_name in CATEGORY_API_KEYS.get(cat, []):
            required_keys.add(key_name)
    keys_ok = render_api_status(required_keys, config, API_KEY_LABELS)

    st.markdown("### Podcast")
    st.markdown(
        f'<div class="mp-card">'
        f'<div><strong>Name</strong> &nbsp; {config.get("podcast_name", "Market Pulse")}</div>'
        f'<div><strong>LLM</strong> &nbsp; <span class="mp-numeric">{config.get("gemini_model", "gemini-2.5-flash")}</span></div>'
        f'<div><strong>Date</strong> &nbsp; <span class="mp-numeric">{date}</span></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown("### Host Voices")
    male_voice_ids = [v["id"] for v in VOICE_CATALOG if v["gender"] == "male"]
    female_voice_ids = [v["id"] for v in VOICE_CATALOG if v["gender"] == "female"]
    configured_s1 = config.get("speaker_1_voice", "am_adam")
    configured_s2 = config.get("speaker_2_voice", "af_bella")
    s1_default_idx = male_voice_ids.index(configured_s1) if configured_s1 in male_voice_ids else 0
    s2_default_idx = female_voice_ids.index(configured_s2) if configured_s2 in female_voice_ids else 0
    selected_voice_s1 = st.selectbox(
        "Alex (Speaker 1)", options=male_voice_ids, index=s1_default_idx,
        format_func=voice_label,
        help="Highest-graded male voices: Michael, Fenrir, Puck (all C+).",
    )
    selected_voice_s2 = st.selectbox(
        "Sam (Speaker 2)", options=female_voice_ids, index=s2_default_idx,
        format_func=voice_label,
        help="Highest-graded female voices: Heart (A), Bella (A-), Emma / Nicole (B-).",
    )
    st.session_state.selected_voice_s1 = selected_voice_s1
    st.session_state.selected_voice_s2 = selected_voice_s2

    st.divider()
    if st.button("Reset", use_container_width=True):
        for k in ["snapshot", "script", "mp3_path", "stage_times", "has_run"]:
            st.session_state[k] = None if k != "stage_times" else {}
        st.session_state.has_run = False
        st.rerun()


# ── CTA ──────────────────────────────────────────────────────
if not selected_categories:
    render_warning_card("Select at least one category to generate a podcast.")

run_pipeline = st.button(
    "⚡ Generate Episode",
    type="primary",
    use_container_width=True,
    disabled=(not keys_ok) or st.session_state.has_run or (not selected_categories),
)


# ── Pipeline ─────────────────────────────────────────────────
if run_pipeline:
    output_dir = config.get("output_dir", "output")
    os.makedirs(output_dir, exist_ok=True)

    cat_names = ", ".join(CATEGORY_LABELS[c] for c in selected_categories)

    # STAGE 1: Data Collection
    with st.status(f"**Stage 1/3 — Collecting data for: {cat_names}...**", expanded=True) as status:
        t0 = time.time()

        router = CategoryCollectorRouter(config, selected_categories)

        def on_status(msg):
            st.write(msg)

        snapshot = router.collect_all(status_callback=on_status)
        snapshot.save(os.path.join(output_dir, f"{date}-snapshot.json"))
        st.session_state.snapshot = snapshot

        elapsed = time.time() - t0
        st.session_state.stage_times["data"] = elapsed
        status.update(label=f"**Stage 1/3 — Data collected** ({elapsed:.1f}s)",
                      state="complete", expanded=False)

    # STAGE 2: Script Generation
    with st.status("**Stage 2/3 — Generating podcast script...**", expanded=True) as status:
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
        status.update(label=f"**Stage 2/3 — Script generated** ({elapsed:.1f}s, {word_count} words)",
                      state="complete", expanded=False)

    # STAGE 3: Audio Generation
    with st.status("**Stage 3/3 — Generating audio...**", expanded=True) as status:
        t0 = time.time()

        st.write("Loading Kokoro-82M TTS model...")
        tts_cfg = config.get("tts", {}) or {}
        voice_s1 = st.session_state.get("selected_voice_s1", config.get("speaker_1_voice", "am_adam"))
        voice_s2 = st.session_state.get("selected_voice_s2", config.get("speaker_2_voice", "af_bella"))
        st.write(f"Voices: Alex = {voice_label(voice_s1)}  |  Sam = {voice_label(voice_s2)}")
        engine = KokoroEngine(
            voice_s1=voice_s1,
            voice_s2=voice_s2,
            speed=tts_cfg.get("base_speed", 1.0),
            enable_blending=tts_cfg.get("enable_blending", True),
            enable_prosody=tts_cfg.get("enable_prosody", True),
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
        status.update(label=f"**Stage 3/3 — Audio generated** ({elapsed:.1f}s, {duration/60:.1f} min episode)",
                      state="complete", expanded=False)

    st.session_state.has_run = True
    st.balloons()
    st.rerun()


# ── Results ──────────────────────────────────────────────────
def _render_data_sections(snapshot, active_cats: list[PodcastCategory]) -> None:
    """Render the data tab's per-category breakdown. Logic preserved from original app.py."""
    col1, col2 = st.columns(2)

    with col1:
        if PodcastCategory.FINANCE_MACRO in active_cats:
            if snapshot.indices:
                st.subheader("Market Indices")
                for name, data in snapshot.indices.items():
                    cp = data.get("change_percent", 0)
                    arrow = "▲" if cp >= 0 else "▼"
                    color = "#22c55e" if cp >= 0 else "#ef4444"
                    st.markdown(
                        f"**{name}**: {data.get('current', 0):,.2f} "
                        f"<span style='color:{color}'>{arrow} {cp:+.2f}%</span>",
                        unsafe_allow_html=True,
                    )

            if snapshot.fear_greed:
                fg = snapshot.fear_greed
                score = fg.get("score", 0)
                label = fg.get("label", "")
                fg_color = "#22c55e" if score >= 60 else ("#ef4444" if score <= 40 else "#f59e0b")
                st.markdown(
                    f"**Fear & Greed Index**: <span style='color:{fg_color};font-size:1.3em'>"
                    f"{score:.0f} ({label})</span>",
                    unsafe_allow_html=True,
                )

            if snapshot.macro_signals:
                ms = snapshot.macro_signals
                verdict = ms.get("verdict", "")
                v_color = "#22c55e" if verdict == "BUY" else ("#ef4444" if verdict == "SELL" else "#f59e0b")
                st.markdown(
                    f"**Macro Signal**: <span style='color:{v_color};font-weight:bold'>"
                    f"{verdict}</span> ({ms.get('bullish_count', 0)}/{ms.get('total_count', 0)} bullish)",
                    unsafe_allow_html=True,
                )

            if snapshot.commodities:
                st.subheader("Commodities")
                for name, data in snapshot.commodities.items():
                    cp = data.get("change_percent", 0)
                    arrow = "▲" if cp >= 0 else "▼"
                    color = "#22c55e" if cp >= 0 else "#ef4444"
                    st.markdown(
                        f"**{name}**: ${data.get('price', 0):,.2f} "
                        f"<span style='color:{color}'>{arrow} {cp:+.2f}%</span>",
                        unsafe_allow_html=True,
                    )

            if snapshot.sectors:
                st.subheader("Sector Performance")
                for s in snapshot.sectors[:8]:
                    cp = s.get("change", 0)
                    arrow = "▲" if cp >= 0 else "▼"
                    color = "#22c55e" if cp >= 0 else "#ef4444"
                    st.markdown(
                        f"**{s.get('name', s.get('symbol', ''))}**: "
                        f"<span style='color:{color}'>{arrow} {cp:+.2f}%</span>",
                        unsafe_allow_html=True,
                    )

            if snapshot.etf_flows:
                summary = snapshot.etf_flows.get("summary", {})
                if summary:
                    direction = summary.get("netDirection", "")
                    d_color = "#22c55e" if "INFLOW" in direction else "#ef4444"
                    total_flow = summary.get("totalEstFlow", 0) / 1e6
                    st.subheader("ETF Flows")
                    st.markdown(
                        f"<span style='color:{d_color};font-weight:600'>{direction}</span>: "
                        f"${total_flow:,.0f}M estimated "
                        f"({summary.get('inflowCount', 0)} inflows, "
                        f"{summary.get('outflowCount', 0)} outflows)",
                        unsafe_allow_html=True,
                    )

        if PodcastCategory.CRYPTO in active_cats:
            if snapshot.crypto_extended:
                st.subheader("Crypto Prices")
                for coin in snapshot.crypto_extended[:10]:
                    cp = coin.change_percent_24h
                    arrow = "▲" if cp >= 0 else "▼"
                    color = "#22c55e" if cp >= 0 else "#ef4444"
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
                    color = "#22c55e" if cp >= 0 else "#ef4444"
                    st.markdown(
                        f"**{name}**: ${data.get('price', 0):,.2f} "
                        f"<span style='color:{color}'>{arrow} {cp:+.2f}%</span>",
                        unsafe_allow_html=True,
                    )

    with col2:
        if PodcastCategory.FINANCE_MICRO in active_cats:
            st.subheader(f"Sentiment: {snapshot.market_sentiment.upper()}")

            if snapshot.top_gainers:
                st.subheader("Top Gainers")
                for m in snapshot.top_gainers[:5]:
                    st.markdown(
                        f"**{m.symbol}**: ${m.price:.2f} "
                        f"<span style='color:#22c55e'>▲ {m.change_percent:+.2f}%</span>",
                        unsafe_allow_html=True,
                    )

            if snapshot.top_losers:
                st.subheader("Top Losers")
                for m in snapshot.top_losers[:5]:
                    st.markdown(
                        f"**{m.symbol}**: ${m.price:.2f} "
                        f"<span style='color:#ef4444'>▼ {m.change_percent:+.2f}%</span>",
                        unsafe_allow_html=True,
                    )

            if snapshot.news:
                st.subheader(f"News ({len(snapshot.news)} articles)")
                for n in snapshot.news[:8]:
                    sc = "#22c55e" if n.sentiment > 0.1 else ("#ef4444" if n.sentiment < -0.1 else "#94a3b8")
                    st.markdown(
                        f"- **{n.title}** ({n.source}) "
                        f"<span style='color:{sc}'>{n.sentiment:+.2f}</span>",
                        unsafe_allow_html=True,
                    )

            if snapshot.earnings:
                st.subheader("Earnings")
                for e in snapshot.earnings[:5]:
                    beat = ""
                    if e.surprise_percent is not None:
                        beat = f" ({'beat' if e.surprise_percent > 0 else 'miss'}: {e.surprise_percent:+.1f}%)"
                    st.markdown(f"- **{e.symbol}**: EPS ${e.eps_actual or 'N/A'} vs ${e.eps_estimate or 'N/A'}{beat}")

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
                st.markdown(
                    f"Total: **{snapshot.sanctions.get('total_count', 0):,}** entries | "
                    f"Vessels: {snapshot.sanctions.get('vessel_count', 0):,} | "
                    f"Aircraft: {snapshot.sanctions.get('aircraft_count', 0):,}"
                )
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

        if PodcastCategory.AI_UPDATES in active_cats and snapshot.ai_updates:
            st.subheader(f"AI Updates ({len(snapshot.ai_updates)} stories)")
            for item in snapshot.ai_updates[:10]:
                badge = item.subcategory.replace("_", " ").title()
                st.markdown(f"- [{badge}] **{item.title}** ({item.source})")
                if item.description:
                    st.caption(item.description[:200])


if st.session_state.has_run:
    render_success_card("Episode ready — listen, download, or send below.")

    # Stage summary cards
    times = st.session_state.stage_times
    labels = {"data": "Data Collection", "script": "Script Generation", "audio": "Audio Generation"}
    for i, key in enumerate(["data", "script", "audio"], start=1):
        elapsed = times.get(key)
        if elapsed is not None:
            render_stage_card(i, 3, labels[key], state="done", elapsed_s=elapsed)
    total = sum(times.values()) if times else 0
    if total:
        render_metric("Total Pipeline Time", f"{total/60:.1f} min")

    tab_audio, tab_data, tab_script = st.tabs(["🎧 Audio", "📊 Market Data", "📝 Script"])

    # Audio tab
    with tab_audio:
        mp3_path = st.session_state.mp3_path
        if mp3_path and os.path.exists(mp3_path):
            file_size = os.path.getsize(mp3_path) / (1024 * 1024)
            st.markdown(
                f'<div class="mp-card"><strong>{os.path.basename(mp3_path)}</strong>'
                f' &nbsp; <span style="color: var(--mp-text-muted)">({file_size:.1f} MB)</span></div>',
                unsafe_allow_html=True,
            )
            st.audio(mp3_path, format="audio/mp3")
            with open(mp3_path, "rb") as f:
                st.download_button(
                    "Download MP3", data=f, file_name=os.path.basename(mp3_path),
                    mime="audio/mpeg", use_container_width=True,
                )
            st.divider()
            st.markdown("### Send via Email")
            email_configured = (config.get("email_address", "") and
                                config.get("email_app_password", ""))
            if not email_configured:
                st.caption("Set EMAIL_ADDRESS and EMAIL_APP_PASSWORD in .env to enable.")
            email_col1, email_col2 = st.columns([3, 1])
            with email_col1:
                recipient = st.text_input(
                    "Recipient email", placeholder="recipient@example.com",
                    disabled=not email_configured,
                )
            with email_col2:
                st.markdown("<br>", unsafe_allow_html=True)
                send_clicked = st.button(
                    "Send", type="primary", use_container_width=True,
                    disabled=not email_configured or not recipient,
                )
            if send_clicked and recipient:
                with st.spinner("Sending email..."):
                    snapshot = st.session_state.snapshot
                    cat_names_list = snapshot.categories if snapshot else []
                    cat_labels = [c.replace("_", " ").title() for c in cat_names_list]
                    sent = send_episode_email(
                        mp3_path=mp3_path, recipient=recipient,
                        categories=cat_labels,
                        sender_email=config.get("email_address"),
                        sender_password=config.get("email_app_password"),
                    )
                if sent:
                    render_success_card(f"Episode sent to {recipient}!")
                else:
                    render_error_card("Failed to send. Check EMAIL_ADDRESS and EMAIL_APP_PASSWORD in .env.")

    # Market Data tab
    with tab_data:
        snapshot = st.session_state.snapshot
        if snapshot:
            active_cats = ([PodcastCategory(c) for c in snapshot.categories]
                           if snapshot.categories else DEFAULT_CATEGORIES)
            _render_data_sections(snapshot, active_cats)

    # Script tab
    with tab_script:
        script = st.session_state.script
        if script:
            import re as _re
            word_count = len(script.split())
            render_metric("Word Count", f"{word_count:,}", delta=f"~{word_count // 150} min episode")
            st.divider()
            tag_re = _re.compile(r"^\[(S[12])(?::([a-z_]+))?\]\s*(.*)")
            for line in script.split("\n"):
                line = line.strip()
                if not line:
                    continue
                m = tag_re.match(line)
                if not m:
                    continue
                render_speaker_line(m.group(1), m.group(2), m.group(3))
