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

#### get_parser_stats() -> Dict[str, Any]
**功能**：取得解析器統計資訊和功能特色

**回傳值**：
- `Dict[str, Any]`: 解析器統計資料

**輸出格式**：
```python
{
    "parser_type": "TestRailXMLParser",
    "supported_formats": ["XML"],
    "supported_encodings": ["UTF-8", "UTF-8-SIG"],
    "features": [
        "深層巢狀結構支援",
        "錯誤恢復處理", 
        "特殊字元處理",
        "空欄位處理"
    ]
}
```

#### _find_all_case_elements(xml_root: ET.Element) -> List[ET.Element]
**功能**：遞迴搜尋所有的 case 元素（私有方法）

**必要參數**：
- `xml_root` (ET.Element): 搜尋的根元素

**回傳值**：
- `List[ET.Element]`: 所有找到的 case 元素列表

**實作特色**：
- 使用 XPath 表達式 ".//case" 進行深層搜尋
- 支援任意深度的巢狀結構

#### _extract_single_test_case(case_elem: ET.Element) -> Optional[Dict[str, Any]]
**功能**：從單個 case 元素中提取測試案例資料（私有方法）

**必要參數**：
- `case_elem` (ET.Element): case XML 元素

**回傳值**：
- `Optional[Dict[str, Any]]`: 測試案例資料字典，失敗時返回 None

**提取邏輯**：
- 自動處理缺失的 custom 元素
- 提供預設值避免空值錯誤
- 優雅處理異常情況

#### _get_element_text(parent: ET.Element, tag_name: str, default: str = "") -> str
**功能**：安全取得 XML 元素的文字內容（私有方法）

**必要參數**：
- `parent` (ET.Element): 父元素
- `tag_name` (str): 目標子元素標籤名稱

**可選參數**：
- `default` (str): 找不到元素時的預設值，預設為空字串

**回傳值**：
- `str`: 元素文字內容或預設值

**安全特性**：
- 自動處理 None 值
- 防止 AttributeError 異常
- 支援深層巢狀元素搜尋

## 2. 資料清理器模組 (data_cleaner.py)

### 2.1 TestCaseDataCleaner 類別

#### __init__()
**功能**：初始化資料清理器，設定日誌記錄器和編譯正則表達式模式

**內部初始化**：
- 設定專用日誌記錄器
- 預編譯所有正則表達式模式以提升效能：
  - `_case_number_pattern`: TCG編號識別模式
  - `_hyphen_fix_pattern`: Hyphen修正模式  
  - `_markdown_bold_pattern`: 粗體格式清理
  - `_markdown_italic_pattern`: 斜體格式清理
  - `_markdown_code_pattern`: 程式碼格式清理
  - `_markdown_code_block_pattern`: 程式碼區塊清理
  - `_url_link_pattern`: URL連結處理

**效能最佳化**：
- 正則表達式預編譯避免重複編譯開銷
- 支援大量資料的高效處理

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

#### get_cleaner_stats() -> Dict[str, Any]
**功能**：取得資料清理器統計資訊和功能特色

**回傳值**：
- `Dict[str, Any]`: 清理器統計資料

**輸出格式**：
```python
{
    "cleaner_type": "TestCaseDataCleaner",
    "supported_formats": ["Markdown", "URL Links"],
    "case_number_format": "TCG-XXX.YYY.ZZZ",
    "features": [
        "測試案例編號提取和修正",
        "Markdown格式清理",
        "URL連結說明文字提取", 
        "hyphen自動修正",
        "Unicode和特殊字元支援"
    ]
}
```

## 3. Lark 客戶端模組 (client.py)

### 3.1 架構說明

本模組採用模組化設計，包含以下核心組件：
- `LarkAuthManager`: 負責認證和 Token 管理
- `LarkTableManager`: 負責資料表操作和 Token 轉換
- `LarkRecordManager`: 負責記錄的批次操作
- `SimpleLarkClient`: 統一的客戶端介面

### 3.2 SimpleLarkClient 類別

#### __init__(app_id: str, app_secret: str)
**功能**：初始化 Lark 客戶端

