---
name: cross-ai-check
description: >-
  Hand Claude's own conclusion to OTHER AI models (local `ollama`, plus cloud `codex`,
  `gemini`, etc.) for independent cross-verification, collect the points of disagreement, then
  deliver a final adjudication. Three modes: code review (bugs / security / design), fact &
  citation checking (are claims and references real), and general reasoning checks (logical gaps
  and counter-arguments). Use it whenever the user says things like "check this again with another
  AI", "cross-check across AIs", "get a second opinion", "let codex/ollama take a look too", or
  "cross-validate this conclusion / this code / this claim", or whenever they want to reduce a
  single model's blind spots and hallucinations — even if the skill is not named explicitly. Note:
  this skill is a workflow of "Claude answers first, then external models independently re-check,
  then Claude synthesizes" — NOT simply calling another model to answer in Claude's place.
---

# Cross-AI Check(跨 AI 交叉檢核)

> **作者 / Author**：Wen-Cheng Lin　｜　**狀態：實驗性 skill（experimental）**
>
> ⚠️ **使用前請仔細考慮**。本 skill 仍在迭代,行為與輸出可能變動;它的結論僅供**輔助第二意見**,
> 不保證正確,重要判斷請自行覆核。是否採用、採用到什麼程度,由使用者自行評估與負責。
>
> ⚠️ **API 風險(務必理解)**:啟用 `codex`/`gemini` 等雲端後端時——
> ① **隱私**:你送檢的素材會**上傳到 OpenAI／Google 伺服器**,機密或未發表內容請改用離線的 `ollama` 或不啟用;
> ② **費用**:雲端 API 多半**按 token 計費**,送越多後端、單次越貴,成本由你承擔;
> ③ **金鑰**:API key 屬個人機密,**切勿貼進任何對話框**,僅存本機 `~/.zshrc`(見 `references/backends.md`)。
> 不想承擔以上風險者,只用免費離線的 `ollama`、或完全不啟用交叉檢核即可(本功能非必要)。

## 這個 skill 在解決什麼問題

單一模型有自己的盲點與幻覺。讓**另一個獨立的模型**拿著相同素材重做一次判斷,再比對兩邊的分歧,
就能把「兩個模型都同意」的部分當成高信心結論,把「彼此打架」的部分標出來請使用者注意。
這比 Claude 自我複查更有效,因為外部模型的訓練分布不同,會在不同地方出錯——交集才可靠。

核心是 `scripts/cross_check.py`:它把素材送給所有**可用**的後端,任何後端沒裝/沒 key 就跳過並標註,
不會讓整批失敗(`ollama` 免 key 通常即可用,`codex`/`gemini` 設好 key 後會自動加入)。

## 這是「選用增強」,不裝也能用

交叉檢核**不是必要功能**——它只是替既有結論加一道獨立複查,**不影響其他任何工作**。
所以:

- **完全不想裝任何後端也行**:沒有可用後端時(`summary.available` 為 0),如實告訴使用者
  「目前沒有外部模型可檢核」,改用 Claude 自評即可,不要假裝做過交叉檢核。
- **要用、又不想碰雲端**:只裝免費離線的 `ollama` 就夠了,`codex`/`gemini` **可不裝**。
- **不主動勸裝**:除非使用者開口要交叉檢核/第二意見,否則不必引導他安裝後端。

## ⚠️ 啟用雲端後端前,先讓使用者知道風險(重要)

`codex`/`gemini` 需要設 API key 才會啟用。**在引導使用者設定前,務必提醒這三點**(細節見 `references/backends.md`):

1. **隱私**:`ollama` 完全離線、不外送;`codex`/`gemini` 會把**素材上傳**到 OpenAI/Google。
   檢核機密或未發表內容時,優先 `--backends ollama`。
