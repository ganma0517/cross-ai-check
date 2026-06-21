# cross-ai-check（跨 AI 交叉檢核）

> **作者**：Wen-Cheng Lin　｜　**這是實驗性工具（experimental）**
>
> ⚠️ 還在開發中，行為可能改變。它只是幫你「找第二意見」，**不保證答案正確**，重要的事請自己再確認。要不要用、用到什麼程度，由你自己決定。

## 這是什麼？

這是一個 [Claude Code](https://docs.claude.com/en/docs/claude-code) 的外掛（skill）。

簡單說：Claude 先給出一個答案，然後這個工具會把**同樣的題目**交給**別的 AI**（你電腦裡的 `ollama`，或雲端的 `gemini`、`codex`）再算一次，最後比對大家的答案。

為什麼有用？因為不同的 AI 會在不同地方出錯。**大家都同意的部分，比較可信；意見不一樣的地方，就要特別注意。**

可以用在三種情況：
- **看程式碼**：找 bug、安全問題、設計缺陷
- **查資料**：判斷某個說法、某篇文獻引用是不是真的
- **檢查推理**：找出邏輯漏洞、想想反方觀點

---

## 檔案結構

```
cross-ai-check/
├── SKILL.md                  # 給 Claude 看的操作說明（怎麼跑這個流程）
├── README.md                 # 你現在看的這份：總覽與注意事項
├── scripts/
│   ├── cross_check.py         # 主程式：把題目發給各個 AI，收回它們的答案
│   └── set-api-key.sh         # 幫你安全地把 API 金鑰存進電腦的小工具
├── references/
│   └── backends.md            # 各個 AI 後端怎麼安裝、設定的細節
└── evals/
    └── evals.json             # 測試用的範例題
```

| 檔案 | 做什麼 |
|------|------|
| `SKILL.md` | Claude 的操作手冊：先自己想答案 → 把題目交給別的 AI → 比對後下結論 |
| `scripts/cross_check.py` | 真正執行的程式。哪個 AI 沒裝好就自動跳過，不會整個壞掉 |
| `scripts/set-api-key.sh` | 安全存金鑰，避免常見錯誤（存成空白、重複、被記錄下來） |
| `references/backends.md` | 想深入設定各個 AI 時看這份 |

---

## 怎麼用

平常你只要跟 Claude 說「**用別的 AI 再檢查一次**」「**找第二意見**」就會啟動，不用記指令。

如果想自己手動跑：

```bash
# 1. 先看有哪些 AI 可以用
python3 scripts/cross_check.py --list

# 2. 指定這次要用哪幾個 AI（用逗號隔開）
python3 scripts/cross_check.py --prompt-file 題目.md \
  --backends ollama,gemini \
  --system "<要它扮演什麼角色，見 SKILL.md>"
```

**你可以自己選要用哪些 AI**。由 Claude 帶你跑時，它會先列出可用的 AI 讓你挑（預設只用免費、離線的 `ollama`；要用雲端的會先問過你）。

> 提醒：這個功能**不是必要的**。只用免費離線的 `ollama`，或乾脆不用交叉檢核，都完全沒問題。

---

## 使用前要知道的事

1. **別的 AI 也會出錯**，尤其電腦裡的小型 AI 能力有限，有時還會答非所問。它的用處是「多一雙眼睛」，最後判斷還是要靠 Claude 回頭核對原始資料。
2. **查文獻真假要靠搜尋，不能靠 AI**。一個沒連網的 AI 不知道某篇論文存不存在，問它只會亂猜。
3. **設定金鑰後要重開 Claude Code**，新設定才會生效。

## 隱私

| AI 後端 | 你的資料會怎樣 | 適合 |
|------|---------|------|
| `ollama`（你的電腦） | **不外傳**，完全留在本機 | 機密、還沒發表的內容 |
| `gemini`、`codex`（雲端） | 會**上傳到 Google／OpenAI** | 一般、不敏感的內容 |

要檢查機密或未發表的東西，請用 `ollama`，或乾脆別用雲端的。雲端供應商怎麼處理你的資料，看他們的條款，這個工具管不到。

## 費用

- 雲端的 `gemini`、`codex` 大多**按使用量收費**（`gemini` 有免費額度，但有上限）。
- 用的 AI 越多，一次花得越多。想省錢就只用本機的 `ollama`。
- 費用要你自己承擔，記得留意帳單。

## 金鑰安全

- **絕對不要把 API 金鑰貼到任何聊天視窗**（Claude、ChatGPT、Gemini 都一樣）。一旦貼出去就等於外洩，要馬上去原網站作廢、重新申請。
- 金鑰只該存在你電腦的 `~/.zshrc`。可以用內附的工具安全存入：
  ```bash
  zsh scripts/set-api-key.sh GEMINI_API_KEY   # 跳出提示 → 貼金鑰 → Enter → 完成
  zsh scripts/set-api-key.sh OPENAI_API_KEY
  ```
- 也別把金鑰寫進任何會上傳到 GitHub 的檔案。

各個 AI 怎麼安裝設定，看 [`references/backends.md`](references/backends.md)。

---

## 免責聲明

這是一個實驗性的個人專案，**照現況提供，不負任何擔保**。用之前請自己評估適不適合，輸出的結果也請自己再確認。
