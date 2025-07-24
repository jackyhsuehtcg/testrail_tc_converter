# 模組接口參數文件 (Parameters Documentation)

本文件詳細記錄所有模組的接口、必要參數、呼叫方式等資訊。實作前必須參閱此文件。

## 1. XML 解析器模組 (xml_parser.py)

### 1.1 TestRailXMLParser 類別

#### parse_xml_file(file_path: str) -> List[Dict[str, Any]]
**功能**：解析 TestRail XML 檔案並提取測試案例資料

**必要參數**：
- `file_path` (str): XML 檔案的絕對路徑

**回傳值**：
- `List[Dict[str, Any]]`: 測試案例資料列表，每個字典包含原始 XML 資料

**異常處理**：
- `FileNotFoundError`: 檔案不存在
- `ET.ParseError`: XML 格式錯誤
- `ValueError`: 檔案內容格式不符

**呼叫範例**：
```python
parser = TestRailXMLParser()
test_cases = parser.parse_xml_file("/path/to/testrail.xml")
```

#### extract_test_cases(xml_root: ET.Element) -> List[Dict[str, Any]]
**功能**：從 XML 根元素中提取測試案例清單

**必要參數**：
- `xml_root` (ET.Element): XML 根元素

**回傳值**：
- `List[Dict[str, Any]]`: 提取的測試案例資料，僅包含必要的 5 個欄位

**預期欄位**：
```python
{
    "id": str,           # 測試案例 ID
    "title": str,        # 完整標題（包含 Test Case Number）
    "priority": str,     # 優先級
    "preconds": str,     # 前置條件
    "steps": str,        # 測試步驟
    "expected": str      # 預期結果
}
```

#### validate_xml_structure(xml_root: ET.Element) -> bool
**功能**：驗證 XML 結構是否符合 TestRail 標準格式

**必要參數**：
- `xml_root` (ET.Element): XML 根元素

**回傳值**：
- `bool`: 結構是否有效

## 2. 資料清理器模組 (data_cleaner.py)

### 2.1 TestCaseDataCleaner 類別

#### extract_test_case_number_and_title(title: str) -> Tuple[str, str]
**功能**：從完整標題中提取測試案例編號和純標題

**必要參數**：
- `title` (str): 完整標題，格式為 "TCG-XXX.YYY.ZZZ 標題內容"

**回傳值**：
- `Tuple[str, str]`: (test_case_number, clean_title)

**處理規則**：
- 識別 TCG-XXX.YYY.ZZZ 格式的編號
- 處理缺失 hyphen 的情況（如 TCGXXX.YYY.ZZZ）
- 自動修正為標準格式 TCG-XXX.YYY.ZZZ

**呼叫範例**：
```python
cleaner = TestCaseDataCleaner()
case_number, title = cleaner.extract_test_case_number_and_title(
    "TCG-001.002.003 登入功能測試"
)
# case_number: "TCG-001.002.003"
# title: "登入功能測試"
```

#### fix_missing_hyphen(case_number: str) -> str
**功能**：修正測試案例編號中缺失的 hyphen

**必要參數**：
- `case_number` (str): 可能缺失 hyphen 的測試案例編號

**回傳值**：
- `str`: 修正後的標準格式編號

**處理邏輯**：
- 檢測格式：`TCG\d+\.\d+\.\d+` -> `TCG-\d+\.\d+\.\d+`
- 確保輸出格式為 `TCG-XXX.YYY.ZZZ`

#### clean_markdown_content(content: str) -> str
**功能**：清理內容中的 Markdown 格式

**必要參數**：
- `content` (str): 包含 Markdown 格式的文字內容

**回傳值**：
- `str`: 清理後的純文字內容

**清理規則**：
- 移除 `**粗體**` -> `粗體`
- 移除 `*斜體*` -> `斜體`
- 移除 `` `程式碼` `` -> `程式碼`
- 處理 URL 連結（見下方函數）

#### extract_url_description(url_content: str) -> str
**功能**：從 URL Markdown 格式中提取說明文字

**必要參數**：
- `url_content` (str): 包含 URL 的內容

**回傳值**：
- `str`: 僅保留說明文字的內容

**處理規則**：
- `[說明文字](URL)` -> `說明文字`
- `http://example.com` -> 保持原樣（如無說明文字）

#### clean_test_case_fields(test_case: Dict[str, Any]) -> Dict[str, Any]
**功能**：清理整個測試案例的所有欄位

