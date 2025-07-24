# TestRail 轉換器技術規格書 (Technical Specification)

## 1. 實作方向

### 1.1 專案目標
開發一個簡潔高效的 CLI 工具，專注於 TestRail XML 到 Lark 多維表格的資料轉換功能。

### 1.2 開發原則
- **最小化實作**：只實作核心轉換功能，避免不必要的複雜性
- **模組分離**：各功能模組負責最核心部分，邏輯由主程式協調
- **測試驅動**：遵循 TDD 開發流程，確保程式碼品質
- **中文化**：所有使用者介面、錯誤訊息、文件使用中文

## 2. 技術選型

### 2.1 核心技術棧
- **程式語言**：Python 3.8+
- **CLI 框架**：click（提供互動式選單和參數處理）
- **XML 解析**：xml.etree.ElementTree（Python 標準庫）
- **HTTP 請求**：requests（與現有 lark_client 保持一致）
- **設定管理**：PyYAML（環境設定和參數管理）

### 2.2 依賴套件清單
```python
# 核心依賴
click>=8.0.0           # CLI 框架
requests>=2.28.0       # HTTP 請求（與現有專案一致）
PyYAML>=6.0           # 設定檔處理
colorama>=0.4.4       # 終端顏色支援（跨平台）

# 開發與測試依賴
pytest>=7.0.0         # 單元測試框架
pytest-cov>=4.0.0     # 測試覆蓋率
pytest-mock>=3.10.0   # Mock 測試工具
```

### 2.3 現有資源利用
- **Lark Client 基礎**：基於 `/Users/hideman/code/jira_sync_v3/lark_client.py` 進行精簡
- **保留功能**：認證管理、批次操作、Rate Limit 處理
- **移除功能**：用戶管理、複雜查詢、統計功能

## 3. 程式架構設計

### 3.1 專案結構
```
testrail_converter/
├── src/
│   ├── __init__.py
│   ├── main.py                    # 主程式入口
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── interface.py           # CLI 互動介面
│   │   └── config.py              # 設定管理
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── xml_parser.py          # TestRail XML 解析
│   │   └── data_cleaner.py        # 資料清理模組
│   ├── lark/
│   │   ├── __init__.py
│   │   ├── client.py              # Lark API 客戶端（精簡版）
│   │   └── formatter.py          # Lark 格式轉換
│   └── utils/
│       ├── __init__.py
│       ├── logger.py              # 日誌管理
│       └── validators.py         # 資料驗證
├── tests/
│   ├── unit/
│   │   ├── test_xml_parser.py
│   │   ├── test_data_cleaner.py
│   │   ├── test_lark_client.py
│   │   └── test_formatter.py
│   └── integration/
│       └── test_end_to_end.py
├── config/
│   ├── config.yaml.example       # 設定檔範本
│   └── logging.yaml              # 日誌設定
├── temp/                         # 臨時檔案目錄
├── test_output/                  # 測試輸出目錄
├── requirements.txt
├── setup.py
└── README.md
```

### 3.2 核心模組設計

#### 3.2.1 XML 解析器 (xml_parser.py)
```python
class TestRailXMLParser:
    """TestRail XML 檔案解析器"""
    
    def parse_xml_file(self, file_path: str) -> List[Dict[str, Any]]
    def extract_test_cases(self, xml_root) -> List[Dict[str, Any]]
    def validate_xml_structure(self, xml_root) -> bool
```

#### 3.2.2 資料清理器 (data_cleaner.py)
```python
class TestCaseDataCleaner:
    """測試案例資料清理器"""
    
    def extract_test_case_number_and_title(self, title: str) -> Tuple[str, str]
    def fix_missing_hyphen(self, case_number: str) -> str
    def clean_markdown_content(self, content: str) -> str
    def extract_url_description(self, url_content: str) -> str
    def clean_test_case_fields(self, test_case: Dict[str, Any]) -> Dict[str, Any]
```

