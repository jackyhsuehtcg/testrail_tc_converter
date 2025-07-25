# TestRail 轉換器配置說明

## 📁 配置檔案結構

```
config/
├── config.yaml.example     # 完整配置範例
├── config.yaml            # 主要配置檔案（需要自行建立）
├── quick-start.yaml        # 快速開始配置
└── README.md              # 本說明檔案

.env.example               # 環境變數配置範例
```

## 🚀 快速開始

### 1. 複製配置檔案
```bash
cp config/config.yaml.example config/config.yaml
```

### 2. 設定 Lark 應用資訊
編輯 `config/config.yaml`，填入您的 Lark 應用資訊：

```yaml
lark:
  app_id: "cli_xxxxxxxxxxxxxxxxx"        # 您的 Lark App ID
  app_secret: "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # 您的 Lark App Secret
```

### 3. 執行轉換
```bash
# 方式一：直接執行
python main.py --config config/config.yaml --xml-file test.xml --wiki-token docXXX --table-id tblXXX

# 方式二：使用啟動腳本
./run.sh --xml-file test.xml --wiki-token docXXX --table-id tblXXX
```

## ⚙️ 配置選項說明

### Lark 配置
```yaml
lark:
  app_id: "your-app-id"              # Lark 應用 ID
  app_secret: "your-app-secret"      # Lark 應用密鑰
  
  field_mapping:                     # 欄位映射配置
    test_case_number: "測試案例編號"  # TestRail 欄位 → Lark 表格欄位
    title: "標題"
    priority: "優先級"
    precondition: "前置條件"
    steps: "測試步驟"
    expected_result: "預期結果"
```

### 處理配置
```yaml
processing:
  test_case_number_pattern: "^TCG-\\d{3}\\.\\d{3}\\.\\d{3}$"  # 測試案例編號格式
  
  batch_processing:
    batch_size: 500                  # 每批次處理的記錄數
    max_retries: 3                   # 最大重試次數
    retry_delay: 1.0                 # 重試延遲（秒）
```

### 日誌配置
```yaml
logging:
  level: INFO                        # DEBUG, INFO, WARNING, ERROR, CRITICAL
  file: "logs/conversion.log"        # 日誌檔案路徑
  max_file_size: 10485760           # 最大檔案大小（10MB）
  backup_count: 5                   # 保留的備份檔案數量
```

## 🔧 環境變數支援

您也可以使用環境變數來覆蓋配置檔案設定：

```bash
# 複製環境變數範例檔案
cp .env.example .env

# 編輯 .env 檔案
LARK_APP_ID=cli_xxxxxxxxxxxxxxxxx
LARK_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 環境變數命名規則
- 配置路徑 `lark.app_id` → 環境變數 `LARK_APP_ID`
- 配置路徑 `processing.batch_processing.batch_size` → 環境變數 `PROCESSING_BATCH_PROCESSING_BATCH_SIZE`

## 📋 配置檔案選項

### 1. 完整配置 (config.yaml)
- 包含所有可用選項
- 適合生產環境使用
- 可細緻調整各項參數

### 2. 快速配置 (quick-start.yaml)
- 最小化配置
- 適合快速測試
- 只包含必要設定

### 3. 環境變數配置 (.env)
- 適合 CI/CD 環境
- 敏感資訊不會寫入檔案
- 覆蓋配置檔案設定

## 🛡️ 安全注意事項

1. **不要將包含真實 App Secret 的配置檔案提交到版本控制**
2. **使用 .env 檔案存放敏感資訊**
3. **確保配置檔案的讀取權限設定正確**

```bash
# 設定配置檔案權限
chmod 600 config/config.yaml
chmod 600 .env
```

## 🔍 配置驗證

執行配置驗證來檢查您的設定：

```bash
python main.py --mode test --config config/config.yaml --wiki-token docXXX --table-id tblXXX
```

## 🚨 常見問題

### Q: App ID 或 App Secret 錯誤
**A:** 檢查 Lark 開發者後台的應用資訊，確保複製正確

### Q: 無法寫入 Lark 表格
**A:** 檢查 Wiki Token 和 Table ID 格式是否正確，以及應用是否有寫入權限

### Q: 日誌檔案無法建立
**A:** 確保 logs 目錄存在且有寫入權限

### Q: 批次處理失敗
**A:** 嘗試減少 batch_size 或增加 retry_delay

## 📚 更多資訊

- [Lark 開發者文件](https://open.larksuite.com/document/)
- [TestRail API 文件](https://www.gurock.com/testrail/docs/api)
- [專案 README.md](../README.md)