**必要參數**：
- `app_id` (str): Lark 應用程式 ID
- `app_secret` (str): Lark 應用程式密鑰

**內部初始化**：
- 初始化認證管理器 (`LarkAuthManager`)
- 初始化資料表管理器 (`LarkTableManager`)
- 初始化記錄管理器 (`LarkRecordManager`)
- 設定日誌記錄器

**異常處理**：
- `ValueError`: 當 App ID 或 App Secret 為空時

#### set_table_info(wiki_token: str, table_id: str) -> bool
**功能**：設定目標資料表資訊並立即驗證

**必要參數**：
- `wiki_token` (str): Lark Wiki Token
- `table_id` (str): 資料表 ID

**回傳值**：
- `bool`: 設定是否成功

**副作用**：
- 自動解析 Wiki Token 為 Obj Token（透過 `LarkTableManager`）
- 快取 Obj Token 以提升後續操作效能
- 驗證資料表存取權限

**異常處理**：
- `ValueError`: 當參數為空時

#### batch_create_records(records: List[Dict]) -> Tuple[bool, List[str]]
**功能**：批次建立記錄到 Lark 資料表，支援大量資料自動分批處理

**必要參數**：
- `records` (List[Dict]): 記錄資料列表，每筆記錄必須包含所有必要欄位

**記錄格式要求**：
```python
{
    "test_case_number": str,  # 必要，測試案例編號
    "title": str,            # 必要，標題
    "priority": str,         # 必要，優先級
    "precondition": str,     # 必要，前置條件（可為空字串）
    "steps": str,           # 必要，測試步驟
    "expected_result": str   # 必要，預期結果
}
```

**回傳值**：
- `Tuple[bool, List[str]]`: (整體成功狀態, 成功建立的記錄 ID 列表)

**處理特性**：
- 自動格式轉換為 Lark API 格式（英文欄位名稱）
- 單次最多 500 筆記錄，自動分批處理
- 透過 `LarkRecordManager` 進行批次操作
- 完整錯誤恢復和異常處理

**異常處理**：
- `ValueError`: 當未設定資料表資訊或記錄格式錯誤時
- `LarkAPIError`: 當 API 呼叫失敗時

#### test_connection() -> bool
**功能**：測試與 Lark API 的連接狀態

**回傳值**：
- `bool`: 連接是否正常

**測試流程**：
1. 驗證 Access Token 獲取（透過 `LarkAuthManager`）
2. 確認 Obj Token 解析（透過 `LarkTableManager`）
3. 嘗試存取目標資料表欄位資訊
4. 驗證 API 響應和權限

**異常處理**：
- `ValueError`: 當未設定資料表資訊時

### 3.3 內部管理器類別

#### LarkAuthManager
**功能**：負責 Lark API 認證和 Token 管理

**主要方法**：
- `get_tenant_access_token(force_refresh: bool = False) -> Optional[str]`
- `is_token_valid() -> bool`

**特性**：
- 自動快取和過期管理（預設提前 5 分鐘刷新）
- 執行緒安全的 Token 管理
- 智慧重試和錯誤恢復

#### LarkTableManager
**功能**：負責資料表操作和 Token 轉換

**主要方法**：
- `get_obj_token(wiki_token: str) -> Optional[str]`

**特性**：
- 自動快取 Wiki Token 到 Obj Token 的轉換結果
- 使用 Lark Wiki API 進行轉換
- 優雅的錯誤處理

#### LarkRecordManager
**功能**：負責記錄的批次操作

**主要方法**：
- `batch_create_records(obj_token: str, table_id: str, records_data: List[Dict]) -> Tuple[bool, List[str], List[str]]`

**特性**：
- 支援最多 500 筆記錄的批次創建
- 自動分批處理大量資料
- 統一的 HTTP 請求處理

### 3.4 記錄驗證

#### _validate_record_format(record: Dict) -> bool
**功能**：驗證記錄格式是否符合 Lark API 要求

**參數**：
- `record` (Dict): 記錄資料

**回傳值**：
- `bool`: 格式是否有效

**驗證規則**：
- 檢查所有必要欄位存在
- 驗證關鍵欄位非空（test_case_number, title, steps, expected_result）
- 確保資料類型正確

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

