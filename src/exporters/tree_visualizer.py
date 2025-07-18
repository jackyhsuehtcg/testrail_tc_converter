"""
樹狀結構視覺化工具
將 TestRail 解析結果呈現為樹狀圖
"""

import json
from typing import Dict, Any, List
from ..models.testrail_models import TestSuite, Section


class TreeVisualizer:
    """樹狀結構視覺化器"""
    
    def __init__(self):
        self.tree_symbols = {
            'branch': '├── ',
            'last_branch': '└── ',
            'vertical': '│   ',
            'space': '    '
        }
    
    def generate_ascii_tree(self, suite: TestSuite) -> str:
        """
        生成 ASCII 樹狀圖
        
        Args:
            suite: 測試套件
            
        Returns:
            ASCII 樹狀圖字串
        """
        lines = []
        
        # 套件標題
        lines.append(f"📋 {suite.name} (ID: {suite.id})")
        if suite.description:
            lines.append(f"   {suite.description}")
        lines.append(f"   總計: {suite.get_total_cases_count()} 個測試案例")
        lines.append("")
        
        # 處理每個根層級 section
        for i, section in enumerate(suite.sections):
            is_last = i == len(suite.sections) - 1
            section_lines = self._generate_section_tree(section, "", is_last)
            lines.extend(section_lines)
        
        return "\n".join(lines)
    
    def _generate_section_tree(self, section: Section, prefix: str, is_last: bool) -> List[str]:
        """
        遞迴生成 section 的樹狀結構
        
        Args:
            section: 區段
            prefix: 前綴字串
            is_last: 是否為最後一個節點
        """
        lines = []
        
        # 當前節點
        connector = self.tree_symbols['last_branch'] if is_last else self.tree_symbols['branch']
        
        # 依據層級使用不同的圖示
        level_icons = {
            1: '📁',  # 根層級
            2: '📂',  # 第二層
            3: '📄',  # 第三層及以下
        }
        icon = level_icons.get(section.level, '📄')
        
        # 區段資訊
        case_count = section.get_total_cases_count()
        direct_cases = len(section.test_cases)
        
        section_info = f"{icon} {section.name}"
        if case_count > 0:
            if direct_cases > 0 and len(section.subsections) > 0:
                section_info += f" ({direct_cases} 直接案例, 共 {case_count} 案例)"
            else:
                section_info += f" ({case_count} 案例)"
        
        lines.append(f"{prefix}{connector}{section_info}")
        
        # 準備子節點的前綴
        if is_last:
            new_prefix = prefix + self.tree_symbols['space']
        else:
            new_prefix = prefix + self.tree_symbols['vertical']
        
        # 顯示直接的測試案例 (只顯示數量，不展開每個案例)
        if section.test_cases:
            test_case_line = f"🧪 {len(section.test_cases)} 個測試案例"
            if section.subsections:
                lines.append(f"{new_prefix}{self.tree_symbols['branch']}{test_case_line}")
            else:
                lines.append(f"{new_prefix}{self.tree_symbols['last_branch']}{test_case_line}")
        
        # 遞迴處理子區段
        for i, subsection in enumerate(section.subsections):
            is_last_subsection = i == len(section.subsections) - 1
            # 如果有直接的測試案例，子區段就不是最後一個
            if section.test_cases and not is_last_subsection:
                subsection_is_last = False
            else:
                subsection_is_last = is_last_subsection
            
            subsection_lines = self._generate_section_tree(subsection, new_prefix, subsection_is_last)
            lines.extend(subsection_lines)
        
        return lines
    
    def generate_json_tree(self, suite: TestSuite) -> str:
        """
        生成 JSON 格式的樹狀結構
        
        Args:
            suite: 測試套件
            
        Returns:
            JSON 字串
        """
        tree_data = suite.get_tree_structure()
        return json.dumps(tree_data, ensure_ascii=False, indent=2)
    
    def generate_detailed_tree(self, suite: TestSuite, show_test_cases: bool = True) -> str:
        """
        生成詳細的樹狀結構，可選擇是否顯示測試案例詳情
        
        Args:
            suite: 測試套件
            show_test_cases: 是否顯示測試案例詳情
            
        Returns:
            詳細樹狀圖字串
        """
        lines = []
        
        # 套件標題
        lines.append(f"📋 TestRail 測試套件: {suite.name}")
        lines.append(f"   ID: {suite.id}")
        if suite.description:
            lines.append(f"   描述: {suite.description}")
        lines.append(f"   總計: {suite.get_total_cases_count()} 個測試案例")
        lines.append("=" * 60)
        lines.append("")
        
        # 處理每個根層級 section
        for i, section in enumerate(suite.sections):
            is_last = i == len(suite.sections) - 1
            section_lines = self._generate_detailed_section_tree(
                section, "", is_last, show_test_cases
            )
            lines.extend(section_lines)
        
        return "\n".join(lines)
    
    def _generate_detailed_section_tree(self, section: Section, prefix: str, 
                                      is_last: bool, show_test_cases: bool) -> List[str]:
        """生成詳細的區段樹狀結構"""
        lines = []
        
        # 當前節點
        connector = self.tree_symbols['last_branch'] if is_last else self.tree_symbols['branch']
        
        # 層級標示
        level_prefix = "  " * (section.level - 1)
        level_indicator = f"[Level {section.level}]"
        
        # 區段資訊
        case_count = section.get_total_cases_count()
        direct_cases = len(section.test_cases)
        
        section_header = f"{prefix}{connector}📁 {section.name} {level_indicator}"
        lines.append(section_header)
        
        if section.description:
            new_prefix = prefix + (self.tree_symbols['space'] if is_last else self.tree_symbols['vertical'])
            lines.append(f"{new_prefix}   描述: {section.description}")
        
        # 準備子節點的前綴
        if is_last:
            new_prefix = prefix + self.tree_symbols['space']
        else:
            new_prefix = prefix + self.tree_symbols['vertical']
        
        # 顯示測試案例
        if show_test_cases and section.test_cases:
            for j, test_case in enumerate(section.test_cases):
                is_last_case = j == len(section.test_cases) - 1 and not section.subsections
                case_connector = self.tree_symbols['last_branch'] if is_last_case else self.tree_symbols['branch']
                
                case_line = f"{new_prefix}{case_connector}🧪 {test_case.title}"
                case_line += f" (ID: {test_case.id}, {test_case.priority.value}, {test_case.type.value})"
                lines.append(case_line)
        elif section.test_cases:
            # 只顯示測試案例數量
            case_connector = self.tree_symbols['last_branch'] if not section.subsections else self.tree_symbols['branch']
            lines.append(f"{new_prefix}{case_connector}🧪 {len(section.test_cases)} 個測試案例")
        
        # 遞迴處理子區段
        for i, subsection in enumerate(section.subsections):
            is_last_subsection = i == len(section.subsections) - 1
            subsection_lines = self._generate_detailed_section_tree(
                subsection, new_prefix, is_last_subsection, show_test_cases
            )
            lines.extend(subsection_lines)
        
        return lines