**必要參數**：
- `test_case` (Dict[str, Any]): 原始測試案例資料

**回傳值**：
- `Dict[str, Any]`: 清理後的測試案例資料

**輸出格式**：
```python
{
    "test_case_number": str,  # 標準格式的測試案例編號
    "title": str,            # 清理後的純標題
    "priority": str,         # 優先級
    "precondition": str,     # 清理後的前置條件
    "steps": str,           # 清理後的測試步驟
    "expected_result": str   # 清理後的預期結果
}
```

## 3. Lark 客戶端模組 (client.py)

### 3.1 SimpleLarkClient 類別

#### __init__(app_id: str, app_secret: str)
**功能**：初始化 Lark 客戶端

**必要參數**：
- `app_id` (str): Lark 應用程式 ID
- `app_secret` (str): Lark 應用程式密鑰

**內部初始化**：
- 認證管理器
- Rate Limit 控制
- 連接狀態管理

#### set_table_info(wiki_token: str, table_id: str) -> bool
**功能**：設定目標資料表資訊

**必要參數**：
- `wiki_token` (str): Lark Wiki Token
- `table_id` (str): 資料表 ID

**回傳值**：
- `bool`: 設定是否成功

**副作用**：
- 驗證 Token 有效性
- 快取資料表連接資訊

#### batch_create_records(records: List[Dict]) -> Tuple[bool, List[str]]
**功能**：批次建立記錄到 Lark 資料表

**必要參數**：
- `records` (List[Dict]): 記錄資料列表，每筆記錄必須包含所有必要欄位

**記錄格式要求**：
```python
{
    "test_case_number": str,  # 必要
    "title": str,            # 必要
    "priority": str,         # 必要，單選欄位值
    "precondition": str,     # 必要
    "steps": str,           # 必要
    "expected_result": str   # 必要
}
```

**回傳值**：
- `Tuple[bool, List[str]]`: (整體成功狀態, 成功建立的記錄 ID 列表)

**限制條件**：
- 單次最多 500 筆記錄
- 自動分批處理
- 遵循 Rate Limit

#### test_connection() -> bool
**功能**：測試與 Lark API 的連接

**回傳值**：
- `bool`: 連接是否正常

## 4. 格式轉換器模組 (formatter.py)

### 4.1 LarkDataFormatter 類別

#### format_test_case_for_lark(test_case: Dict) -> Dict
**功能**：將清理後的測試案例轉換為 Lark 可接受的格式

**必要參數**：
- `test_case` (Dict): 清理後的測試案例資料

**回傳值**：
- `Dict`: Lark 格式的記錄資料

**轉換規則**：
- 確保所有欄位類型正確
- Priority 欄位進行單選值驗證
- 文字欄位進行長度和格式檢查

#### format_priority_field(priority: str) -> str
**功能**：格式化優先級欄位為 Lark 單選欄位可接受的值

**必要參數**：
- `priority` (str): 原始優先級值

**回傳值**：
- `str`: 標準化的優先級值

**標準值對應**：
- `High`, `high`, `HIGH` -> `High`
- `Medium`, `medium`, `MEDIUM` -> `Medium`
- `Low`, `low`, `LOW` -> `Low`
- 其他值 -> `Medium` (預設值)

#### validate_required_fields(test_case: Dict) -> bool
**功能**：驗證測試案例是否包含所有必要欄位

**必要參數**：
- `test_case` (Dict): 測試案例資料

**必要欄位檢查**：
- `test_case_number`: 非空字串
- `title`: 非空字串
- `priority`: 有效的優先級值
- `precondition`: 字串（可為空）
- `steps`: 非空字串
- `expected_result`: 非空字串

**回傳值**：
- `bool`: 是否通過驗證

#### batch_format_records(test_cases: List[Dict]) -> List[Dict]
**功能**：批次格式化多筆測試案例

**必要參數**：
- `test_cases` (List[Dict]): 測試案例列表

**回傳值**：
- `List[Dict]`: 格式化後的記錄列表

**處理流程**：
1. 逐筆驗證必要欄位
2. 格式化每筆記錄
3. 過濾無效記錄
4. 回傳有效記錄列表

## 5. CLI 介面模組 (interface.py)

### 5.1 InteractiveCLI 類別

#### show_main_menu() -> str
**功能**：顯示主選單並取得使用者選擇

**回傳值**：
- `str`: 使用者選擇的選項

