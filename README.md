# TestRail Test Case Converter

將 TestRail 匯出的 XML 檔案轉換並上傳至 Lark 多維表格的工具。

## 功能特色

- 支援 TestRail XML 檔案的階層式 section/sub-section 結構解析
- 自動轉換 Ticket Number 格式（支援 `TCG-93178` 和 `TCG93178` 兩種格式）
- 清理 Markdown 格式內容（移除 `**` 強調、連結等）
- 批次上傳至 Lark 多維表格
- 支援單檔案或目錄批次處理
- 提供乾運行模式進行測試

## 安裝需求

```bash
pip install requests pyyaml
```

## 配置設定

創建 `config.yaml` 檔案：

```yaml
lark_base:
  app_id: "your_app_id"
  app_secret: "your_app_secret"
```

## 使用方法

### 基本使用

```bash
# 轉換單個檔案
python convert_testrail_to_lark.py --input "test.xml" --table-url "https://xxx.larksuite.com/base/Q4XxwaS2Cif80DkAku9lMKuAgof?table=tblkN8BxqYwxjc3S"

# 轉換目錄中的所有 XML 檔案
python convert_testrail_to_lark.py --input "./xml_files/" --table-url "https://xxx.larksuite.com/base/Q4XxwaS2Cif80DkAku9lMKuAgof?table=tblkN8BxqYwxjc3S"
```

### 乾運行模式

```bash
# 只進行轉換測試，不實際上傳
python convert_testrail_to_lark.py --input "test.xml" --table-url "https://xxx.larksuite.com/base/Q4XxwaS2Cif80DkAku9lMKuAgof?table=tblkN8BxqYwxjc3S" --dry-run
```

### 詳細日誌

```bash
# 顯示詳細日誌
python convert_testrail_to_lark.py --input "test.xml" --table-url "https://xxx.larksuite.com/base/Q4XxwaS2Cif80DkAku9lMKuAgof?table=tblkN8BxqYwxjc3S" --verbose
```

## 參數說明

- `--input`, `-i`: 輸入檔案路徑（單個 XML 檔案）或目錄路徑（包含 XML 檔案的目錄）
- `--table-url`, `-t`: Lark 表格 URL（包含 wiki_token 和 table_id）
- `--config`, `-c`: 配置檔案路徑（預設: config.yaml）
- `--dry-run`, `-d`: 乾運行模式，只進行轉換測試，不實際上傳
- `--verbose`, `-v`: 顯示詳細日誌

## Lark 表格 URL 格式

Lark 表格 URL 格式如下：
```
https://xxx.larksuite.com/base/{wiki_token}?table={table_id}&view={view_id}
```

範例：
```
https://xxx.larksuite.com/base/Q4XxwaS2Cif80DkAku9lMKuAgof?table=tblkN8BxqYwxjc3S&view=vewJHSwJVd
```

## 欄位對應

| TestRail 欄位 | Lark 欄位 | 轉換說明 |
|---|---|---|
| title | Ticket Number | 提取 Ticket Number 格式：{單號}-{第一層編號}-{第二層編號} |
| title | Title | 提取描述部分 |
| priority | Priority | 優先級轉換 |
| preconds | Precondition | 前置條件，清理 Markdown 格式 |
| steps | Steps | 測試步驟，清理 Markdown 格式 |
| expected | Expected Result | 預期結果，清理 Markdown 格式 |

## 日誌檔案

執行過程中會自動生成 `convert_testrail_to_lark.log` 日誌檔案，記錄詳細的執行過程。

## 專案結構

```
testrail_test_case_converter/
├── convert_testrail_to_lark.py      # 主要轉換腳本
├── config.yaml                      # 配置檔案
├── src/
│   ├── models/
│   │   ├── testrail_models.py      # TestRail 資料模型
│   │   ├── lark_field_mapping.py   # Lark 欄位對應處理
│   │   └── lark_client.py          # Lark API 客戶端
│   └── parser/
│       └── xml_parser.py           # TestRail XML 解析器
├── tools/
│   └── testrail_converter.py       # 命令列工具
└── tests/                          # 測試檔案
```

## 開發工具

- `test_convert_and_upload.py`: 測試轉換並上傳功能
- `test_ticket_number_format.py`: 測試 Ticket Number 格式處理
- `tools/testrail_converter.py`: 命令列工具，支援多種輸出格式

## 故障排除

1. **配置檔案錯誤**：確保 `config.yaml` 檔案存在且包含正確的 Lark app_id 和 app_secret
2. **表格 URL 解析失敗**：檢查 Lark 表格 URL 格式是否正確
3. **欄位不匹配**：確保 Lark 表格包含所有必要欄位
4. **網路連接問題**：檢查網路連接和 Lark API 訪問權限

## 注意事項

- 確保 Lark 應用程式有權限存取目標多維表格
- 建議先使用 `--dry-run` 模式測試轉換結果
- 大批次上傳可能需要較長時間，請耐心等待
- 日誌檔案會記錄詳細的執行過程，便於故障排除