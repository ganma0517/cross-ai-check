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

本工具的核心概念是「**獨立交叉驗證**」：Claude 先產生結論，再將同一問題交由其他 AI 模型（本機的 `ollama`，或雲端的 `gemini`、`codex`）各自重新作答，最後比對彼此的差異。**多個模型一致同意的部分可信度較高；出現分歧之處，則是需要審慎檢視的地方。** 適用於程式碼審查、文獻與事實查證、以及推理檢核。

使用前須留意：

- **外部模型同樣可能出錯**，本機小型模型尤其能力有限、偶爾答非所問。它的角色是提供第二意見，最終仍須由 Claude 回到原始素材作判斷。
- **隱私**：`ollama` 於本機運行、不外傳資料；`gemini`、`codex` 則會將素材**上傳至雲端供應商**。涉及機密或未發表內容，建議僅使用 `ollama`，或不啟用雲端後端。
- **費用**：雲端後端多按用量計費，啟用的模型越多、單次成本越高；如需節省可僅使用 `ollama`。
- **金鑰安全**：API 金鑰屬個人機密，**切勿貼入任何對話視窗**（一經貼出即視同外洩，須立即撤銷重發），僅應存放於本機 `~/.zshrc`，可透過 `scripts/set-api-key.sh` 安全寫入。
- 本功能**非屬必要**：僅使用免費且離線的 `ollama`，或完全不啟用交叉檢核，皆可正常運作。

---

## Disclaimer

This is an experimental personal project, provided **as-is with no warranty**. Evaluate whether it fits your needs, and verify its output yourself.