#### __init__()
**功能**：初始化 CLI 介面

**內部設定**：
- 檔案大小限制：100MB
- Wiki Token 驗證正則表達式：`^[a-zA-Z0-9]{20,30}$`
- Table ID 驗證正則表達式：`^tbl[a-zA-Z0-9]{10,20}$`
- 日誌記錄器設定

#### show_main_menu() -> str
**功能**：顯示主選單並取得使用者選擇

**回傳值**：
- `str`: 使用者選擇的選項

**選單選項**：
- `"convert"`: 開始轉換流程
- `"test"`: 測試連接
- `"quit"`: 退出程式

**特性**：
- 友善的中文介面設計
- 無效選項自動重試
- 支援 KeyboardInterrupt 優雅退出

#### get_file_path_input() -> str
**功能**：取得 XML 檔案路徑輸入並完整驗證

**回傳值**：
- `str`: 驗證過的檔案絕對路徑

**驗證規則**：
- 檔案必須存在
- 檔案必須為 .xml 格式
- 檔案大小不超過 100MB

**異常處理**：
- `ValidationError`: 當使用者取消操作時
- `OSError`: 檔案存取錯誤時自動重試
- 自動轉換為絕對路徑

#### get_lark_config_input() -> Dict[str, str]
**功能**：取得 Lark 設定資訊並驗證格式

**回傳值**：
```python
{
    "wiki_token": str,  # 驗證過的 Wiki Token
    "table_id": str     # 驗證過的 Table ID
}
```

**驗證規則**：
- Wiki Token 格式：20-30 位英數字符
- Table ID 格式：tbl + 10-20 位英數字符
- 支援輸入重試機制

**異常處理**：
- `ValidationError`: 當使用者取消操作時

#### show_progress(current: int, total: int) -> None
**功能**：顯示動態處理進度條

**必要參數**：
- `current` (int): 目前處理數量
- `total` (int): 總數量

**特性**：
- 動態進度條顯示（30 字符寬度）
- 百分比計算和顯示
- 使用 █ 和 ░ 字符的視覺化進度條
- 即時更新（使用 \r 覆寫）
- 完成時自動換行

#### show_results(success_count: int, error_count: int) -> None
**功能**：顯示詳細的處理結果統計

**必要參數**：
- `success_count` (int): 成功處理的數量
- `error_count` (int): 錯誤的數量

**顯示內容**：
- 成功和錯誤數量統計
- 成功率百分比計算
- 根據結果顯示不同的狀態訊息
- 友善的中文介面設計

#### _get_wiki_token_input() -> str
**功能**：取得 Wiki Token 輸入（私有方法）

**回傳值**：
- `str`: 驗證過的 Wiki Token

**特性**：
- 格式驗證和錯誤提示
- 自動重試機制
- 支援 KeyboardInterrupt

#### _get_table_id_input() -> str
**功能**：取得 Table ID 輸入（私有方法）

**回傳值**：
- `str`: 驗證過的 Table ID

**特性**：
- 格式驗證和錯誤提示
- 自動重試機制
- 支援 KeyboardInterrupt

#### _validate_wiki_token(token: str) -> bool
**功能**：驗證 Wiki Token 格式（私有方法）

**參數**：
- `token` (str): 待驗證的 Wiki Token

**回傳值**：
- `bool`: 格式是否有效

**驗證規則**：
- 20-30 位英數字符
- 無需特定前綴

#### _validate_table_id(table_id: str) -> bool
**功能**：驗證 Table ID 格式（私有方法）

**參數**：
- `table_id` (str): 待驗證的 Table ID

**回傳值**：
- `bool`: 格式是否有效

**驗證規則**：
- 必須以 "tbl" 開頭
- 後接 10-20 位英數字符
- 總長度 13-23 字符

## 6. 設定管理模組 (config_manager.py) ✅ **已完成**

### 6.1 ConfigManager 類別

#### __init__()
**功能**：初始化設定管理器

**內部初始化**：
- 設定專用日誌記錄器
- 預設值配置 (lark, processing, logging 區段)
- 必要區段和欄位定義
- 環境變數映射模式配置

