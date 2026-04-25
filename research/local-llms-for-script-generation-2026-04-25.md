# Open-Source LLMs for Local Script Generation (Market Pulse)

_Research date: 2026-04-25 • Depth: medium-deep • Search: Tavily_

## TL;DR

For a long-form (~2000 word), two-speaker, citation-bearing finance podcast script, the **two strongest local options in April 2026 are Qwen 3.5–27B and Google's brand-new Gemma 4** (released April 2, 2026). Qwen 3.5–27B leads the published instruction-following leaderboards (IFEval 95.0%, IFBench 76.5%)[^1][^9]; Gemma 4 26B-A4B (MoE, 3.8B active) and 31B Dense ship native structured-JSON + system-instruction support and post huge gains over Gemma 3, with the 31B claiming #3 on the Arena AI open-model leaderboard[^31]. Mistral Small 3.1 / 3.2 is a solid non-Qwen, non-Gemma alternative. Local flagships like Kimi K2/K2.5, GLM-5, and Llama 4 Maverick exist but require **>200 GB of combined VRAM+RAM** and are out of reach for typical prosumer machines[^7][^11][^12]. Below 16 GB VRAM, expect a meaningful quality drop versus Gemini 2.5 Flash regardless of model — local mode should be a dev/cost-saver, not the default for episodes shipped to subscribers.

## Key findings

