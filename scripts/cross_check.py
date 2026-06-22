#!/usr/bin/env python3
"""
cross_check.py — 把同一份「素材 + 檢核問題」送給多個外部 AI 後端,收集各自的獨立回應。

設計目標:
- 獨立性:每個後端只拿到原始素材與問題,拿不到 Claude 的結論,避免 anchoring。
- 容錯:某個後端沒裝 / 沒設好 key / 連線失敗,就標成 unavailable 並跳過,不讓整批失敗。
- 可擴充:新增一個後端 = 在 BACKENDS 加一筆設定,SKILL.md 與呼叫端不必改。

用法:
  cross_check.py --prompt-file material.md                 # 用所有可用後端
  cross_check.py --prompt "請檢視這段邏輯..."               # 直接給字串
  cross_check.py --prompt-file m.md --backends ollama       # 指定後端(逗號分隔)
  cross_check.py --list                                     # 只列出後端可用狀態
  cross_check.py --prompt-file m.md --system "你是嚴格的 code reviewer"

輸出:stdout 一份 JSON
  {"backends":[{"name","available","ok","response","error","duration_s"}, ...]}
"""
import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
import urllib.error

# usage cache：cross_check.py 把各後端 token 用量累計寫進這裡，供 statusline 讀取。
USAGE_CACHE = os.path.expanduser("~/.claude/.crossai-usage.json")
USAGE_KEEP_DAYS = 7

# CLI 後端（codex/gemini）若有印 token，常見樣式;抓不到再 fallback 估算。
_TOK_PATTERNS = [
    re.compile(r"tokens?\s*used[:\s]+([\d,]+)", re.I),
    re.compile(r"total[_\s]*tokens?[:\s]+([\d,]+)", re.I),
    re.compile(r"([\d,]+)\s+tokens?\b", re.I),
]


def _estimate_tokens(prompt, response):
    # 粗估:約 4 字元 / token。input=prompt、output=response。
    inp = math.ceil(len(prompt or "") / 4)
    out = math.ceil(len(response or "") / 4)
    return {"input": inp, "output": out, "total": inp + out, "estimated": True}


def _parse_cli_tokens(text):
    # 從 CLI 的 stdout+stderr 嘗試解析 total token;抓不到回 None。
    for pat in _TOK_PATTERNS:
        m = pat.search(text or "")
        if m:
            try:
                return int(m.group(1).replace(",", ""))
            except ValueError:
                continue
    return None

# ---------------------------------------------------------------------------
# 後端定義。每個後端是一個 dict:
#   name        顯示名稱
#   detect()    -> bool,環境是否具備(裝了 CLI / 服務有起來 / 有 key)
#   run(prompt, system) -> str,送出並回傳純文字回應;失敗請 raise
#   note        unavailable 時給使用者的提示(怎麼裝 / 怎麼設)
# 要加新後端(例如 gemini),照樣補一筆即可。
# ---------------------------------------------------------------------------

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("CROSS_CHECK_OLLAMA_MODEL", "qwen2.5:7b")