#### load_config(config_path: Optional[str] = None) -> Dict[str, Any]
**功能**：載入設定檔案並整合環境變數

**可選參數**：
- `config_path` (str): 設定檔路徑，預設為 `config/config.yaml`

**回傳值**：
- `Dict[str, Any]`: 完整的設定資料

**處理流程**：
1. 從檔案載入基礎設定
2. 合併預設值
3. 整合環境變數覆蓋
4. 驗證設定完整性
5. 儲存並返回最終設定

**異常處理**：
- `ConfigError`: 當設定載入或驗證失敗時

#### get_lark_config() -> Dict[str, Any]
**功能**：取得 Lark API 相關設定

**回傳值**：
```python
{
    "app_id": str,           # Lark 應用程式 ID
    "app_secret": str,       # Lark 應用程式密鑰
    "rate_limit": {          # API 速率限制設定
        "max_requests": int,
        "window_seconds": int
    },
    "field_mapping": {       # 欄位映射 (英文->中文)
        "test_case_number": str,
        "title": str,
        "priority": str,
        "precondition": str,
        "steps": str,
        "expected_result": str
    }
}
```

**異常處理**：
- `ConfigError`: 當設定未載入時

#### get_processing_config() -> Dict[str, Any]
**功能**：取得資料處理相關設定

**回傳值**：
```python
{
    "test_case_number_pattern": str,    # 測試案例編號正則表達式
    "required_fields": List[str],       # 必要欄位列表
    "batch_processing": {               # 批次處理設定
        "batch_size": int,
        "max_retries": int,
        "retry_delay": float
    }
}
```

**異常處理**：
- `ConfigError`: 當設定未載入時

#### get_logging_config() -> Dict[str, Any]
**功能**：取得日誌相關設定

**回傳值**：
```python
{
    "level": str,      # 日誌級別 (DEBUG, INFO, WARNING, ERROR)
    "format": str,     # 日誌格式字串
    "file": str        # 日誌檔案路徑
}
```

**異常處理**：
- `ConfigError`: 當設定未載入時

#### validate_config(config: Dict[str, Any]) -> bool
**功能**：驗證設定的完整性和正確性

**必要參數**：
- `config` (Dict[str, Any]): 設定資料

**回傳值**：
- `bool`: 驗證是否通過

**驗證規則**：
- 檢查必要區段 (lark, processing)
- 檢查必要欄位 (app_id, app_secret, test_case_number_pattern, required_fields)
- 驗證 Lark 設定格式
- 驗證處理設定格式

**異常處理**：
- `ConfigError`: 當驗證失敗時

#### backup_config() -> Dict[str, Any]
**功能**：備份當前設定

**回傳值**：
- `Dict[str, Any]`: 設定備份

**異常處理**：
- `ConfigError`: 當設定未載入時

#### restore_config(backup: Dict[str, Any])
**功能**：從備份還原設定

**必要參數**：
- `backup` (Dict[str, Any]): 設定備份

#### __str__() -> str
**功能**：字串表示，自動隱藏敏感資訊

**回傳值**：
- `str`: 安全的設定字串表示 (敏感資料已遮罩)

**敏感資料保護**：
- 自動檢測並遮罩包含 "secret", "password", "token", "key" 的欄位
- 遞迴處理巢狀字典和列表結構

### 6.2 環境變數整合功能

#### 支援的環境變數映射模式
```python
LARK_*          -> lark.*
PROCESSING_*    -> processing.*
LOGGING_*       -> logging.*
```

#### 巢狀欄位映射範例
```python
LARK_APP_ID                        -> lark.app_id
LARK_APP_SECRET                    -> lark.app_secret
LARK_RATE_LIMIT_MAX_REQUESTS       -> lark.rate_limit.max_requests
LARK_FIELD_MAPPING_TITLE           -> lark.field_mapping.title
PROCESSING_BATCH_PROCESSING_BATCH_SIZE -> processing.batch_processing.batch_size
LOGGING_LEVEL                      -> logging.level
```

#### 自動類型轉換
- 數字字串 → int/float
- "true"/"false" → boolean
- 其他 → string

### 6.3 ConfigError 異常類別

