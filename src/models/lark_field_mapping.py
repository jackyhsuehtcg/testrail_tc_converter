"""
Lark 多維表格欄位對應配置
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from .testrail_models import TestCase, Priority


@dataclass
class LarkFieldMapping:
    """Lark 欄位對應定義"""
    testrail_field: str
    lark_field: str
    transform_func: Optional[callable] = None
    required: bool = False
    description: str = ""


class LarkFieldProcessor:
    """Lark 欄位處理器"""
    
    def __init__(self):
        self.field_mappings = self._init_field_mappings()
    
    def _init_field_mappings(self) -> List[LarkFieldMapping]:
        """初始化欄位對應"""
        return [
            LarkFieldMapping(
                testrail_field="title",
                lark_field="Ticket Number",
                transform_func=self._extract_ticket_number,
                required=True,
                description="從 title 中提取 Ticket Number 格式：{單號}-{第一層編號}-{第二層編號}"
            ),
            LarkFieldMapping(
                testrail_field="title",
                lark_field="Title",
                transform_func=self._extract_title_description,
                required=True,
                description="從 title 中提取描述部分"
            ),
            LarkFieldMapping(
                testrail_field="priority",
                lark_field="Priority",
                transform_func=self._convert_priority,
                required=True,
                description="優先級轉換"
            ),
            LarkFieldMapping(
                testrail_field="preconds",
                lark_field="Precondition",
                transform_func=self._clean_markdown_text,
                required=False,
                description="前置條件，清理 Markdown 格式"
            ),
            LarkFieldMapping(
                testrail_field="steps",
                lark_field="Steps",
                transform_func=self._clean_markdown_text,
                required=False,
                description="測試步驟，清理 Markdown 格式"
            ),
            LarkFieldMapping(
                testrail_field="expected",
                lark_field="Expected Result",
                transform_func=self._clean_markdown_text,
                required=False,
                description="預期結果，清理 Markdown 格式"
            )
        ]
    
    def _extract_ticket_number(self, title: str) -> str:
        """
        從 title 中提取 Ticket Number
        Pattern: {單號}-{第一層編號}-{第二層編號}
        範例: TCG-93178.010.010 Associated User -> TCG-93178.010.010
        範例: **TCG-93178.010.010 Associated User -> TCG-93178.010.010 (忽略前面的 *)
        範例: TCG93178.010.010 Associated User -> TCG-93178.010.010 (自動加上 hyphen)
        """
        if not title:
            return ""
        
        # 忽略前面的 * 符號，正則表達式匹配 Pattern (包含 hyphen)
        pattern_with_hyphen = r'^\**([A-Z]+-\d+\.\d+\.\d+)'
        match = re.match(pattern_with_hyphen, title)
        
        if match:
            return match.group(1)
        
        # 匹配沒有 hyphen 的格式，並自動加上 hyphen
        pattern_no_hyphen = r'^\**([A-Z]+)(\d+\.\d+\.\d+)'
        match_no_hyphen = re.match(pattern_no_hyphen, title)
        
        if match_no_hyphen:
            prefix = match_no_hyphen.group(1)
            number_part = match_no_hyphen.group(2)
            return f"{prefix}-{number_part}"
        
        # 如果沒有匹配到完整格式，嘗試其他可能的格式
        # 例如：TCG-93178.010 或 **TCG-93178.010
        pattern_alt_with_hyphen = r'^\**([A-Z]+-\d+\.\d+)'
        match_alt = re.match(pattern_alt_with_hyphen, title)
        
        if match_alt:
            return match_alt.group(1)
        
        # 匹配沒有 hyphen 的簡化格式
        pattern_alt_no_hyphen = r'^\**([A-Z]+)(\d+\.\d+)'
        match_alt_no_hyphen = re.match(pattern_alt_no_hyphen, title)
        
        if match_alt_no_hyphen:
            prefix = match_alt_no_hyphen.group(1)
            number_part = match_alt_no_hyphen.group(2)
            return f"{prefix}-{number_part}"
        
        return ""
    
    def _extract_title_description(self, title: str) -> str:
        """
        從 title 中提取描述部分
        範例: TCG-93178.010.010 Associated User - Completely new user -> Associated User - Completely new user
        範例: **TCG-93178.010.010 Associated User - Completely new user -> Associated User - Completely new user (忽略前面的 *)
        範例: TCG93178.010.010 Associated User - Completely new user -> Associated User - Completely new user (支援無 hyphen 格式)
        """
        if not title:
            return ""
        
        # 移除前面的 * 符號和 Ticket Number 部分 (包含 hyphen)
        pattern_with_hyphen = r'^\**[A-Z]+-\d+(?:\.\d+)*\s*(.+)'
        match = re.match(pattern_with_hyphen, title)
        
        if match:
            return match.group(1).strip()
        
        # 移除前面的 * 符號和 Ticket Number 部分 (沒有 hyphen)
        pattern_no_hyphen = r'^\**[A-Z]+\d+(?:\.\d+)*\s*(.+)'
        match_no_hyphen = re.match(pattern_no_hyphen, title)
        
        if match_no_hyphen:
            return match_no_hyphen.group(1).strip()
        
        # 如果沒有匹配到，返回原始 title
        return title
    
    def _convert_priority(self, priority: Priority) -> str:
        """轉換優先級"""
        if isinstance(priority, Priority):
            return priority.value
        return str(priority) if priority else "Medium"
    
    def _clean_markdown_text(self, text: str) -> str:
        """
        清理 Markdown 格式的文字
        - 移除 ** 強調
        - 移除連結，只保留文字
        - 移除圖片連結
        - 保留基本的換行和編號
        """
        if not text:
            return ""
        
        # 移除圖片連結 ![alt](url)
        text = re.sub(r'!\[([^\]]*)\]\([^)]*\)', r'', text)
        
        # 移除一般連結 [text](url)，保留文字
        text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', text)
        
        # 移除粗體 **text**
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        
        # 移除斜體 *text*
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        
        # 移除底線 __text__
        text = re.sub(r'__([^_]+)__', r'\1', text)
        
        # 移除單底線 _text_
        text = re.sub(r'_([^_]+)_', r'\1', text)
        
        # 移除程式碼標記 `code`
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # 移除 HTML 標籤 <tag>content</tag>
        text = re.sub(r'<[^>]+>', '', text)
        
        # 移除 HTML 實體 &gt; -> >
        text = text.replace('&gt;', '>')
        text = text.replace('&lt;', '<')
        text = text.replace('&amp;', '&')
        text = text.replace('&quot;', '"')
        
        # 清理多餘的空白行
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        
        # 清理行首行尾空白
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text.strip()
    
    def convert_test_case_to_lark(self, test_case: TestCase) -> Dict[str, Any]:
        """
        將 TestCase 轉換為 Lark 欄位格式
        """
        lark_data = {}
        
        for mapping in self.field_mappings:
            # 從 TestCase 中獲取源欄位值
            source_value = getattr(test_case, mapping.testrail_field, None)
            
            if source_value is None:
                continue
            
            # 應用轉換函數
            if mapping.transform_func:
                lark_value = mapping.transform_func(source_value)
            else:
                lark_value = source_value
            
            # 設置到 Lark 欄位
            lark_data[mapping.lark_field] = lark_value
        
        # 設置固定的空欄位 - 不傳送特殊類型欄位
        # lark_data["Acceptance Criteria"] = ""  # 雙向連結欄位不傳送
        # lark_data["Attachment"] = ""           # 附件欄位不傳送
        # lark_data["Assignee"] = ""             # 人員欄位不傳送
        # lark_data["Test Result"] = ""          # 選擇欄位不傳送
        # lark_data["TCG"] = ""                  # 雙向連結欄位不傳送
        
        return lark_data
    
    def get_lark_field_names(self) -> List[str]:
        """獲取所有 Lark 欄位名稱"""
        field_names = []
        
        # 映射的欄位
        for mapping in self.field_mappings:
            if mapping.lark_field not in field_names:
                field_names.append(mapping.lark_field)
        
        # 固定的空欄位
        additional_fields = ["Acceptance Criteria", "Attachment", "Assignee", "Test Result", "TCG"]
        for field in additional_fields:
            if field not in field_names:
                field_names.append(field)
        
        return field_names
    
    def validate_ticket_number(self, ticket_number: str) -> bool:
        """驗證 Ticket Number 格式 (必須包含 hyphen)"""
        if not ticket_number:
            return False
        
        # 檢查是否符合 {單號}-{第一層編號}-{第二層編號} 格式 (必須包含 hyphen)
        pattern = r'^[A-Z]+-\d+\.\d+\.\d+$'
        return bool(re.match(pattern, ticket_number))
    
    def get_mapping_summary(self) -> Dict[str, Any]:
        """獲取對應摘要"""
        return {
            "total_fields": len(self.field_mappings),
            "mapped_fields": [
                {
                    "testrail_field": mapping.testrail_field,
                    "lark_field": mapping.lark_field,
                    "required": mapping.required,
                    "description": mapping.description
                }
                for mapping in self.field_mappings
            ],
            "empty_fields": ["Acceptance Criteria", "Attachment", "Assignee", "Test Result", "TCG"],
            "field_order": self.get_lark_field_names()
        }


# 全域處理器實例
lark_processor = LarkFieldProcessor()