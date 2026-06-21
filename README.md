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

簡單講，就是「**找別的 AI 來幫你對答案**」。

Claude 先回答，這個工具再把同一題丟給其他 AI 重做一次——可以是你電腦裡的 `ollama`，或雲端的 `gemini`、`codex`。然後大家的答案擺一起比。**大家都講一樣的，比較放心；講法兜不攏的，就是你要多看兩眼的地方。** 拿來看程式碼、查文獻或某個說法是真是假、挑推理漏洞都行。

用之前先知道幾件事：

- **別的 AI 也會講錯**，尤其電腦裡的小模型，有時根本答非所問。它就是多一雙眼睛，最後還是 Claude 回去對原始資料說了算。
- **隱私**：`ollama` 跑在你電腦上，東西不外傳；`gemini`、`codex` 會把你的內容**傳上雲端**。機密的、還沒發表的，就只用 `ollama`，別開雲端。
- **錢**：雲端的多半用多少算多少，AI 開越多、一次越貴。想省就只跑 `ollama`。
- **金鑰**：API 金鑰是你的密碼，**千萬別貼到任何聊天框**（一貼出去就等於外洩，得馬上作廢重辦），只放自己電腦的 `~/.zshrc`，用 `scripts/set-api-key.sh` 存最保險。
- 這功能**不裝也沒差**：只用免費又離線的 `ollama`，或乾脆不用交叉檢核，都完全 OK。

---

## Disclaimer

This is an experimental personal project, provided **as-is with no warranty**. Evaluate whether it fits your needs, and verify its output yourself.
