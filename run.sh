#!/bin/bash
# TestRail 轉換器啟動腳本

echo "🚀 TestRail 轉換器"
echo "=================="

# 檢查 Python 是否安裝
if ! command -v python &> /dev/null; then
    echo "❌ 錯誤：未找到 Python，請先安裝 Python 3"
    exit 1
fi

# 檢查配置檔案
if [ ! -f "config/config.yaml" ]; then
    echo "⚠️  配置檔案不存在，正在複製範例配置..."
    cp config/config.yaml.example config/config.yaml
    echo "✅ 已建立 config/config.yaml"
    echo "📝 請編輯 config/config.yaml 填入您的 Lark App ID 和 Secret"
    echo ""
fi

# 檢查必要目錄
mkdir -p logs data temp

# 執行程式
if [ $# -eq 0 ]; then
    echo "💡 使用說明："
    echo "   互動模式：./run.sh"
    echo "   轉換模式：./run.sh --xml-file file.xml --wiki-token docXXX --table-id tblXXX"
    echo "   測試模式：./run.sh --mode test --wiki-token docXXX --table-id tblXXX"
    echo ""
    echo "🔧 啟動互動模式..."
    python main.py
else
    echo "🔧 執行轉換..."
    python main.py "$@"
fi