- **Qwen 3.5–27B (dense)** is the highest-scoring open-weight model on instruction following (IFEval 95.0, IFBench 76.5) and retains >97% of full-precision quality at Q4 — fits in ~16 GB VRAM.[^1][^9][^10]
- **Qwen 3.5–35B-A3B (MoE)** runs at >100 t/s on a 4090 because only 3B params are active per token, ideal for fast iteration on lower VRAM.[^1][^2]
- **Phi-4 14B** has a documented IFEval weakness (Microsoft's own technical report calls it out)[^14] — not recommended for strict format adherence like `[S1]/[S2]`.
- **DeepSeek-R1 distills** (Qwen-based 14B/32B, Llama-70B) are reasoning-optimized but emit `<think>...</think>` traces by default[^4] — extra cleanup needed for clean dialogue.
- **Llama 4 Scout/Maverick** are technically open-weight but Maverick (400B total / 17B active) needs an 80 GB+ host[^5]; Scout fits on a single H100 (~109 GB params, ~80 GB Q4) — **out of consumer reach**.[^6]
- **Kimi K2 / K2.5** are 1T-parameter MoE — practical local deployment requires ~300 GB RAM + ~280 GB VRAM at Q4; reports of ~7 t/s on a multi-3090 home rig.[^11][^12]
- **GPT-OSS 20B** runs in 16 GB and matches OpenAI o3-mini on reasoning; **GPT-OSS 120B** needs an 80 GB GPU. Both are Apache 2.0, but instruction-hierarchy adherence trails proprietary o4-mini per OpenAI's own card.[^7][^8]
- **Gemma 3 27B** has best-in-class multimodal support and a 128K context, but loses to Qwen3.5-27B on instruction-following benchmarks.[^15][^16]
- **GLM-4.6 / 4.7 / 5** are 200B–744B-param flagships — only the 9B `glm-4.6v-flash` is comfortably local; the rest need workstation-class memory.[^17][^18]

## Details

### 1. Qwen 3.5 family — the recommended baseline

Qwen 3.5 is what changed the landscape since the last research pass. The dense 27B variant tops IFEval at 0.950 and IFBench at 0.765, beating every open-weight competitor and some closed-source models including Claude Sonnet 4.5[^1][^9]. The MoE variants — 35B-A3B (3B active), 122B-A10B (10B active), 397B-A17B (17B active) — apply the same training recipe with progressively larger expert pools.[^2]

For Market Pulse's script-generation task — strict `[S1]/[S2]` speaker tagging, ~2000-word target, no advice-language drift — instruction following is the single most important capability, and Qwen 3.5–27B is the model with the cleanest score there.

**Ollama tags & footprints (Q4_K_M unless noted):**
| Tag | Params | Active | Disk | VRAM (Q4) | Notes |
|---|---|---|---|---|---|
| `qwen3.5:9b` | 9B | dense | ~6 GB | ~8 GB | Entry level, 8 GB cards |
| `qwen3.5:27b` | 27B | dense | ~16 GB | ~20 GB | Best instruction follower at sane size |
| `qwen3.5:35b-a3b` | 35B | 3B MoE | ~22 GB | ~16 GB + RAM | Fast iteration; experts spill to RAM |
| `qwen3.5:122b-a10b` | 122B | 10B MoE | ~70 GB | 48 GB+ workstation | Frontier-tier locally |

License: Apache 2.0[^2]. Quantization-aware quality at Q4 is "outstanding" per Cherickal's 2026 review, retaining >97% of FP scores at 27B.[^3]

### 2. Older Qwen 3 — still a perfectly fine fallback

`qwen3:30b-a3b` and `qwen3:32b` are the predecessors. They remain widely deployed and well-tested, and Qwen 3 introduced the now-standard hybrid thinking mode (toggle with `enable_thinking=False` or by injecting `/no_think` in the system prompt — important for our pipeline, which doesn't want `<think>` traces in scripted dialogue).[^19][^20]

If `qwen3.5` tags aren't available on your local Ollama mirror, `qwen3:32b` is the closest substitute — narrower instruction-following gap than any Llama / Mistral / Gemma alternative.

### 3. Mistral Small 3.1 / 3.2 — best non-Qwen

Mistral Small 3 (24B, Apache 2.0) was specifically designed for "the 80% of generative AI tasks that require robust language and instruction following with very low latency"[^21]. Released January 2025; Mistral Small 3.1 added 128K context and image input March 2025[^22]; Mistral Small 3.2 (June 2025) further refined instruction following.[^23] Fits a 24 GB card or 32 GB Mac.

IFEval: 0.829 — well below Qwen 3.5–27B (0.950)[^9]. But Mistral models tend to be *more concise* in practice than Qwen, which can be a feature for tightly word-budgeted generation. Recommended Ollama tag: `mistral-small3.1:24b-instruct-2503-q4_K_M` (~15 GB on disk, requires Ollama 0.6.5+).[^24]

### 4. DeepSeek — R1 distills, V3, full R1

Two distinct stories here:

**DeepSeek-V3 / R1 (full)** — 671B-param MoE with 37B active. Strong on benchmarks (IF-Eval prompt-strict 86.1 for V3, 83.3 for R1) but practically un-runnable at home — requires server-class memory similar to Kimi K2.[^25]

**DeepSeek-R1 distill series** — six smaller dense models fine-tuned on R1's chain-of-thought outputs[^4]. The Qwen-14B and Qwen-32B distills produce dramatic reasoning gains (AIME 2024 pass@1: 69.7 / 72.6 vs. ~30 for the same-size base models). But:

- All distills emit `<think>...</think>` blocks — the pipeline would need a stripping pass before TTS.
- They optimize for math/code reasoning, not necessarily instruction following or natural-sounding dialogue.
- For a podcast script generator where output structure matters more than logic chains, the distills are **overkill in the wrong direction**.

`ollama run deepseek-r1:8b` now points to DeepSeek-R1-0528-Qwen3-8B, the most recent distill, which beats Qwen3-8B on AIME but inherits the same thinking-mode caveat.[^4]

### 5. Llama 4 (Scout, Maverick, Behemoth)

| Model | Params (total / active) | License | Local? |
|---|---|---|---|
| Llama 4 Scout | 109B / 17B (16 experts) | Llama 4 Community License | One H100 at Q4 (~80 GB) — not consumer |
| Llama 4 Maverick | 400B / 17B (128 experts) | Llama 4 Community License | One H100 *host* (multi-GPU) |
| Llama 4 Behemoth | 2T / 288B | preview only | Data-center scale |

Scout's headline feature is a 10M-token context window with >95% needle-in-a-haystack accuracy at 8M[^5][^6]. Maverick scores higher on reasoning benchmarks (LMArena ELO 1417) but Scout often wins on sub-bench long-context tasks. Llama 4 also has a non-permissive community license — not equivalent to Apache.

For Market Pulse: **skip** unless you have an H100. Snapshot data fits in 32K tokens easily; the 10M context is wasted.

### 6. Gemma 4 — Google's new flagship (April 2, 2026 release)

**Gemma 4 launched 23 days before this research date** and substantially changes the picture for Google's open-weight family. Built on the same research foundation as Gemini 3, released under Apache 2.0, and natively multimodal (text + image + audio + video).[^30][^31][^32] Four variants:

| Variant | Type | Total / Active | Context | Footprint (Q4) |
|---|---|---|---|---|
| `gemma4:e2b` | Edge dense | 2.3B | 128K | ~2 GB |
| `gemma4:e4b` | Edge dense | 4.5B | 128K | ~3 GB |
| `gemma4:26b` | MoE | 25.2B / 3.8B active | 256K | ~16 GB |
| `gemma4:31b` | Dense | 31B | 256K | ~20 GB |

The 26B-A4B is the surprise of the family — only 3.8B params active per token, so it runs **faster than the 4B edge model** while landing within 2% of the 31B dense on every benchmark Google published.[^33]

**Benchmarks from Google's official model card[^31][^32]** (Gemma 4 31B → Gemma 3 27B no-think):

| Benchmark | Gemma 4 31B | Gemma 4 26B-A4B | Gemma 3 27B |
|---|---|---|---|
| MMLU Pro | 85.2% | 82.6% | 67.6% |
| AIME 2026 (no tools) | 89.2% | 88.3% | 20.8% |
| GPQA Diamond | 84.3% | 82.3% | 42.4% |
| LiveCodeBench v6 | 80.0% | 77.1% | 29.1% |
| Codeforces ELO | 2150 | 1718 | 110 |
| τ²-Bench (agentic) | 76.9% | 68.2% | 16.2% |
| BigBench Extra Hard | 74.4% | 64.8% | 19.3% |

The jumps are not marginal. Gemma 4 31B on GPQA Diamond (84.3%) sits within 1.5 points of Qwen 3.5–27B (85.8%)[^33], and Google's blog explicitly calls out "significant improvements in math and instruction-following benchmarks"[^34]. The 31B variant is currently #3 on the Arena AI open-model leaderboard; the 26B MoE is #6.[^31]

**Why this matters for Market Pulse:** Gemma 4 ships with **native structured JSON output and native system-instruction handling**[^31] — the exact two capabilities our `[S1]/[S2]` strict-format pipeline depends on. The 26B MoE also has the practical edge of running at 4B-speed but with 26B-class quality.

**Caveats:**
- Google did not publish IFEval/IFBench numbers in the headline release that would let us slot Gemma 4 into the leaderboard ranking against Qwen 3.5–27B. The "improvement" claim is qualitative for now.
- Some Gemma 4 features may need a recent Ollama version — Hacker News commenters report needing the v0.20 pre-release for full functionality on launch week.[^33]
- Sliding-window attention is 1024 tokens for the 26B MoE[^32] — for an ~8K-token script this is fine, but worth keeping in mind for the "deep" 8000-word preset.

### 6b. Gemma 3 — still useful as a fallback

Gemma 3 27B remains widely deployed and well-tested for vision-capable use cases[^15][^16]. Benchmarks (PT 27B): MMLU 78.6, HellaSwag 85.6, TriviaQA 85.5. The QAT variants (`gemma3:27b-it-qat`) preserve quality at lower memory footprint. **But for a fresh deployment in April 2026, prefer Gemma 4 over Gemma 3** — the gaps in Google's own comparison table are too large to justify staying on the older generation.

### 7. Phi-4 (14B) and Phi-4-reasoning

Microsoft's own Phi-4 technical report explicitly flags IFEval as the model's weakest benchmark: "phi-4's weakest benchmark scores are on SimpleQA, DROP, and IFEval. … IFEval reveals a real weakness of our model — it has trouble strictly following instructions."[^14]

For our `[S1]/[S2]` formatting + word-budget + no-advice-phrase requirements, this is a deal-breaker. **Skip Phi-4 for script generation**, even though it's competitive on knowledge benchmarks for its size.

`phi4-reasoning:14b` (an SFT/RL fine-tune on o3-mini reasoning traces) fixes some of this but stays behind Qwen 3.5 on IFEval (0.834 per llm-stats).[^9]

### 8. GPT-OSS (20B / 120B) — OpenAI's open-weight release

Apache 2.0, released August 2025[^7][^8]. The 20B variant runs in 16 GB; 120B needs an 80 GB GPU.[^7]

Strengths: reasoning matches o3-mini (20B) and o4-mini (120B); strong tool use; chain-of-thought visibility for debugging.[^7] On IFBench, GPT-OSS-120B-High scores 0.695 — above most other open models but below the Qwen 3.5 line.[^9]

Caveat from the model card itself: "gpt-oss-120b and gpt-oss-20b generally underperform OpenAI o4-mini on our instruction hierarchy evaluations"[^8] — same red flag as Phi-4. Acceptable for general chat; less ideal for strict-format generation.

### 9. GLM family (4.6, 4.7, 5)

Z.ai's GLM-4.6 is a 355B-parameter dense reasoning model[^17]; GLM-4.6V-Flash (9B) is the only consumer-runnable variant.[^17] GLM-5 is 744B / 40B-active MoE — definitely server-class.[^18]

Reports from Codeminer42's stress test: "Opus 4.5 outperformed GLM 4.7 by a large margin" on a debugging task, but GLM 4.7 was rated "more than sufficient" for "routine CRUD operations, CSS tweaks, or boilerplate"[^27]. Translates to: probably fine for podcast scripts, but no public IFEval/IFBench data was found that justifies preferring it over Qwen 3.5.

### 10. Kimi K2 / K2.5 — local-impractical

User specifically asked to confirm. Kimi K2 is **1 trillion total parameters, 32B active, MoE**, trained with the Muon optimizer[^11]. Even at Q1/Q2 GGUF quantization (Unsloth's TQ1_0), local deployment requires:

- Single-pod-with-eight-3090s example: ~300 GB RAM, ~280 GB VRAM at peak, ~7 t/s generation[^12]
- 32 GB single-GPU: only ~50% VRAM utilized at 19K context — you'd be CPU-spilling most experts[^28]

**Verdict: not realistic on prosumer hardware.** Kimi K2.5 has the same architecture[^13]. If you have an H100/MI300 cluster and want to try, the model is excellent at agentic tasks, but it's the wrong tool for our budget.

### 11. Other 2025–2026 models (briefly)

- **Granite 3.x (IBM)** — Apache 2.0, well-instructed, but no entry in the IFEval/IFBench top-50 reviewed[^9]; competitive at small sizes (2B/8B) for edge use.
- **Yi-Lightning / Yi 1.5** — minimal recent activity in the sources reviewed; superseded by Qwen 3.5 for similar use cases.
- **Command-R / Command-R+** (Cohere) — RAG-optimized, but the latest open weights I could find were the 2024 generation.
- **Hermes 3 70B (Nous)** — tops the IFBench leaderboard at 0.812 — *higher than Qwen 3.5–27B*[^9]. Very interesting for instruction-strict use, but 70B parameters means 48GB+ at Q4 and slower throughput. Worth piloting on a workstation tier.
- **Devstral Small 2 / Magistral** — Mistral's coding/reasoning specialist branches, not relevant for prose generation.
- **MiniMax M2.1 / M2.5** — competitive (IFBench 0.700 for M2.1)[^9], 230B params, similar local-impractical profile to GLM.
- **NVIDIA Nemotron 3 Super (120B-A12B)** — IFBench 0.726, MoE design[^9]; would need vLLM + a high-end workstation.

## Recommendations by hardware tier (for Market Pulse)

| VRAM | First pick | Backup | Skip |
|---|---|---|---|
| **8 GB** | `qwen3.5:9b` (Q4) | `gemma3:4b-it-qat` | Anything 14B+ unless CPU-spilling is OK |
| **16 GB** | `gemma4:26b` (MoE, 3.8B active, ~16 GB) or `qwen3.5:27b` (Q4_K_M, tight) | `qwen3.5:35b-a3b`, `mistral-small3.1:24b` | `phi4`, `deepseek-r1` for non-reasoning tasks |
| **24 GB** | `gemma4:31b` Q4 or `qwen3.5:27b` (Q5_K_M / Q6_K) | `qwen3:32b`, `gemma3:27b-it-qat` | `llama4-scout` (still doesn't fit) |
| **48 GB+** | `qwen3.5:27b` Q8 + `qwen3.5:122b-a10b` Q4 | `hermes-3:70b` (top IFBench), `gpt-oss:120b`, `gemma4:31b` Q8 | `kimi-k2`, `glm-5` (not enough memory) |
| **Server (80 GB+)** | `llama4-scout` Q4, `glm-4.6` Q2, `gpt-oss:120b` FP8 | DeepSeek V3.1 | — |

**Pipeline-specific suggestions:**
- Set `num_ctx` and `num_predict` explicitly when calling Qwen3.x via Ollama — defaults (2048 / -1) cause silent truncation on 8K-token script generation.[^20]
- For Qwen 3.5 / Qwen 3, inject `/no_think` in the system prompt to prevent thinking tags polluting the `[S1]/[S2]` stream. Or pull the `*-instruct-2507` tag explicitly.
- Don't rely on 8K-token output reaching the full 8K — LIFEBench (NeurIPS 2025) found that "almost all models fail to reach the vendor-claimed maximum output lengths in practice".[^29] For a 2000-word script (~3000 tokens), this isn't a problem; for the "deep" 8000-word preset, it might be.

## Disagreements & open questions

- **Qwen 3.5 release timing**: Cherickal's Medium piece dates `Qwen3.5–27B` to February 24, 2026[^3] while haimaker.ai cites it as already deployed in 2026[^1]. Both agree it's current. SiliconFlow's "best of 2026" piece still ranks Qwen3-235B-A22B and Qwen3-30B-A3B as their top picks, suggesting Qwen 3.5 may not yet be the default in all distribution channels[^2].
- **Hermes 3 70B vs Qwen 3.5–27B on IFBench**: llm-stats puts Hermes 3 70B at 0.812 (rank 1) and Qwen 3.5–27B at 0.765 (rank 2)[^9]. If you have 48 GB+, Hermes 3 70B may be the stronger instruction follower despite the 2.5× footprint. Worth A/B-ing on your actual prompts.
- **Qwen 3.5 Ollama availability**: I could not independently verify that `qwen3.5:27b` is currently on the official `ollama.com/library` registry as of 2026-04-25 — multiple second-hand sources reference it[^1][^2][^3] but I did not fetch the registry page directly. If it's not yet there, fall back to `qwen3:32b` (which definitely is).

## Sources

[^1]: haimaker.ai — "Best Ollama Models for OpenClaw (2026)" — https://haimaker.ai/blog/best-local-models-for-openclaw/ (accessed 2026-04-25)
[^2]: SiliconFlow — "The Best Qwen3 Models in 2026" — https://www.siliconflow.com/articles/en/the-best-qwen3-models-in-2025 (accessed 2026-04-25)
[^3]: Cherickal — "How to Run Your Own Local LLM — 2026 Edition" — https://thomascherickal.medium.com/how-to-run-your-own-local-llm-2026-edition-version-1-7ec6fe654c03 (accessed 2026-04-25)
[^4]: Ollama — `deepseek-r1:32b` model card — https://ollama.com/library/deepseek-r1:32b (accessed 2026-04-25)
[^5]: docsbot — "Llama 4 Scout vs Maverick comparison" — https://docsbot.ai/models/compare/llama-4-scout/llama-4-maverick (accessed 2026-04-25)
[^6]: Local AI Master — "Llama 4 Local Setup" — https://localaimaster.com/blog/llama-4-local-setup-guide (accessed 2026-04-25)
[^7]: OpenAI — "Introducing gpt-oss" — https://openai.com/index/introducing-gpt-oss/ (accessed 2026-04-25)
[^8]: arXiv — "gpt-oss-120b & gpt-oss-20b Model Card" — https://arxiv.org/pdf/2508.10925 (accessed 2026-04-25)
[^9]: llm-stats.com — IFEval and IFBench leaderboards — https://llm-stats.com/benchmarks/ifeval and https://llm-stats.com/benchmarks/ifbench (accessed 2026-04-25)
[^10]: benchlm.ai — "Instruction Following Benchmarks 2026" — https://benchlm.ai/instruction-following (accessed 2026-04-25)
[^11]: Runpod — "Running a 1-Trillion Parameter AI Model In a Single Pod" — https://www.runpod.io/blog/guide-to-moonshotais-kimi-k2-on-runpod (accessed 2026-04-25)
[^12]: Abhishek Mishra — "Trillion Parameter AI at Home" — https://hackmd.io/@abhishek-mishra/H12rmkZl-g (accessed 2026-04-25)
[^13]: DataCamp — "How to Run Kimi K2.5 Locally" — https://www.datacamp.com/tutorial/how-to-run-kimi-k2-5-locally (accessed 2026-04-25)
[^14]: Microsoft Research — "Phi-4 Technical Report" — https://www.microsoft.com/en-us/research/wp-content/uploads/2024/12/P4TechReport.pdf (accessed 2026-04-25)
[^15]: Hugging Face — `google/gemma-3-27b-pt` model card — https://huggingface.co/google/gemma-3-27b-pt (accessed 2026-04-25)
[^16]: Zazencodes — "Ultimate Gemma 3 Guide — Testing 1b, 4b, 12b and 27b" — https://zazencodes.com/blog/ultimate-gemma3-ollama-guide-testing-1b-4b-12b-27b (accessed 2026-04-25)
[^17]: Unsloth — "GLM-4.6: Run Locally Guide" — https://unsloth.ai/docs/models/tutorials/glm-4.6-how-to-run-locally (accessed 2026-04-25)
[^18]: Ollama search — GLM family — https://ollama.com/search?q=glm (accessed 2026-04-25)
[^19]: Qwen blog — "Qwen3: Think Deeper, Act Faster" — https://qwenlm.github.io/blog/qwen3/ (accessed 2026-04-25)
[^20]: GitHub — `QwenLM/qwen3` README — https://github.com/QwenLM/qwen3 (accessed 2026-04-25)
[^21]: Mistral AI — "Mistral Small 3" — https://mistral.ai/news/mistral-small-3 (accessed 2026-04-25)
[^22]: Simon Willison — "Mistral Small 3.1" — https://simonwillison.net/2025/Mar/17/mistral-small-31/ (accessed 2026-04-25)
[^23]: Artificial Analysis — "Mistral Small 3.2" — https://artificialanalysis.ai/models/mistral-small-3-2 (accessed 2026-04-25)
[^24]: Ollama — `mistral-small3.1:24b-instruct-2503-q4_K_M` — https://ollama.com/library/mistral-small3.1:24b-instruct-2503-q4_K_M (accessed 2026-04-25)
[^25]: Hugging Face — `deepseek-ai/DeepSeek-R1` model card — https://huggingface.co/deepseek-ai/DeepSeek-R1 (accessed 2026-04-25)
[^26]: AiOps School — "The Best Ollama Models in 2026" — https://aiopsschool.com/blog/the-best-ollama-models-in-2026-which-model-should-you-run-on-your-hardware/ (accessed 2026-04-25)
[^27]: Codeminer42 — "Claude Code + Ollama: Stress Testing Opus 4.5 vs GLM 4.7" — https://blog.codeminer42.com/claude-code-ollama-stress-testing-opus-4-5-vs-glm-4-7/ (accessed 2026-04-25)
[^28]: Hugging Face Discussion — Kimi K2 Instruct GGUF offloading — https://huggingface.co/unsloth/Kimi-K2-Instruct-GGUF/discussions/5 (accessed 2026-04-25)
[^29]: NeurIPS 2025 — "LIFEBENCH: Evaluating Length Instruction Following in LLMs" — https://openreview.net/forum?id=dndqkXKY6W (accessed 2026-04-25)
[^30]: Google Blog — "Gemma 4: Our most capable open models to date" — https://blog.google/innovation-and-ai/technology/developers-tools/gemma-4/ (accessed 2026-04-25)
[^31]: Hugging Face Blog — "Welcome Gemma 4: Frontier multimodal intelligence on device" — https://huggingface.co/blog/gemma4 (accessed 2026-04-25)
[^32]: Google AI for Developers — "Gemma 4 model card" — https://ai.google.dev/gemma/docs/core/model_card_4 (accessed 2026-04-25)
[^33]: Towards AI — "I Tested All 4 Gemma 4 Models: The 26B One Is Cheating" — https://pub.towardsai.net/i-tested-all-4-gemma-4-models-the-26b-one-is-cheating-in-the-best-way-744e40d90d37 (accessed 2026-04-25)
[^34]: Mashable — "Google launches Gemma 4, a new open-source model" — https://mashable.com/article/google-releases-gemma-4-open-ai-model-now-open-source-how-to-try-it (accessed 2026-04-25)