#### ConfigError(Exception)
**功能**：設定相關錯誤的自訂異常類別

**使用場景**：
- 設定檔案不存在或無法讀取
- YAML 格式錯誤
- 設定驗證失敗
- 權限不足

## 7. 工具函數模組 (utils/) ✅ **已完成**

### 7.1 Logger (logger.py)

#### setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO, format_string: Optional[str] = None, config_path: Optional[str] = None) -> logging.Logger
**功能**：設定並取得 Logger 實例

**必要參數**：
- `name` (str): Logger 名稱

**可選參數**：
- `log_file` (str): 日誌檔案路徑
- `level` (int): 日誌級別，預設為 INFO
- `format_string` (str): 格式字串
- `config_path` (str): 配置檔案路徑

**回傳值**：
- `logging.Logger`: 配置好的 Logger 實例

#### LoggerManager 類別
**功能**：統一管理所有 Logger 實例

**主要方法**：
- `get_logger(name, log_file, level, format_string)`: 取得或創建 Logger
- `set_global_level(level)`: 設定全域日誌級別
- `set_global_format(format_string)`: 設定全域日誌格式
- `cleanup()`: 清理所有 Logger 處理器

#### RotatingLogger 類別
**功能**：帶日誌輪轉功能的 Logger 包裝器

**必要參數**：
- `name` (str): Logger 名稱
- `log_file` (str): 日誌檔案路徑
- `max_bytes` (int): 單個檔案最大大小，預設 10MB
- `backup_count` (int): 備份檔案數量，預設 5
- `level` (int): 日誌級別，預設 INFO

#### TimedRotatingLogger 類別
**功能**：帶時間輪轉功能的 Logger 包裝器

**必要參數**：
- `name` (str): Logger 名稱
- `log_file` (str): 日誌檔案路徑
- `when` (str): 輪轉時間單位，預設 'midnight'
- `interval` (int): 輪轉間隔，預設 1
- `backup_count` (int): 備份檔案數量，預設 30
- `level` (int): 日誌級別，預設 INFO

### 7.2 Validators (validators.py)

#### validate_file_path(file_path: Union[str, Path, None], allowed_extensions: Optional[List[str]] = None, max_size_mb: Optional[float] = None, check_readable: bool = False) -> bool
**功能**：驗證檔案路徑有效性

**必要參數**：
- `file_path` (Union[str, Path, None]): 要驗證的檔案路徑

**可選參數**：
- `allowed_extensions` (List[str]): 允許的副檔名列表
- `max_size_mb` (float): 最大檔案大小（MB）
- `check_readable` (bool): 是否檢查檔案可讀性

**回傳值**：
- `bool`: 檔案路徑是否有效

#### validate_test_case_number(case_number: Union[str, None], pattern: Optional[str] = None, strip_whitespace: bool = True) -> bool
**功能**：驗證測試案例編號格式

**必要參數**：
- `case_number` (Union[str, None]): 測試案例編號

**可選參數**：
- `pattern` (str): 自訂正則表達式模式
- `strip_whitespace` (bool): 是否清理前後空白

**回傳值**：
- `bool`: 編號格式是否有效

#### validate_priority_value(priority: Union[str, None], allowed_values: Optional[List[str]] = None) -> bool
**功能**：驗證優先級值有效性

**必要參數**：
- `priority` (Union[str, None]): 優先級值

**可選參數**：
- `allowed_values` (List[str]): 允許的優先級值列表

**回傳值**：
- `bool`: 優先級值是否有效

#### validate_required_fields(data: Dict[str, Any], required_fields: List[str], allow_empty: bool = False) -> bool
**功能**：驗證必要欄位完整性

**必要參數**：
- `data` (Dict[str, Any]): 要驗證的資料字典
- `required_fields` (List[str]): 必要欄位列表

**可選參數**：
- `allow_empty` (bool): 是否允許空值

**回傳值**：
- `bool`: 所有必要欄位是否都存在且有效

#### validate_email_format(email: Union[str, None]) -> bool
**功能**：驗證電子郵件格式

**必要參數**：
- `email` (Union[str, None]): 電子郵件地址