#### 3.2.3 Lark 客戶端 (client.py)
```python
class SimpleLarkClient:
    """精簡版 Lark API 客戶端"""
    
    def __init__(self, app_id: str, app_secret: str)
    def set_table_info(self, wiki_token: str, table_id: str)
    def batch_create_records(self, records: List[Dict]) -> Tuple[bool, List[str]]
    def test_connection(self) -> bool
```

#### 3.2.4 格式轉換器 (formatter.py)
```python
class LarkDataFormatter:
    """Lark 資料格式轉換器"""
    
    def format_test_case_for_lark(self, test_case: Dict) -> Dict
    def format_priority_field(self, priority: str) -> str
    def validate_required_fields(self, test_case: Dict) -> bool
    def batch_format_records(self, test_cases: List[Dict]) -> List[Dict]
```

#### 3.2.5 CLI 介面 (interface.py)
```python
class InteractiveCLI:
    """互動式命令列介面"""
    
    def show_main_menu(self) -> str
    def get_file_path_input(self) -> str
    def get_lark_config_input(self) -> Dict[str, str]
    def show_progress(self, current: int, total: int)
    def show_results(self, success_count: int, error_count: int)
```

### 3.3 資料流程設計

#### 3.3.1 主要處理流程
```python
def main_conversion_flow():
    # 1. CLI 互動取得參數
    xml_file_path = cli.get_file_path_input()
    lark_config = cli.get_lark_config_input()
    
    # 2. XML 解析
    parser = TestRailXMLParser()
    raw_test_cases = parser.parse_xml_file(xml_file_path)
    
    # 3. 資料清理
    cleaner = TestCaseDataCleaner()
    cleaned_cases = [cleaner.clean_test_case(case) for case in raw_test_cases]
    
    # 4. 格式轉換
    formatter = LarkDataFormatter()
    lark_records = formatter.batch_format_records(cleaned_cases)
    
    # 5. 批次寫入 Lark
    client = SimpleLarkClient(app_id, app_secret)
    client.set_table_info(wiki_token, table_id)
    success, errors = client.batch_create_records(lark_records)
    
    # 6. 結果回報
    cli.show_results(len(success), len(errors))
```

#### 3.3.2 錯誤處理策略
- **XML 解析錯誤**：檔案格式驗證，提供明確錯誤訊息
- **資料清理錯誤**：記錄問題項目，繼續處理其他資料
- **Lark API 錯誤**：重試機制，批次失敗時分割重試
- **網路連接錯誤**：連接測試，提供診斷建議

## 4. 設定管理

### 4.1 設定檔結構 (config.yaml)
```yaml
# Lark API 設定
lark:
  app_id: ${LARK_APP_ID}
  app_secret: ${LARK_APP_SECRET}
  rate_limit:
    max_requests_per_minute: 60
    batch_size: 500
  field_mapping:
    test_case_number: "test_case_number"
    title: "title"
    priority: "priority"  # 單選欄位
    precondition: "precondition"  # 文字欄位
    steps: "steps"  # 文字欄位
    expected_result: "expected_result"  # 文字欄位

# 資料處理設定
processing:
  test_case_number_pattern: "TCG-\\d+\\.\\d+\\.\\d+"
  required_fields:
    - title
    - priority
    - precondition
    - steps
    - expected_result
  
# 日誌設定
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file_path: "logs/converter.log"
```

### 4.2 環境變數管理
```bash
# 必要環境變數
LARK_APP_ID=your_app_id
LARK_APP_SECRET=your_app_secret

# 可選環境變數
LARK_WIKI_TOKEN=default_wiki_token
LARK_TABLE_ID=default_table_id
LOG_LEVEL=INFO
```

## 5. 品質保證

### 5.1 測試策略
- **單元測試**：每個模組 80%+ 測試覆蓋率
- **整合測試**：完整轉換流程測試
- **效能測試**：大檔案處理能力測試
- **錯誤處理測試**：異常情況處理驗證