def _ollama_detect():
    try:
        req = urllib.request.Request(f"{OLLAMA_HOST}/api/tags")
        with urllib.request.urlopen(req, timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def _ollama_run(prompt, system):
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    if system:
        payload["system"] = system
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{OLLAMA_HOST}/api/generate", data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        body = json.load(r)
    text = body.get("response", "").strip()
    inp = body.get("prompt_eval_count")
    out = body.get("eval_count")
    usage = None
    if inp is not None or out is not None:
        inp = inp or 0
        out = out or 0
        usage = {"input": inp, "output": out, "total": inp + out, "estimated": False}
    return text, usage


def _codex_detect():
    # OpenAI Codex CLI:`codex exec` 為非互動一次性模式,需要 OPENAI_API_KEY。
    return bool(shutil.which("codex")) and bool(os.environ.get("OPENAI_API_KEY"))


def _codex_run(prompt, system):
    full = f"{system}\n\n{prompt}" if system else prompt
    proc = subprocess.run(
        ["codex", "exec", full],
        capture_output=True, text=True, timeout=300,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "codex exit != 0")
    text = proc.stdout.strip()
    tot = _parse_cli_tokens(proc.stdout + "\n" + (proc.stderr or ""))
    usage = {"input": 0, "output": 0, "total": tot, "estimated": False} \
        if tot is not None else _estimate_tokens(full, text)
    return text, usage


def _gemini_detect():
    # Google Gemini CLI:`gemini -p`,需 GEMINI_API_KEY 或 gcloud/OAuth 授權。
    # 與 codex 一致:CLI 在還不夠,沒 key/授權 runtime 仍會失敗,故 detect 階段就一併檢查,
    # 避免 --list 顯示 available 但實跑才報錯。
    if not shutil.which("gemini"):
        return False
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return True
    # OAuth/gcloud 授權憑證(gemini-cli 登入後寫於 ~/.gemini/)
    creds = os.path.expanduser("~/.gemini/oauth_creds.json")
    return os.path.exists(creds)


def _gemini_run(prompt, system):
    full = f"{system}\n\n{prompt}" if system else prompt
    # 非互動模式下，gemini 會因「目錄未受信任」拒跑；官方建議用此環境變數放行。
    env = {**os.environ, "GEMINI_CLI_TRUST_WORKSPACE": "true"}
    proc = subprocess.run(
        ["gemini", "-p", full],
        capture_output=True, text=True, timeout=300, env=env,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "gemini exit != 0")
    text = proc.stdout.strip()
    tot = _parse_cli_tokens(proc.stdout + "\n" + (proc.stderr or ""))
    usage = {"input": 0, "output": 0, "total": tot, "estimated": False} \
        if tot is not None else _estimate_tokens(full, text)
    return text, usage


BACKENDS = [
    {
        "name": f"ollama:{OLLAMA_MODEL}",
        "detect": _ollama_detect,
        "run": _ollama_run,
        "note": f"ollama 服務未啟動或無模型。請執行 `ollama serve` 並 `ollama pull {OLLAMA_MODEL}`。",
    },
    {
        "name": "codex",
        "detect": _codex_detect,
        "run": _codex_run,
        "note": "未偵測到 codex CLI 或 OPENAI_API_KEY。安裝:`npm i -g @openai/codex`,並 export OPENAI_API_KEY。",
    },
    {
        "name": "gemini",
        "detect": _gemini_detect,
        "run": _gemini_run,
        "note": "未偵測到 gemini CLI。安裝:`npm i -g @google/gemini-cli`,並設定 GEMINI_API_KEY。",
    },
]


def select(names):
    if not names:
        return BACKENDS
    wanted = {n.strip() for n in names.split(",")}
    out = []
    for b in BACKENDS:
        short = b["name"].split(":")[0]
        if b["name"] in wanted or short in wanted:
            out.append(b)
    return out


def main():
    ap = argparse.ArgumentParser(description="跨 AI 檢核:多後端獨立意見收集器")
    ap.add_argument("--prompt")
    ap.add_argument("--prompt-file")
    ap.add_argument("--system", default="")
    ap.add_argument("--backends", default="", help="逗號分隔;省略=所有可用後端")
    ap.add_argument("--list", action="store_true", help="只列出後端可用狀態")
    args = ap.parse_args()

    chosen = select(args.backends)

    if args.list:
        rows = []
        for b in chosen:
            ok = b["detect"]()
            rows.append({"name": b["name"], "available": ok,
                         "note": None if ok else b["note"]})
        print(json.dumps({"backends": rows}, ensure_ascii=False, indent=2))
        return

    if args.prompt_file:
        with open(args.prompt_file, encoding="utf-8") as f:
            prompt = f.read()
    elif args.prompt:
        prompt = args.prompt
    else:
        ap.error("需要 --prompt 或 --prompt-file")

    results = []
    for b in chosen:
        row = {"name": b["name"], "available": False, "ok": False,
               "response": None, "error": None, "duration_s": None, "usage": None}
        if not b["detect"]():
            row["error"] = b["note"]
            results.append(row)
            continue
        row["available"] = True
        t0 = time.time()
        try:
            text, usage = b["run"](prompt, args.system)
            row["response"] = text
            row["usage"] = usage
            row["ok"] = True
        except Exception as e:
            row["error"] = f"{type(e).__name__}: {e}"
        row["duration_s"] = round(time.time() - t0, 1)
        results.append(row)

    available = [r for r in results if r["available"]]
    print(json.dumps({
        "backends": results,
        "summary": {
            "total": len(results),
            "available": len(available),
            "succeeded": len([r for r in results if r["ok"]]),
        },
    }, ensure_ascii=False, indent=2))

    _record_usage(results)

    if not available:
        sys.exit(3)  # 沒有任何後端可用 → 讓呼叫端知道要提醒使用者


def _record_usage(results):
    """把本次各後端的 token 用量累加進今日 cache(供 statusline 顯示)。
    記帳失敗絕不可中斷主流程,故整段包在 try/except。"""
    try:
        today = time.strftime("%Y-%m-%d")
        try:
            with open(USAGE_CACHE, encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                data = {}
        except Exception:
            data = {}

        day = data.setdefault(today, {})
        for r in results:
            u = r.get("usage")
            if not r.get("ok") or not u or not u.get("total"):
                continue
            short = r["name"].split(":")[0]  # ollama / codex / gemini
            slot = day.setdefault(short, {"input": 0, "output": 0,
                                          "total": 0, "runs": 0, "estimated": False})
            slot["input"] += u.get("input", 0) or 0
            slot["output"] += u.get("output", 0) or 0
            slot["total"] += u.get("total", 0) or 0
            slot["runs"] += 1
            if u.get("estimated"):
                slot["estimated"] = True

        # 修剪:只保留最近 USAGE_KEEP_DAYS 天的日期 key。
        keep = {time.strftime("%Y-%m-%d", time.localtime(time.time() - i * 86400))
                for i in range(USAGE_KEEP_DAYS)}
        data = {k: v for k, v in data.items() if k in keep}

        with open(USAGE_CACHE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass


if __name__ == "__main__":
    main()
