# cross-ai-check

> **Author**: Wen-Cheng Lin　｜　**Experimental skill**
>
> ⚠️ Still under development; behavior may change. It only gives you a **second opinion** — it does **not** guarantee correct answers. Double-check anything important yourself. Whether and how much to rely on it is your call.

## What it is

A [Claude Code](https://docs.claude.com/en/docs/claude-code) **skill** for **independent cross-verification**: Claude first reaches its own conclusion, then hands the *same raw material* to one or more **other AIs** (`ollama` on your machine, or cloud models `gemini` / `codex`) so they redo the judgment from scratch, and finally Claude compares everyone's answers.

It runs in three modes: **code review** (bugs / security / design), **fact & citation check** (are the claims and references real), and **reasoning check** (logical gaps and counter-arguments).

---

## The analysis workflow

The whole point is **independence** — a second model is only useful if it isn't led by Claude's wording. The flow enforces that:

```
┌─────────────────────┐
│ 1. Claude answers   │  Claude does the real analysis itself first
│    independently    │  (review / verify / reason) and forms a draft
└──────────┬──────────┘  conclusion — NOT yet shown as final.
           │
┌──────────▼──────────┐
│ 2. Neutral material │  The material + a neutral question are written to
│    file             │  a file. Claude's own conclusion is deliberately
└──────────┬──────────┘  left OUT, so the other AI can't just agree.
           │
┌──────────▼──────────┐
│ 3. Ask the user     │  List available backends; default to offline
│    which AIs        │  `ollama`. Get consent before any cloud backend
└──────────┬──────────┘  (uploads material + may cost money).
           │
┌──────────▼──────────┐
│ 4. External models  │  `cross_check.py` sends the material to each chosen
│    answer           │  backend and returns their raw, independent answers.
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│ 5. Compare &        │  Claude lines up its own conclusion against each
│    adjudicate       │  model's: consensus → high confidence, divergence
└─────────────────────┘  → flagged, with Claude's reasoned final call.
```

Run it through Claude (just say *"check this again with another AI"*), or manually:

```bash
python3 scripts/cross_check.py --list                  # see available backends
python3 scripts/cross_check.py --prompt-file question.md \
  --backends ollama,gemini \
  --system "<role for the AI to play; see SKILL.md>"
```

---

## Anti-hallucination strategy

Cross-checking only reduces hallucination if it's done right. The defenses built into this skill:

1. **Independence over anchoring.** External models receive **raw material, never Claude's conclusion**. Handing them "here's my answer, is it right?" just invites sycophantic agreement and destroys the check's value. Each model solves from scratch; Claude compares only at the end.

2. **Consensus = signal, divergence = work.** Different models have different training distributions and fail in *different* places. **Where they all agree is more trustworthy; where they disagree is exactly what you should scrutinize.** The intersection is the reliable part — not any single model's verdict.

3. **Citations need search, not an LLM.** Whether a paper / DOI / source actually *exists* is a **retrieval** question. An offline model has no live knowledge and will confidently invent fake sources. So fact-checking is split: **Claude verifies existence via WebSearch / firecrawl / scholarly search**, and the external model is only asked for *reasoning-level* doubts (is this effect size plausible, is this causal claim overreaching). Source truth is decided by search results, not a second LLM.

4. **Catch off-topic answers from small models.** Local models (e.g. `qwen2.5:7b`) sometimes ignore the question and answer something unrelated. Each response is sanity-checked for relevance; if it's off-topic, the prompt is tightened and retried once. Garbage output is **never laundered into the summary** — it's marked "could not stay on topic, for reference only."

5. **Claude adjudicates — it never blindly follows.** External models are a "second pair of eyes" for spotting omissions, not an authority. The final call stays with Claude going back to the original material, with reasons stated.

6. **No faking it.** If no backend is available (`summary.available == 0`), Claude says so plainly and falls back to self-review — it does **not** pretend a cross-check happened.

> Bottom line: this lowers the odds of a single-model blind spot; it does **not** guarantee correctness. Treat agreement as *more confident*, not *proven*.

---

## Privacy, cost & key safety

| Concern | What to know |
|---|---|
| **Privacy** | `ollama` runs locally and uploads nothing. `gemini` / `codex` **upload your material** to Google / OpenAI. For confidential or unpublished content, use `ollama` only or skip cloud backends. |
| **Cost** | Cloud backends may **charge by usage** (`gemini` has a limited free tier; `codex` depends on your account). The more backends per run, the higher the cost. Use only local `ollama` to stay free. |
| **API keys** | **Never paste an API key into any chat window** — once pasted it's leaked; revoke and reissue. Keys live only in `~/.zshrc`; store them with the bundled helper, then restart Claude Code: |

```bash
zsh scripts/set-api-key.sh GEMINI_API_KEY   # prompt → paste key → Enter → done
zsh scripts/set-api-key.sh OPENAI_API_KEY
```

See [`references/backends.md`](references/backends.md) for per-backend setup. Cross-checking is **optional** — using only offline `ollama`, or not cross-checking at all, works fine.

---

## 中文摘要（補充）

核心概念是「**獨立交叉驗證**」：Claude 先自己得出結論，再把**同一份原始素材**（不含 Claude 的判斷）交由其他 AI（本機 `ollama` 或雲端 `gemini`/`codex`）各自重做一次，最後比對差異。

**分析流程**：① Claude 先獨立作答 → ② 寫出中性素材檔（刻意不放 Claude 的結論）→ ③ 讓使用者選後端（預設離線 `ollama`，動用雲端前先取得同意）→ ④ 外部模型各自作答 → ⑤ Claude 並排比對裁決。

**防範幻覺策略**：① 給素材不給結論，避免 anchoring 與附和；② 多模型一致＝高信心，分歧＝需審視，交集才可靠；③ 文獻是否存在靠**檢索非 LLM**（離線模型會幻覺假來源），由 Claude 用搜尋查證、外部模型只補推理層質疑；④ 偵測本機小模型答非所問並重試一次，垃圾輸出不寫進彙整；⑤ 最終由 Claude 回到原始素材裁決，不盲從；⑥ 沒有可用後端就如實說明，不假裝做過交叉檢核。本功能可降低單一模型盲點，但**不保證正確**，一致只代表更有信心、非已證實。

---

## Disclaimer

This is an experimental personal project, provided **as-is with no warranty**. Evaluate whether it fits your needs, and verify its output yourself.
