# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 專案目的

TestRail 測試案例轉換器，主要功能包含：

1. **XML 解析引擎**：解析 TestRail 匯出的測試案例 XML 結構，包含 Section、sub-section、各測試案例欄位
2. **模組化設計**：將解析演算法和邏輯獨立成可重用模組，支援獨立運作並轉換成 XLSX 格式
3. **視覺化呈現**：將解析結果繪製成樹狀圖，便於結構化檢視
4. **後端整合**：與 Lark 多維表格連結，將解析結果寫入指定資料表

## 核心架構設計

### 主要模組
- **Parser Module**：XML 解析核心，處理 TestRail 格式
- **Data Model**：統一的資料結構定義
- **Export Module**：支援多種輸出格式（XLSX、樹狀圖等）
- **Integration Module**：Lark API 整合

### 資料流程
1. XML 輸入 → Parser → 標準化資料結構
2. 資料結構 → Export Module → 多種輸出格式
3. 資料結構 → Integration Module → Lark 多維表格

## TestRail XML 結構分析

基於現有檔案的結構：
- `<suite>` - 測試套件根節點（包含 id, name, description）
- `<sections>` - 階層式區段組織（可巢狀）
- `<cases>` - 測試案例定義，包含：
  - 基本屬性：id, title, template, type, priority
  - 自定義欄位：preconds（前置條件）, steps（測試步驟）, expected（預期結果）
  - 其他欄位：estimate, references

## 開發規範

### 檔案組織
```
src/
├── parser/          # XML 解析模組
├── models/          # 資料模型定義
├── exporters/       # 輸出格式處理
├── integrations/    # 第三方整合（Lark）
└── utils/           # 共用工具
```

### 模組設計原則
- 每個模組獨立可測試
- 清楚的介面定義
- 支援管道式處理（pipeline）
- 錯誤處理和日誌記錄

## 輸出格式需求

### XLSX 格式
- 保持階層結構的可讀性
- 包含所有測試案例欄位
- 支援篩選和排序

### 樹狀圖
- 視覺化 Section 階層
- 測試案例數量統計
- 互動式導航

### Lark 多維表格
- 對應欄位映射
- 批次寫入機制
- 錯誤處理和重試邏輯