# TestRail 測試案例轉換器工具

## 概述

這個工具可以將 TestRail 匯出的 XML 檔案轉換為多種格式，包括 TXT、Markdown、樹狀圖等。

## 功能特色

- ✅ **階層式解析**：正確處理 TestRail 的 section/sub-section 巢狀結構
- ✅ **多格式輸出**：支援 TXT、Markdown、樹狀圖等格式
- ✅ **視覺化呈現**：生成美觀的 ASCII 樹狀圖
- ✅ **詳細資訊**：可選擇包含或排除測試案例詳情
- ✅ **批次處理**：支援同時處理多個檔案

## 使用方法

### 基本用法

```bash
# 轉換單個檔案為 TXT 和 Markdown 格式
python tools/testrail_converter.py input.xml -o output/

# 指定輸出格式
python tools/testrail_converter.py input.xml -o output/ -f txt md tree

# 包含詳細資訊
python tools/testrail_converter.py input.xml -o output/ -f txt md --details

# 處理多個檔案
python tools/testrail_converter.py file1.xml file2.xml -o output/ -f txt md tree
```

### 參數說明

- `input_files`：TestRail XML 檔案路徑（可指定多個）
- `-o, --output`：輸出目錄（預設：output）
- `-f, --format`：輸出格式選項
  - `txt`：純文字格式
  - `md` 或 `markdown`：Markdown 格式
  - `tree`：樹狀圖格式
  - `detailed_tree`：詳細樹狀圖格式
- `--details`：包含詳細的測試案例資訊
- `--no-details`：不包含詳細的測試案例資訊
- `-v, --verbose`：詳細輸出模式

### 輸出格式說明

#### 1. TXT 格式 (.txt)
- 純文字格式的報告
- 包含套件資訊、結構概覽、統計資訊
- 可選擇包含詳細的測試案例資訊

#### 2. Markdown 格式 (.md)
- Markdown 格式的報告
- 包含表格化的統計資訊
- 支援在 GitHub、GitLab 等平台預覽

#### 3. 樹狀圖格式 (_tree.txt)
- ASCII 樹狀圖視覺化
- 使用表情符號區分不同層級
- 顯示測試案例數量統計

#### 4. 詳細樹狀圖格式 (_detailed_tree.txt)
- 包含更多詳細資訊的樹狀圖
- 顯示層級標示和描述資訊
- 適合深入分析結構

## 使用範例

### 範例 1：基本轉換
```bash
python tools/testrail_converter.py "TP-3153 Associated Users Phase 2.xml" -o output
```

這會產生：
- `output/TP-3153_Associated_Users_Phase_2_S360.txt`
- `output/TP-3153_Associated_Users_Phase_2_S360.md`
- `output/TP-3153_Associated_Users_Phase_2_S360_tree.txt`

### 範例 2：包含詳細資訊
```bash
python tools/testrail_converter.py "TP-3153 Associated Users Phase 2.xml" -o output --details
```

### 範例 3：只生成樹狀圖
```bash
python tools/testrail_converter.py "TP-3153 Associated Users Phase 2.xml" -o output -f tree detailed_tree
```

### 範例 4：批次處理
```bash
python tools/testrail_converter.py *.xml -o output -f txt md tree
```

## 輸出檔案命名

輸出檔案會自動根據套件名稱和 ID 命名：
- 格式：`{套件名稱}_{套件ID}.{副檔名}`
- 特殊字符會被替換為底線
- 範例：`TP-3153_Associated_Users_Phase_2_S360.txt`

## 系統需求

- Python 3.6+
- 無需額外依賴套件（使用 Python 標準庫）

## 注意事項

1. 確保輸入的 XML 檔案是有效的 TestRail 匯出格式
2. 輸出目錄會自動建立（如果不存在）
3. 如果輸出檔案已存在，會被覆蓋
4. 建議使用 `-v` 參數查看詳細處理過程

## 錯誤排除

### 常見問題

1. **ImportError**：確保從正確的目錄執行命令
2. **檔案不存在**：檢查 XML 檔案路徑是否正確
3. **解析錯誤**：確認 XML 檔案格式正確且完整
4. **權限錯誤**：確保對輸出目錄有寫入權限

### 查看詳細錯誤資訊
```bash
python tools/testrail_converter.py input.xml -o output -v
```