### 5.2 測試資料準備
```
tests/fixtures/
├── sample_testrail.xml           # 標準測試資料
├── malformed_testrail.xml        # 格式錯誤測試資料
├── large_testrail.xml            # 大檔案效能測試
└── edge_cases_testrail.xml       # 邊界條件測試
```

### 5.3 持續整合檢查
- **程式碼規範**：使用 black, flake8 進行程式碼格式檢查
- **類型檢查**：使用 mypy 進行靜態類型檢查
- **安全檢查**：使用 bandit 進行安全漏洞掃描
- **依賴檢查**：使用 safety 檢查套件安全性

## 6. 版本控制與部署

### 6.1 Git 版本控制策略
- **主分支 (main)**：穩定版本，用於生產環境
- **開發分支**：
  - `feature/xml-parser` - XML 解析功能
  - `feature/data-cleaner` - 資料清理功能
  - `feature/lark-integration` - Lark 整合功能
  - `feature/cli-interface` - CLI 介面功能
- **分支命名規則**：`類型/功能描述`
- **提交訊息**：使用中文，清楚描述變更內容

### 6.2 Git 工作流程
1. **開發階段**：在 feature 分支開發並通過測試
2. **合併前檢查**：確保所有單元測試通過
3. **合併到 main**：使用 Pull Request 進行程式碼審查
4. **標籤管理**：使用語義化版本標籤 (v1.0.0, v1.1.0)

### 6.3 直接執行部署（無需安裝）
- **執行方式**：`python src/main.py` 直接執行
- **依賴管理**：使用 `pip install -r requirements.txt` 安裝依賴
- **環境準備**：
  ```bash
  # 1. Clone 專案
  git clone <repository_url>
  cd testrail_converter
  
  # 2. 設定虛擬環境
  pyenv activate robotdev
  
  # 3. 安裝依賴
  pip install -r requirements.txt
  
  # 4. 設定環境變數
  cp config/config.yaml.example config/config.yaml
  export LARK_APP_ID=your_app_id
  export LARK_APP_SECRET=your_app_secret
  
  # 5. 直接執行
  python src/main.py
  ```

### 6.4 部署檔案結構
```
部署環境/
├── testrail_converter/           # Git clone 的專案目錄
├── config/
│   └── config.yaml              # 實際設定檔（不納入版控）
├── logs/                        # 執行日誌目錄
├── input/                       # XML 檔案存放目錄
└── output/                      # 處理結果存放目錄
```

## 7. 效能指標

### 7.1 處理能力目標
- **檔案大小**：支援最大 100MB XML 檔案
- **記錄數量**：單次處理最多 10,000 筆測試案例
- **處理速度**：1,000 筆/分鐘（包含網路傳輸）
- **記憶體使用**：峰值不超過 200MB

### 7.2 可靠性指標
- **資料準確率**：99.9%+ 格式轉換準確率
- **API 成功率**：98%+ Lark API 呼叫成功率
- **錯誤恢復**：自動重試失敗批次，最多 3 次

## 8. 維護與擴展

### 8.1 日誌記錄
- **操作日誌**：記錄轉換過程和結果
- **錯誤日誌**：詳細記錄異常情況和堆疊追蹤
- **效能日誌**：記錄處理時間和資源使用情況

### 8.2 擴展性考量
- **模組化設計**：便於新增其他資料來源格式
- **插件架構**：支援自定義資料清理規則
- **設定驅動**：透過設定檔調整處理邏輯
- **API 抽象**：便於支援其他目標平台

### 8.3 版本發布流程
1. **功能完成**：feature 分支開發完成並通過測試
2. **整合測試**：合併到 main 分支並執行完整測試
3. **版本標籤**：建立版本標籤並撰寫 Release Notes
4. **部署更新**：使用 `git pull` 更新部署環境
5. **驗證測試**：在部署環境執行驗證測試