**回傳值**：
- `bool`: 電子郵件格式是否有效

#### validate_url_format(url: Union[str, None], allowed_schemes: Optional[List[str]] = None) -> bool
**功能**：驗證 URL 格式

**必要參數**：
- `url` (Union[str, None]): URL 地址

**可選參數**：
- `allowed_schemes` (List[str]): 允許的協議列表

**回傳值**：
- `bool`: URL 格式是否有效

#### FieldValidator 類別
**功能**：欄位驗證器，支援自訂規則和批次驗證

**主要方法**：
- `add_rule(name, validator)`: 添加自訂驗證規則
- `validate(value, rules)`: 驗證單個值
- `validate_batch(data, rules)`: 批次驗證多個欄位

**內建規則**：
- `required`: 驗證值不為空
- `string`: 驗證值為字串
- `integer`: 驗證值為整數
- `float`: 驗證值為浮點數
- `email`: 驗證電子郵件格式
- `url`: 驗證 URL 格式
- `min_length:N`: 驗證最小長度
- `max_length:N`: 驗證最大長度
- `min:N`: 驗證最小值
- `max:N`: 驗證最大值

#### ValidationError 異常類別 
**功能**：資料驗證錯誤的自訂異常

**初始化參數**：
- `message` (str): 錯誤訊息
- `field` (Optional[str]): 相關欄位名稱
- `value` (Any): 導致錯誤的值

### 7.3 全域便利函數

#### get_logger_manager() -> LoggerManager
**功能**：取得全域 Logger 管理器實例

#### set_global_log_level(level: int)
**功能**：設定所有 Logger 的全域級別

#### set_global_log_format(format_string: str)
**功能**：設定所有 Logger 的全域格式

#### cleanup_loggers()
**功能**：清理所有 Logger 的處理器

#### add_validation_rule(name: str, validator: Callable[[Any], bool])
**功能**：添加全域驗證規則

#### validate_field(value: Any, rules: List[str]) -> bool
**功能**：使用全域驗證器驗證欄位

#### validate_data(data: Dict[str, Any], rules: Dict[str, List[str]]) -> ValidationResult
**功能**：使用全域驗證器批次驗證資料

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

# 2.1 取得統計資訊（可選）
parser_stats = parser.get_parser_stats()
cleaner_stats = cleaner.get_cleaner_stats()
print(f"解析器類型: {parser_stats['parser_type']}")
print(f"清理器功能: {', '.join(cleaner_stats['features'])}")

# 3. 格式轉換
formatter = LarkDataFormatter()
lark_records = formatter.batch_format_records(cleaned_cases)

# 4. 寫入 Lark
client = SimpleLarkClient(app_id, app_secret)
client.set_table_info(wiki_token, table_id)
success, record_ids = client.batch_create_records(lark_records)
```

### 9.2 使用 CLI 介面的完整轉換流程

```python
from cli.interface import InteractiveCLI
from xml_parser import TestRailXMLParser
from data_cleaner import TestCaseDataCleaner
from formatter import LarkDataFormatter
from client import SimpleLarkClient

# 1. 初始化 CLI 介面
cli = InteractiveCLI()

# 2. 顯示主選單並取得使用者選擇
choice = cli.show_main_menu()

if choice == "convert":
    # 3. 取得檔案路徑輸入
    xml_file_path = cli.get_file_path_input()
    
    # 4. 取得 Lark 設定
    lark_config = cli.get_lark_config_input()
    
    # 5. 解析 XML
    parser = TestRailXMLParser()
    raw_cases = parser.parse_xml_file(xml_file_path)
    
    # 6. 清理和格式化資料
    cleaner = TestCaseDataCleaner()
    formatter = LarkDataFormatter()
    
    cleaned_cases = []
    total_cases = len(raw_cases)
    
    for i, raw_case in enumerate(raw_cases):
        # 顯示處理進度
        cli.show_progress(i, total_cases)
        
        cleaned_case = cleaner.clean_test_case_fields(raw_case)
        cleaned_cases.append(cleaned_case)
    
    # 7. 格式轉換為 Lark 格式
    lark_records = formatter.batch_format_records(cleaned_cases)
    
    # 8. 寫入 Lark
    client = SimpleLarkClient(app_id, app_secret)
    client.set_table_info(lark_config["wiki_token"], lark_config["table_id"])
    success, record_ids = client.batch_create_records(lark_records)
    
    # 9. 顯示結果
    success_count = len(record_ids) if success else 0
    error_count = len(lark_records) - success_count
    cli.show_results(success_count, error_count)