2. **費用**:雲端後端多半**按 token 計費**(送越多後端、單次越貴);在意成本就只跑本機。
3. **金鑰安全**:**絕不要請使用者把 API key 貼進對話框**(會留進紀錄=外洩)。
   請他們自己在終端用防呆腳本 `zsh scripts/set-api-key.sh GEMINI_API_KEY`(本 skill 附帶)寫進 `~/.zshrc`,
   **設定後重啟 Claude Code** 才生效。你(Claude)若要代為檢查,只能查「有沒有寫入、長度與開頭」,不可回顯 key 內容。

## 鐵則:外部模型拿到的是「素材」,不是 Claude 的結論

交叉檢核的價值來自**獨立性**。如果把 Claude 的答案直接丟給外部模型問「對不對」,它會被你的措辭帶著走
(anchoring),只會附和,失去檢核意義。所以:

- 送給 `cross_check.py` 的 prompt **只放原始素材 + 要它判斷的問題**,**不要**放 Claude 的結論或傾向。
- 讓外部模型**自己從頭做一次**,然後由 Claude 在最後一步比對「我的 vs 它的」。

## 工作流程

### 1. Claude 先獨立完成自己的判斷
照常做這件事該做的分析(review 程式、查證主張、檢視推理),先在心裡/草稿得出 Claude 自己的結論。
**先不要**告訴使用者這是最終答案——還要過外部檢核。

### 2. 準備中性的素材檔
把要檢核的東西寫成一個檔(例如 `/tmp/cc_material.md`):放**原始素材**(程式碼片段、主張與其引用、
推理段落)與**中性問句**。依模式選 system prompt(見下方「三種模式」)。不要寫進 Claude 的判斷。

### 2.5 讓使用者選擇要用哪些檢核 AI（執行前必做）
**不要逕自把素材送給所有後端。** 先列出可用後端,讓使用者決定這次用哪些——這同時是隱私與費用的把關點。

```bash
python3 ~/.claude/skills/cross-ai-check/scripts/cross_check.py --list
```

把結果整理成簡短清單給使用者選,並標出各自的性質,例如:
- `ollama`（本機·離線·免費）— 不外送素材,隱私最佳
- `gemini`（雲端·Google·有免費額度）— 會上傳素材
- `codex`（雲端·OpenAI·按量計費）— 會上傳素材

選擇原則:
- **使用者已指明**（例:「只用 ollama」「也讓 gemini 看」）→ 照辦。
- **未指明**→ 主動詢問要用哪些(可用 AskUserQuestion 列出可用後端多選)。**預設只勾離線的 `ollama`**;
  要動用雲端後端(會外送素材＋可能計費)前,先取得使用者同意。
- **檢核機密／未發表內容**→ 提醒優先只用 `ollama`。
- 使用者選定後,用 `--backends` 帶入(見下一步);沒有任何可用後端就跳到本步驟末的 0 後端處理。

### 3. 呼叫外部模型（用上一步選定的後端）
```bash
python3 ~/.claude/skills/cross-ai-check/scripts/cross_check.py \
  --prompt-file /tmp/cc_material.md \
  --backends <使用者選定的後端,逗號分隔,例 ollama,gemini> \
  --system "<該模式的 system prompt>"
```
- `--backends` 用 2.5 步使用者**實際選定**的後端;省略才是「所有可用」——但本 skill 預設要先問,不要省略。
- 後端名可用短名(`ollama`/`codex`/`gemini`)或完整名(`ollama:qwen2.5:7b`)。
- 輸出是 JSON:每個後端有 `available`/`ok`/`response`/`error`。讀 `response` 作為該模型的獨立意見。
- 若 `summary.available` 為 0(沒有任何後端可用),如實告訴使用者並附上 `error` 裡的安裝提示,
  改用 Claude 自評,**不要假裝做了交叉檢核**。

### 3.5 檢查回應品質:本機小模型常會答非所問
本機小模型(如 `qwen2.5:7b`)能力有限,**有時會忽略你的問題、回出完全不相干的內容**
(實測曾發生:請它 review 一段 Python,它卻回了一段 A/B 測試的東西)。所以拿到 `response` 後,
先花一秒判斷它**有沒有真的在回答你問的素材**:

- 若明顯偏題(答的東西跟素材無關),**別把它當有效意見**。重寫成更聚焦、更具體的提問**重試一次**:
  把素材縮短、把問題講得更死(例如「這個函式在什麼輸入下會出錯?逐行看」),通常第二次就會切題。
- 為降低偏題機率,**素材檔本身就要聚焦**:一次只丟一段程式/一條主張/一段論證,不要塞一大坨。
- 重試一次仍偏題,就如實標註「外部模型本次未能切題,僅供參考」,以 Claude 判斷為準——不要硬把垃圾輸出寫進彙整。

### 4. 比對並裁決(這是 Claude 的核心價值)
把 Claude 自己的結論與各外部模型的 `response` 並排比對,只向使用者呈現**有意義的部分**:

```markdown
## 交叉檢核結果(參與模型:claude + ollama:qwen2.5:7b)

### ✅ 共識(高信心)
- <兩邊都同意的點>

### ⚠️ 分歧(需注意)
- **<議題>**:Claude 認為… / ollama 認為… → Claude 研判:<裁決與理由>

### ❓ 外部模型額外提出、值得查的點
- <Claude 原本沒提、但對方點出且合理的點>

### 最終結論
<綜合後的結論;若外部模型只是附和或品質不足,直說並以 Claude 判斷為準>
```

裁決時別盲從外部模型——本機小模型(如 7B)能力有限,可能出錯或答非所問。
把它當「第二雙眼睛」找遺漏,而非權威。理由要講清楚。

## 三種模式的 system prompt

依使用者要檢核的內容挑一個傳給 `--system`(可自行微調):

**A. 程式碼 review**
> 你是資深程式碼審查者。只根據提供的程式碼,獨立指出 bug、邊界條件、安全性與設計問題。
> 用繁體中文條列,每點標明「位置 + 問題 + 建議」。沒問題的地方不用硬找。不要重寫整段程式。

**B. 事實 / 文獻查證**
> 你是嚴謹的事實查核者。針對提供的每一條主張與引用,獨立判斷其正確性與可信度,
> 指出可能不實、誇大、或無法佐證之處。用繁體中文條列。不確定就說不確定,不要編造來源。

> ⚠️ **這個模式有個重要限制**:查證「某篇文獻/引用是否真實存在」靠的是**檢索能力,不是另一個 LLM**。
> 本機模型(qwen2.5:7b)沒有連網、不知道真實書目,你問它某篇論文真不真,它只會用語氣猜、甚至幻覺出假來源——
> 這點上它幫不了你。所以 fact-check 時請這樣分工:
> - **引用/來源是否存在、DOI、期刊、年份**:由 **Claude 自己用 WebSearch / firecrawl / 學術搜尋**去查,這才是可靠來源。
> - **送外部模型的部分**:聚焦在**它能貢獻的判斷**——例如「這個效果量(降 50%)在這個領域合不合理」「這個因果宣稱有沒有過度推論」這類推理性質疑。
> - 彙整時講清楚:來源真偽以**搜尋結果**為準,外部模型只補推理層的第二意見。
> 換句話說,本模式是「Claude 搜尋查證 + 外部模型推理複查」的組合,不要只靠第二個 LLM 來判斷文獻真假。

**C. 通用推理檢核**
> 你是嚴格的批判性審查者。獨立檢視這段推理的邏輯漏洞、隱藏假設、反例與反方意見。
> 用繁體中文條列最重要的疑點。針對論證本身,不要附和原作者立場。

## 擴充後端

要接新的 AI(例如 gemini 裝好、或某個自架 API):編輯 `scripts/cross_check.py` 的 `BACKENDS` 清單,
加一筆 `{name, detect, run, note}` 即可——`detect()` 判斷環境是否具備、`run(prompt, system)` 送出並回純文字。
SKILL.md 與呼叫方式都不必改。常見後端的安裝/設定見 `references/backends.md`。