**選單選項**：
- `"convert"`: 開始轉換流程
- `"test"`: 測試連接
- `"quit"`: 退出程式

#### get_file_path_input() -> str
**功能**：取得 XML 檔案路徑輸入

**回傳值**：
- `str`: 驗證過的檔案絕對路徑

**驗證規則**：
- 檔案必須存在
- 檔案必須為 .xml 格式
- 檔案大小不超過 100MB

#### get_lark_config_input() -> Dict[str, str]
**功能**：取得 Lark 設定資訊

**回傳值**：
```python
{
    "wiki_token": str,  # Wiki Token
    "table_id": str     # 資料表 ID
}
```

**驗證規則**：
- Wiki Token 格式檢查
- Table ID 格式檢查

#### show_progress(current: int, total: int) -> None
**功能**：顯示處理進度

**必要參數**：
- `current` (int): 目前處理數量
- `total` (int): 總數量

#### show_results(success_count: int, error_count: int) -> None
**功能**：顯示處理結果

**必要參數**：
- `success_count` (int): 成功處理的數量
- `error_count` (int): 錯誤的數量

## 6. 設定管理模組 (config.py)

### 6.1 ConfigManager 類別

#### load_config(config_path: str = None) -> Dict[str, Any]
**功能**：載入設定檔案

**可選參數**：
- `config_path` (str): 設定檔路徑，預設為 `config/config.yaml`

**回傳值**：
- `Dict[str, Any]`: 設定資料

#### get_lark_config() -> Dict[str, Any]
**功能**：取得 Lark API 相關設定

**回傳值**：
```python
{
    "app_id": str,
    "app_secret": str,
    "rate_limit": Dict,
    "field_mapping": Dict
}
```

#### get_processing_config() -> Dict[str, Any]
**功能**：取得資料處理相關設定

**回傳值**：
```python
{
    "test_case_number_pattern": str,
    "required_fields": List[str],
    "batch_processing": Dict
}
```

## 7. 工具函數模組 (utils/)

### 7.1 Logger (logger.py)

#### setup_logger(name: str, config_path: str = None) -> logging.Logger
**功能**：設定並取得 Logger 實例

**必要參數**：
- `name` (str): Logger 名稱

**可選參數**：
- `config_path` (str): 日誌設定檔路徑

### 7.2 Validators (validators.py)

#### validate_file_path(file_path: str) -> bool
**功能**：驗證檔案路徑有效性

#### validate_test_case_number(case_number: str) -> bool
**功能**：驗證測試案例編號格式

#### validate_priority_value(priority: str) -> bool
**功能**：驗證優先級值有效性

## 8. 錯誤處理規範

### 8.1 自訂異常類別

```python
class TestRailParseError(Exception):
    """TestRail XML 解析錯誤"""
    pass

class DataCleaningError(Exception):
    """資料清理錯誤"""
    pass

class LarkAPIError(Exception):
    """Lark API 呼叫錯誤"""
    pass

class ValidationError(Exception):
    """資料驗證錯誤"""
    pass
```

### 8.2 錯誤處理原則

1. **必要參數檢查**：所有 public 方法都必須檢查必要參數
2. **異常捕獲**：適當捕獲和重新拋出異常
3. **日誌記錄**：所有錯誤都必須記錄到日誌
4. **中文錯誤訊息**：所有使用者面向的錯誤訊息使用中文

## 9. 使用範例

### 9.1 完整轉換流程

```python
from xml_parser import TestRailXMLParser
from data_cleaner import TestCaseDataCleaner
from formatter import LarkDataFormatter
from client import SimpleLarkClient

# 1. 解析 XML
parser = TestRailXMLParser()
raw_cases = parser.parse_xml_file("test.xml")

# 2. 清理資料
cleaner = TestCaseDataCleaner()
cleaned_cases = [cleaner.clean_test_case_fields(case) for case in raw_cases]

# 3. 格式轉換
formatter = LarkDataFormatter()
lark_records = formatter.batch_format_records(cleaned_cases)

# 4. 寫入 Lark
client = SimpleLarkClient(app_id, app_secret)
client.set_table_info(wiki_token, table_id)
success, record_ids = client.batch_create_records(lark_records)
```

---

**重要提醒**：
- 實作前必須詳細閱讀對應模組的參數說明
- 所有參數驗證都必須在方法內部進行
- 必要參數不可為 None 或空值
- 所有方法都必須有適當的異常處理
- 遵循 principle.md 的開發規範