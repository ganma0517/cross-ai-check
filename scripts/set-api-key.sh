#!/bin/zsh
# 安全設定 API key 到 ~/.zshrc 的小工具（cross-ai-check skill 附帶）
# 用法：zsh <skill 路徑>/scripts/set-api-key.sh GEMINI_API_KEY
#   例：zsh ~/.claude/skills/cross-ai-check/scripts/set-api-key.sh OPENAI_API_KEY
# 特性：隱藏輸入(-s)、不進 history、拒收空值、自動去重舊行、寫入後遮罩確認。

set -e
VAR="$1"
RC="$HOME/.zshrc"

if [[ -z "$VAR" ]]; then
  echo "用法：zsh <skill>/scripts/set-api-key.sh <變數名稱>"
  echo "例： zsh ~/.claude/skills/cross-ai-check/scripts/set-api-key.sh GEMINI_API_KEY"
  exit 1
fi

# 1. 隱藏輸入讀 key
print -n "貼上 $VAR 的值後按 Enter（畫面不會顯示）: "
read -s K
echo

# 2. 拒收空值
if [[ -z "$K" ]]; then
  echo "❌ 沒有讀到任何內容，未寫入。請確認剪貼簿有 key 再重跑。"
  exit 1
fi

# 3. 去除該變數所有舊行（含空值殘行），避免重複
if [[ -f "$RC" ]]; then
  sed -i '' "/^export ${VAR}=/d" "$RC"
fi

# 4. 寫入新行
print "export ${VAR}=${K}" >> "$RC"

# 5. 遮罩確認
LEN=${#K}
HEAD=${K:0:4}
unset K
echo "✅ 已寫入 $VAR（長度 ${LEN}，開頭 ${HEAD}…），且已清掉重複行。"
echo "   生效：重啟 Claude Code，或在 shell 跑 source ~/.zshrc"
