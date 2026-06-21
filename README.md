# cross-ai-check（跨 AI 交叉檢核）

> **作者 / Author**：Wen-Cheng Lin　｜　**狀態：實驗性 skill（experimental）**
>
> ⚠️ 本 skill 仍在迭代，行為與輸出可能變動。它提供的是**輔助性第二意見，不保證正確**；
> 重要判斷請自行覆核。是否採用、採用到什麼程度，由使用者自行評估與負責。

一個 [Claude Code](https://docs.claude.com/en/docs/claude-code) skill：把 Claude 自己得出的結論，
交給**其他獨立 AI 模型**（本機 `ollama`、雲端 `codex`/`gemini`）重做一次判斷，收集分歧點後再由 Claude 彙整裁決。
價值來自**獨立性**——不同模型在不同地方出錯，兩邊都同意的部分才是高信心結論。

三種檢核模式：**程式碼 review**（bug／安全／設計）、**事實與文獻查證**（主張與引用真偽）、
**通用推理檢核**（邏輯漏洞與反方意見）。

---

## 構成結構

```
cross-ai-check/
├── SKILL.md                  # skill 主檔：觸發描述、工作流程、三種模式、裁決規則
├── README.md                 # 本檔：總覽、注意事項、隱私與 API 風險
├── scripts/
│   ├── cross_check.py         # 核心：多後端獨立意見收集器（偵測→送素材→回 JSON）
│   └── set-api-key.sh         # 防呆設定 API key 到 ~/.zshrc（隱藏輸入/擋空值/去重）
├── references/
│   └── backends.md            # 後端安裝/設定、安全須知、自訂後端範例
└── evals/
    └── evals.json             # 觸發評測樣本
```

| 檔案 | 角色 |
|------|------|
| `SKILL.md` | Claude 讀的指令本體；定義「先自評 → 送中性素材給外部模型 → 比對裁決」流程 |
| `scripts/cross_check.py` | 真正執行的程式；對所有**可用**後端送出 prompt，任一後端缺裝/缺 key 就跳過並標註，不讓整批失敗 |
| `scripts/set-api-key.sh` | 安全寫入 key 的小工具，避開「空值／重複行／進 shell history」等坑 |
| `references/backends.md` | 各後端細節與安全規範（深入內容） |

---

## 使用方式（摘要）

實際由 Claude 依 `SKILL.md` 驅動，使用者通常只要說「用別的 AI 再檢查一次」「跨 AI 比對」「找第二意見」即可。
手動呼叫核心程式：

```bash
# 1. 先看有哪些檢核 AI 可用
python3 scripts/cross_check.py --list

# 2. 用 --backends 指定這次要用哪些（逗號分隔；省略才是全用）
python3 scripts/cross_check.py --prompt-file material.md \
  --backends ollama,gemini \
  --system "<該模式的 system prompt，見 SKILL.md>"
```

**可自由選擇要用哪些檢核 AI**：由 Claude 驅動時，會在執行前列出可用後端讓你挑（預設只勾離線的 `ollama`，
動用雲端後端前會先徵得同意）；手動呼叫則用 `--backends` 指定。輸出為 JSON，每個後端含
`available`/`ok`/`response`/`error`。**只用免費離線的 `ollama`、或完全不啟用交叉檢核都可以——本功能非必要。**

---

## ⚠️ 使用注意事項

1. **這是第二意見，不是裁判**：外部模型**也會幻覺**，尤其本機小模型（如 `qwen2.5:7b`）能力有限、
   有時答非所問。它的角色是「找遺漏、標分歧」，最終裁決仍由 Claude 回到原始素材判斷。
2. **送素材、不送結論**：交叉檢核靠獨立性。把 Claude 的答案直接丟去問「對不對」會造成附和（anchoring），
   失去意義。`SKILL.md` 已規範只送原始素材＋中性問句。
3. **文獻真偽靠檢索、不靠 LLM**：某篇論文是否真實存在，要用搜尋／學術資料庫查，不能問另一個沒連網的模型。
4. **設定 key 後需重啟 Claude Code** 才會讀到新環境變數。

## 🔐 隱私權

| 後端 | 資料流向 | 適用 |
|------|---------|------|
| `ollama`（本機） | **完全離線**，素材不離開你的電腦 | 機密／未發表內容首選 |
| `codex`（OpenAI）、`gemini`（Google） | 你送檢的素材會**上傳到對方伺服器** | 一般、非敏感內容 |

- 檢核**機密或未發表內容**前，請優先用 `ollama`，或乾脆不啟用雲端後端。
- 雲端供應商對資料的留存／訓練政策以**各家條款為準**，本 skill 無法控制；介意者請走離線。

## 💳 API 風險與費用

- `codex`/`gemini` 走雲端 API，多半**按 token 計費**（`gemini` 有免費額度但有上限）。
- 由 Claude 驅動時預設只用離線的 `ollama`,動用雲端後端會先徵得同意;**你可隨時指定只用哪些後端**——
  後端越多、單次成本越高。在意花費就 `--backends ollama` 只跑本機。
- 費用由使用者自行承擔；請自行留意供應商用量與帳單。

## 🔑 金鑰安全

- **切勿把 API key 貼進任何對話框**（Claude／ChatGPT／Gemini 等）——會留進紀錄，等同外洩，須立即撤銷重發。
- key 只該存在本機 `~/.zshrc`，可用附帶腳本安全寫入：
  ```bash
  zsh scripts/set-api-key.sh GEMINI_API_KEY   # 提示→貼 key→Enter→✅ 已寫入
  zsh scripts/set-api-key.sh OPENAI_API_KEY
  ```
- 別把 key 寫進任何會被 git commit 的檔案。

各後端安裝與詳細設定見 [`references/backends.md`](references/backends.md)。

---

## 免責聲明

本 skill 為實驗性個人專案，**按現狀（as-is）提供，不負任何擔保**。使用前請自行評估是否適用，
並對輸出結果自行覆核與負責。
