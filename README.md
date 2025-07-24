# TestRail 轉換器

將 TestRail XML 格式的測試案例轉換到 Lark 多維表格的命令列工具。

## 專案概述

本工具專門處理從 TestRail 匯出的標準 XML 格式檔案，進行資料清理和格式轉換後，批次匯入到 Lark 多維表格中。

### 主要功能

- ✅ 解析 TestRail XML 格式檔案
- ✅ 自動清理測試案例編號格式 (TCG-XXX.YYY.ZZZ)
- ✅ 處理 Markdown 格式和 URL 連結
- ✅ 批次寫入 Lark 多維表格 (最多 500 筆/次)
- ✅ 互動式 CLI 介面
- ✅ 完整的錯誤處理和日誌記錄

## 系統需求

- Python 3.8 或以上版本
- pyenv + robotdev 虛擬環境
- 網路連接（存取 Lark API）

## 快速開始

### 1. 環境準備

```bash
# Clone 專案
git clone <repository_url>
cd testrail_converter

# 啟動虛擬環境
pyenv activate robotdev

# 安裝依賴套件
pip install -r requirements.txt
```

### 2. 設定配置

```bash
# 複製設定檔範本
cp config/config.yaml.example config/config.yaml

# 設定環境變數
export LARK_APP_ID=your_app_id
export LARK_APP_SECRET=your_app_secret
```

### 3. 執行程式

```bash
# 直接執行主程式
python src/main.py
```

## 專案結構

```
testrail_converter/
├── src/                          # 主程式碼
│   ├── main.py                   # 程式入口
│   ├── cli/                      # CLI 介面模組
│   ├── parsers/                  # XML 解析和資料清理
│   ├── lark/                     # Lark API 整合
│   └── utils/                    # 工具函數
├── tests/                        # 測試套件  
│   ├── unit/                     # 單元測試
│   ├── integration/              # 整合測試
│   └── fixtures/                 # 測試資料
├── config/                       # 設定檔
├── plan/                         # 專案規劃文件
├── logs/                         # 日誌檔案
├── temp/                         # 臨時檔案
└── test_output/                  # 測試輸出
```

## 開發指南

### 測試執行

```bash
# 執行單元測試
pyenv exec python -m pytest tests/unit/ -v

# 執行整合測試
pyenv exec python -m pytest tests/integration/ -v

# 執行所有測試並生成覆蓋率報告
pyenv exec python -m pytest tests/ --cov=src --cov-report=html -v
```

### 程式碼規範

本專案遵循以下開發原則：

- 測試驅動開發 (TDD)
- 中文註解和訊息
- Git 分支開發策略
- 模組化設計

詳細規範請參考 `plan/principle.md`。

## 設定說明

### 環境變數

| 變數名稱 | 說明 | 必要性 |
|---------|------|--------|
| `LARK_APP_ID` | Lark 應用程式 ID | 必要 |
| `LARK_APP_SECRET` | Lark 應用程式密鑰 | 必要 |
| `LARK_WIKI_TOKEN` | 預設 Wiki Token | 可選 |
| `LARK_TABLE_ID` | 預設資料表 ID | 可選 |
| `LOG_LEVEL` | 日誌級別 | 可選 |

### 設定檔

主要設定檔為 `config/config.yaml`，包含：

- Lark API 設定
- 資料處理規則
- 檔案處理設定
- 日誌配置
- CLI 介面設定

## 使用說明

### 基本流程

1. 準備 TestRail XML 檔案
2. 設定 Lark API 認證資訊
3. 執行程式並依照互動式選單操作
4. 選擇來源 XML 檔案
5. 輸入目標 Lark 資料表資訊
6. 等待轉換完成並檢視結果

### 資料格式要求

- **XML 格式**：TestRail 標準匯出格式
- **測試案例編號**：TCG-XXX.YYY.ZZZ 格式（自動修正缺失的 hyphen）
- **檔案大小**：最大支援 100MB
- **記錄數量**：單次最多處理 10,000 筆

## 疑難排解

### 常見問題

1. **認證失敗**：檢查 `LARK_APP_ID` 和 `LARK_APP_SECRET` 環境變數
2. **檔案解析錯誤**：確認 XML 檔案格式符合 TestRail 標準
3. **網路連接問題**：檢查網路連接和防火牆設定
4. **記憶體不足**：減少批次處理大小或分割大檔案

### 日誌檢查

程式執行日誌存放在 `logs/` 目錄：

- `converter.log`：一般操作日誌
- `error.log`：錯誤詳細記錄

## 版本資訊

- **目前版本**：1.0.0
- **Python 版本**：3.8+
- **最後更新**：2024年

## 授權資訊

本專案遵循內部開發規範，僅供內部使用。

## 聯絡資訊

如有問題或建議，請聯繫開發團隊。