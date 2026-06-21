# 後端設定參考(backends)

`cross_check.py` 會自動偵測下列後端;偵測不到就跳過並在 `error` 給安裝提示。
新增後端只需在腳本的 `BACKENDS` 清單加一筆 `{name, detect, run, note}`。

> **後端安裝都是選用的。** 交叉檢核是給結論加的「第二意見」,不是必要功能——
> 一個後端都沒裝也能正常使用其他功能(此時就以 Claude 自評為準)。想用又不想碰雲端,
> 只裝免費離線的 `ollama` 即可;`codex`/`gemini` 可完全不裝。

## ⚠️ 安全與風險須知(設 key 前必讀)

1. **絕不要把 API key 貼進任何對話視窗(含 Claude / ChatGPT / Gemini 等聊天框)。**
   貼進去就會被記進對話紀錄,等同外洩,必須立刻到該平台撤銷重發。key 只該進你本機的
   `~/.zshrc`。同理也別把 key 寫進會被 commit 的檔案。
2. **隱私分級**:`ollama` 完全離線、不外送任何素材,隱私最佳,適合敏感內容;
   `codex`(OpenAI)、`gemini`(Google)會把你的**素材上傳到對方伺服器**——
   檢核機密/未發表內容前先想清楚。
3. **計費風險**:`codex`/`gemini` 走雲端 API,多半**按 token 計費**(gemini 有免費額度但有上限)。
   交叉檢核**可指定要用哪些後端**(`--backends`);若不指定才會送給所有可用後端,後端越多、單次成本越高。
   由 skill 驅動時預設只用離線的 `ollama`、動用雲端前會先徵得同意;在意花費就 `--backends ollama` 只跑本機。
4. **設定後要讓它生效**:key 寫進 `~/.zshrc` 後,**重啟 Claude Code**(或新開 shell `source ~/.zshrc`)
   才會被讀到;否則 `--list` 仍顯示 unavailable。

### 安全地把 key 寫進 ~/.zshrc(避免兩個常見坑)

手打 `read -s ... >> ~/.zshrc` 容易踩雷:**貼上失敗寫出空值**(`export X=` 後面空白)、
或**重複設定堆出多行**。建議用一支防呆小腳本:隱藏輸入、擋空值、自動去重舊行、寫完遮罩確認。
本 skill 附帶的 `scripts/set-api-key.sh` 即為此用,用法(路徑依 skill 實際位置):

```bash
zsh ~/.claude/skills/cross-ai-check/scripts/set-api-key.sh GEMINI_API_KEY   # 提示→貼 key→Enter→✅ 已寫入
zsh ~/.claude/skills/cross-ai-check/scripts/set-api-key.sh OPENAI_API_KEY
```

驗證是否寫入(不洩漏內容,只看長度與開頭):
```bash
grep '^export GEMINI_API_KEY=' ~/.zshrc | sed 's/=.*/=<已設定>/'
```

## ollama(本機,預設可用)
- 免 API key、免費、離線。
- 服務:`ollama serve`(背景常駐);模型:`ollama pull qwen2.5:7b`。
- 環境變數:
  - `OLLAMA_HOST`(預設 `http://localhost:11434`)
  - `CROSS_CHECK_OLLAMA_MODEL`(預設 `qwen2.5:7b`)— 換更大的模型可提升檢核品質。
- 腳本走 HTTP API(`/api/generate`, `stream:false`),回乾淨 JSON,不夾終端控制碼。

## codex(OpenAI Codex CLI)
- 安裝:`npm i -g @openai/codex`
- 設定:`export OPENAI_API_KEY=sk-...`(用上面的 `scripts/set-api-key.sh` 寫進 `~/.zshrc`)。
  key 從 https://platform.openai.com/api-keys 製作,**帳號需先綁付款方式**,否則呼叫會回 quota 錯誤。
- 腳本用非互動模式 `codex exec "<prompt>"`,避免卡在互動 REPL。
- 偵測條件:`which codex` **且**環境有 `OPENAI_API_KEY`(兩者缺一就 unavailable)。
- ⚠️ 按 token 計費,留意用量。

## gemini(Google Gemini CLI)
- 安裝:`npm i -g @google/gemini-cli`
- 設定:`export GEMINI_API_KEY=...`(用 `scripts/set-api-key.sh`;key 從 https://aistudio.google.com/apikey 製作,有免費額度)。
  或改用 `gemini` 互動式 **Google 帳號 OAuth 登入**(免 key,憑證存 `~/.gemini/`)。
- 腳本用 `gemini -p "<prompt>"`。
- 偵測條件:**只看** `which gemini`——所以 `--list` 可能顯示 available,但**執行時仍需 key 或已登入**,
  否則該筆會在 `error` 報認證失敗。裝了 CLI ≠ 設好 key,兩件事都要做。
- ⚠️ **目錄信任坑**:`gemini` 在「未受信任的目錄」會拒跑非互動模式(報 *not running in a trusted directory*)。
  `cross_check.py` 的 `_gemini_run` 已自動帶 `GEMINI_CLI_TRUST_WORKSPACE=true` 放行;若你自行呼叫 `gemini -p`
  遇到此錯,加這個環境變數或 `--skip-trust` 即可。

## 自訂後端範例(自架 / 其他 API)
在 `BACKENDS` 加:
```python
def _myapi_detect():
    return bool(os.environ.get("MYAPI_KEY"))

def _myapi_run(prompt, system):
    full = f"{system}\n\n{prompt}" if system else prompt
    # ... 發 HTTP 請求,回傳純文字 ...
    return text

BACKENDS.append({
    "name": "myapi",
    "detect": _myapi_detect,
    "run": _myapi_run,
    "note": "未設定 MYAPI_KEY。",
})
```

## 設計備註
- 一律走**非互動 / 一次性**模式(API 或 `exec`/`-p`),不要進互動 REPL,否則腳本會卡住。
- 各後端互相獨立、容錯隔離:一個失敗只標記該筆,不影響其他。
- timeout 統一 300 秒;本機大模型較慢時可自行調整 `run()` 內的 `timeout`。