elif choice == "test":
    # 測試連接流程
    lark_config = cli.get_lark_config_input()
    client = SimpleLarkClient(app_id, app_secret)
    client.set_table_info(lark_config["wiki_token"], lark_config["table_id"])
    
    if client.test_connection():
        cli.show_results(1, 0)  # 顯示測試成功
    else:
        cli.show_results(0, 1)  # 顯示測試失敗
```

---

## 10. 已實作模組額外特性

### 10.1 XML解析器額外實作

**私有方法**：
- `_find_all_case_elements()`: 遞迴搜尋所有 case 元素
- `_extract_single_test_case()`: 提取單個測試案例資料
- `_get_element_text()`: 安全取得元素文字內容

**統計功能**：
- `get_parser_stats()`: 提供解析器類型和功能特色資訊

**強化特性**：
- 深層巢狀結構支援
- 錯誤恢復處理
- 特殊字元處理
- 空欄位處理
- 高效能大檔案處理（測試通過638個案例）

### 10.2 資料清理器額外實作

**正則表達式預編譯**：
- 7個預編譯正則表達式模式提升效能
- 支援巢狀Markdown格式處理
- 自動hyphen修正功能

**統計功能**：
- `get_cleaner_stats()`: 提供清理器類型和功能特色資訊

**強化特性**：
- Unicode和多語言字元完整支援
- 優雅降級和錯誤恢復
- 迭代清理確保巢狀格式完全移除
- 高效能批次處理（測試通過638個案例）

### 10.3 格式轉換器額外實作

**核心轉換功能**：
- 完整的資料類型轉換和驗證機制
- 智能優先級標準化（大小寫不敏感）
- 批次處理時的自動錯誤過濾
- 完整的 Unicode 和特殊字符支援

**驗證和錯誤處理**：
- 必要欄位完整性檢查
- 關鍵欄位非空驗證
- ValidationError 自定義異常處理
- 優雅的錯誤恢復和降級

**效能最佳化**：
- 高效能批次處理能力
- 智能記錄過濾和驗證
- 與資料清理器輸出格式完美相容

### 10.4 CLI 介面額外實作

**使用者介面設計**：
- 友善的中文介面和選單系統
- 直觀的操作流程和提示訊息
- 動態進度條和百分比顯示
- 詳細的結果統計和成功率計算

**輸入驗證和處理**：
- 完整的檔案驗證（存在性、格式、大小限制）
- Lark Token 格式驗證（Wiki Token: 20-30位英數字符、Table ID: tbl+10-20位英數字符）
- 正則表達式精確格式檢查
- 輸入重試機制和錯誤恢復

**異常處理和使用者體驗**：
- Robust 的錯誤處理和使用者取消支援
- 支援 KeyboardInterrupt 優雅退出
- ValidationError 異常統一處理
- 自動重試和錯誤提示機制

**測試覆蓋**：
- XML解析器：94% 覆蓋率，30個測試案例
- 資料清理器：92% 覆蓋率，28個測試案例
- Lark 客戶端：91% 覆蓋率，38個單元測試 + 5個整合測試
- 格式轉換器：100% 覆蓋率，27個單元測試 + 7個整合測試
- CLI 介面：87% 覆蓋率，29個單元測試 + 12個整合測試
- 設定管理模組：92% 覆蓋率，23個單元測試 + 9個整合測試
- 整合測試：完整流程測試涵蓋所有模組互動
- 真實資料驗證：TP-3153（107案例）、TP-2726（638案例）

---

**重要提醒**：
- 實作前必須詳細閱讀對應模組的參數說明
- 所有參數驗證都必須在方法內部進行
- 必要參數不可為 None 或空值
- 所有方法都必須有適當的異常處理
- 遵循 principle.md 的開發規範