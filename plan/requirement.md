# TestRail 轉換器需求規格書 (Requirement Specification)

## 1. 專案概述

### 1.1 專案目標
開發一個命令列工具，將 TestRail 匯出的 XML 格式測試案例轉換並匯入到 Lark 多維表格中。

### 1.2 專案範圍
- 讀取 TestRail 標準 XML 格式檔案
- 資料欄位提取與清理
- 批次寫入 Lark 多維表格
- 提供互動式 CLI 介面

## 2. 功能性需求

### 2.1 資料來源處理
- **輸入格式**：TestRail 匯出的標準 XML 格式檔案
- **支援來源**：單一 XML 檔案讀取

### 2.2 資料欄位提取與處理

#### 2.2.1 必要欄位（僅提取以下 5 個欄位）
- **Title 欄位**：包含 Test Case Number 和 Title 內容
- **Priority 欄位**：測試案例優先級
- **Precondition 欄位**：測試前置條件
- **Steps 欄位**：測試執行步驟
- **Expected Result 欄位**：預期測試結果

#### 2.2.2 Test Case Number 處理
- **格式規範**：TCG-XXX.YYY.ZZZ（XXX、YYY、ZZZ 為數字組合）
- **提取規則**：從 Title 欄位中提取 Test Case Number
- **Title 處理**：提取 Test Case Number 後，剩餘部分作為實際 Title

#### 2.2.3 資料清理規則
- **缺失 Hyphen 處理**：檢測並補正 TCG 與 XXX 之間缺失的 hyphen
- **Hyphen 標準化**：確保輸出的 Test Case Number 格式為 TCG-XXX.YYY.ZZZ
- **Markdown 清理**：移除 markdown 格式標記
- **URL 處理**：若為 URL 格式，僅保留說明文字部分

### 2.3 Lark 整合功能

#### 2.3.1 基礎要求
- 基於現有專案 `/Users/hideman/code/jira_sync_v3/lark_client.py` 進行精簡開發
- 僅實作資料寫入功能，移除其他附加功能
- 遵循 Lark API Rate Limit 限制

#### 2.3.2 欄位對應規則
- **Test Case Number**：從 Title 中提取的測試案例編號
- **Title**：提取 Test Case Number 後的剩餘標題內容
- **Priority**：優先級（單選欄位類型）
- **Precondition**：前置條件（文字欄位類型）
- **Steps**：測試步驟（文字欄位類型）
- **Expected Result**：預期結果（文字欄位類型）

#### 2.3.3 批次處理
- **批次大小限制**：單次更新最多 500 筆資料
- **批次處理**：自動分割大量資料為多個批次進行處理

### 2.4 使用者介面

#### 2.4.1 CLI 介面規格
- **介面類型**：命令列介面 (CLI)
- **互動方式**：選單式互動問答
- **輸入項目**：
  - 來源 XML 檔案路徑
  - 目標 Lark 資料表資訊

#### 2.4.2 使用者體驗
- 提供清楚的操作指引
- 顯示處理進度資訊
- 提供必要的錯誤提示和成功通知

## 3. 非功能性需求

### 3.1 技術規格
- **開發語言**：Python
- **介面類型**：CLI (Command Line Interface)
- **架構原則**：最小化實作，避免不必要功能

### 3.2 效能需求
- 遵循 Lark API Rate Limit
- 支援大量資料的批次處理
- 合理的記憶體使用效率

### 3.3 可靠性需求
- 資料轉換準確性確保
- 錯誤處理和例外狀況管理
- 資料完整性驗證

## 4. 系統整合需求

### 4.1 外部依賴
- **Lark API**：多維表格寫入功能
- **XML 解析**：Python 標準 XML 處理庫

### 4.2 參考實作
- 基於 `/Users/hideman/code/jira_sync_v3/lark_client.py` 進行開發
- 保持與現有 Lark 整合模式的一致性

## 5. 資料流程

### 5.1 主要流程
```
讀取 XML → 取出欄位值並清理 → 轉換為 Lark 格式 → 批次寫入 Lark 資料表
```

### 5.2 詳細步驟
1. **XML 解析**：讀取並解析 TestRail XML 檔案
2. **資料提取**：從 XML 中提取所需欄位
3. **資料清理**：執行格式標準化和清理規則
4. **格式轉換**：轉換為 Lark 多維表格可接受的格式
5. **批次寫入**：分批次寫入 Lark 資料表

## 6. 驗收標準

### 6.1 功能驗收
- [ ] 成功讀取 TestRail XML 檔案
- [ ] 正確提取 5 個必要欄位（Title, Priority, Precondition, Steps, Expected Result）
- [ ] 正確從 Title 中提取 Test Case Number 並清理格式
- [ ] 正確處理 markdown 和 URL 格式
- [ ] 成功批次寫入 Lark 多維表格，遵循欄位類型要求
- [ ] CLI 介面操作順暢

### 6.2 品質驗收
- [ ] 所有功能模組通過單元測試
- [ ] 遵循 principle.md 規定的開發原則
- [ ] 程式碼註解和文件完整
- [ ] 錯誤處理機制完善

## 7. 約束條件

### 7.1 開發約束
- 嚴格遵循 `principle.md` 規定的開發通則
- 採用測試驅動開發 (TDD) 方法
- 使用中文進行開發溝通與文件撰寫

### 7.2 技術約束
- 使用 pyenv + robotdev 虛擬環境
- 遵循模組分離原則
- Git 分支開發流程

### 7.3 安全約束
- 敏感資訊不納入版本控制
- API Token 使用環境變數管理
- 日誌不記錄敏感資訊