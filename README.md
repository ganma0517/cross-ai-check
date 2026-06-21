# cross-ai-check

> **Author**: Wen-Cheng Lin　｜　**Experimental skill**
>
> ⚠️ Still under development; behavior may change. It only gives you a **second opinion** — it does **not** guarantee correct answers. Double-check anything important yourself. Whether and how much to rely on it is your call.

## What it is

A [Claude Code](https://docs.claude.com/en/docs/claude-code) **skill**.

In short: Claude first produces an answer, then this tool hands the **same question** to **other AIs** (`ollama` on your own machine, or cloud models `gemini` / `codex`) to solve again, and finally compares everyone's answers.

Why it helps: different AIs fail in different places. **Where they all agree is more trustworthy; where they disagree is what you should look at carefully.**

Three modes:
- **Code review** — bugs, security, design flaws
- **Fact / citation check** — whether a claim or a cited reference is real
- **Reasoning check** — logical gaps and counter-arguments

---

## Structure

```
cross-ai-check/
├── SKILL.md                  # Instructions Claude reads (how to run the flow)
├── README.md                 # This file: overview and cautions
├── scripts/
│   ├── cross_check.py         # Core: sends the question to each AI, collects answers
│   └── set-api-key.sh         # Helper to safely store an API key in ~/.zshrc
├── references/
│   └── backends.md            # How to install / configure each AI backend
└── evals/
    └── evals.json             # Sample questions for testing
```

| File | Role |
|------|------|
| `SKILL.md` | Claude's playbook: form its own answer → hand the question to other AIs → compare and conclude |
| `scripts/cross_check.py` | The program that runs. A backend that isn't set up is skipped, not fatal |
| `scripts/set-api-key.sh` | Stores keys safely, avoiding common mistakes (empty value, duplicates, shell history) |
| `references/backends.md` | Read this for deeper per-backend setup |

---

## Usage

Normally you just tell Claude "**check this again with another AI**" or "**get a second opinion**" — no commands to memorize.

To run it manually:

```bash
# 1. See which AIs are available
python3 scripts/cross_check.py --list

# 2. Choose which AIs to use this time (comma-separated)
python3 scripts/cross_check.py --prompt-file question.md \
  --backends ollama,gemini \
  --system "<role for the AI to play; see SKILL.md>"
```

**You can pick which AIs to use.** When Claude drives it, it lists the available AIs and lets you choose (default is the free, offline `ollama`; it asks before using cloud ones).

> Note: this feature is **optional**. Using only the free offline `ollama`, or not using cross-checking at all, is perfectly fine.

---

## Before you use it

1. **Other AIs make mistakes too**, especially small local models, which sometimes answer off-topic. Treat them as "an extra pair of eyes"; the final judgment still comes from Claude checking the original material.
2. **Checking whether a reference is real needs search, not an AI.** An offline AI doesn't know if a paper exists and will just guess.
3. **Restart Claude Code after setting a key** so the new setting takes effect.

## Privacy

| Backend | What happens to your data | Good for |
|------|---------|------|
| `ollama` (your machine) | **Stays local**, never uploaded | confidential or unpublished content |
| `gemini`, `codex` (cloud) | **Uploaded** to Google / OpenAI | general, non-sensitive content |

For confidential or unpublished material, use `ollama` or skip the cloud backends. How providers handle your data is governed by their own terms — this tool can't control that.

## Cost

- Cloud `gemini` / `codex` mostly **charge by usage** (`gemini` has a free tier with limits).
- The more AIs you use, the more a single run costs. To save money, use only the local `ollama`.
- You bear the cost — keep an eye on your bill.

## Key safety

- **Never paste an API key into any chat window** (Claude, ChatGPT, Gemini alike). Once pasted it's effectively leaked — revoke and reissue it immediately.
- A key should only live in your machine's `~/.zshrc`. Use the bundled helper to store it safely:
  ```bash
  zsh scripts/set-api-key.sh GEMINI_API_KEY   # prompt → paste key → Enter → done
  zsh scripts/set-api-key.sh OPENAI_API_KEY
  ```
- Don't write a key into any file that gets committed to GitHub.

See [`references/backends.md`](references/backends.md) for per-backend setup.

---

## 中文摘要（補充）

這是一個 Claude Code 外掛：Claude 先給答案，再把**同一題**交給**別的 AI**（本機 `ollama`，或雲端 `gemini`／`codex`）重做一次，然後比對。**大家都同意的比較可信，意見不同的地方要特別留意。** 可用於程式碼 review、文獻／事實查證、推理檢核。

使用前請注意：

- **別的 AI 也會出錯**，小型本機模型有時答非所問；最終仍由 Claude 回頭核對原始資料。
- **隱私**：`ollama` 完全離線不外傳；`gemini`／`codex` 會把素材**上傳雲端**。機密或未發表內容請只用 `ollama`，或不啟用雲端。
- **費用**：雲端後端多半按用量計費，用越多越貴；省錢就只用 `ollama`。
- **金鑰安全**：API 金鑰**絕不要貼進任何聊天視窗**（等於外洩，要立刻作廢重發），只存在本機 `~/.zshrc`，可用 `scripts/set-api-key.sh` 安全寫入。
- 這個功能**非必要**：只用免費離線的 `ollama`、或完全不用交叉檢核都可以。

---

## Disclaimer

This is an experimental personal project, provided **as-is with no warranty**. Evaluate whether it fits your needs, and verify its output yourself.
