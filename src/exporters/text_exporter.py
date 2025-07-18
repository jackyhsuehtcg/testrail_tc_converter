"""
文字格式輸出模組
支援 TXT 和 Markdown 格式輸出
"""

from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

from ..models.testrail_models import TestSuite, Section, TestCase


class TextExporter:
    """文字格式輸出器"""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def export_to_txt(self, suite: TestSuite, output_path: str, 
                     include_details: bool = True) -> None:
        """
        輸出為 TXT 格式
        
        Args:
            suite: 測試套件
            output_path: 輸出檔案路徑
            include_details: 是否包含詳細資訊
        """
        content = self._generate_txt_content(suite, include_details)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def export_to_markdown(self, suite: TestSuite, output_path: str,
                          include_details: bool = True) -> None:
        """
        輸出為 Markdown 格式
        
        Args:
            suite: 測試套件
            output_path: 輸出檔案路徑
            include_details: 是否包含詳細資訊
        """
        content = self._generate_markdown_content(suite, include_details)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _generate_txt_content(self, suite: TestSuite, include_details: bool) -> str:
        """生成 TXT 格式內容"""
        lines = []
        
        # 標題
        lines.append("=" * 80)
        lines.append(f"TestRail 測試套件報告")
        lines.append("=" * 80)
        lines.append(f"生成時間: {self.timestamp}")
        lines.append("")
        
        # 套件資訊
        lines.append("套件資訊:")
        lines.append(f"  ID: {suite.id}")
        lines.append(f"  名稱: {suite.name}")
        if suite.description:
            lines.append(f"  描述: {suite.description}")
        lines.append(f"  總測試案例數: {suite.get_total_cases_count()}")
        lines.append(f"  根層級區段數: {len(suite.sections)}")
        lines.append("")
        
        # 結構概覽
        lines.append("結構概覽:")
        lines.append("-" * 40)
        for i, section in enumerate(suite.sections, 1):
            lines.extend(self._generate_section_txt(section, "", i == len(suite.sections)))
        lines.append("")
        
        # 詳細資訊
        if include_details:
            lines.append("詳細測試案例:")
            lines.append("-" * 40)
            for section in suite.sections:
                lines.extend(self._generate_detailed_section_txt(section))
        
        return "\n".join(lines)
    
    def _generate_markdown_content(self, suite: TestSuite, include_details: bool) -> str:
        """生成 Markdown 格式內容"""
        lines = []
        
        # 標題
        lines.append(f"# TestRail 測試套件報告")
        lines.append("")
        lines.append(f"**生成時間:** {self.timestamp}")
        lines.append("")
        
        # 套件資訊
        lines.append("## 套件資訊")
        lines.append("")
        lines.append(f"- **ID:** {suite.id}")
        lines.append(f"- **名稱:** {suite.name}")
        if suite.description:
            lines.append(f"- **描述:** {suite.description}")
        lines.append(f"- **總測試案例數:** {suite.get_total_cases_count()}")
        lines.append(f"- **根層級區段數:** {len(suite.sections)}")
        lines.append("")
        
        # 結構樹狀圖
        lines.append("## 結構概覽")
        lines.append("")
        lines.append("```")
        for i, section in enumerate(suite.sections, 1):
            lines.extend(self._generate_section_txt(section, "", i == len(suite.sections)))
        lines.append("```")
        lines.append("")
        
        # 統計資訊
        lines.append("## 統計資訊")
        lines.append("")
        lines.append("| 區段名稱 | 層級 | 直接案例 | 總案例 | 子區段數 |")
        lines.append("|----------|------|----------|--------|----------|")
        
        for section in suite.sections:
            lines.extend(self._generate_stats_markdown(section))
        lines.append("")
        
        # 詳細資訊
        if include_details:
            lines.append("## 詳細測試案例")
            lines.append("")
            for section in suite.sections:
                lines.extend(self._generate_detailed_section_markdown(section))
        
        return "\n".join(lines)
    
    def _generate_section_txt(self, section: Section, prefix: str, is_last: bool) -> List[str]:
        """生成區段的 TXT 樹狀結構"""
        lines = []
        
        # 樹狀結構符號
        connector = "└── " if is_last else "├── "
        
        # 區段資訊
        case_count = section.get_total_cases_count()
        section_line = f"{prefix}{connector}{section.name}"
        if case_count > 0:
            section_line += f" ({case_count} 案例)"
        
        lines.append(section_line)
        
        # 子區段的前綴
        if is_last:
            new_prefix = prefix + "    "
        else:
            new_prefix = prefix + "│   "
        
        # 處理子區段
        for i, subsection in enumerate(section.subsections):
            is_last_sub = i == len(section.subsections) - 1
            lines.extend(self._generate_section_txt(subsection, new_prefix, is_last_sub))
        
        return lines
    
    def _generate_detailed_section_txt(self, section: Section) -> List[str]:
        """生成詳細的區段資訊 (TXT 格式)"""
        lines = []
        
        if section.test_cases:
            lines.append(f"\n區段: {section.name} (Level {section.level})")
            lines.append("-" * min(60, len(section.name) + 20))
            
            for i, case in enumerate(section.test_cases, 1):
                lines.append(f"\n{i}. 測試案例: {case.title}")
                lines.append(f"   ID: {case.id}")
                lines.append(f"   類型: {case.type.value}")
                lines.append(f"   優先級: {case.priority.value}")
                
                if case.preconds:
                    lines.append(f"   前置條件: {case.preconds[:100]}...")
                if case.steps:
                    lines.append(f"   測試步驟: {case.steps[:100]}...")
                if case.expected:
                    lines.append(f"   預期結果: {case.expected[:100]}...")
        
        # 遞迴處理子區段
        for subsection in section.subsections:
            lines.extend(self._generate_detailed_section_txt(subsection))
        
        return lines
    
    def _generate_stats_markdown(self, section: Section) -> List[str]:
        """生成統計資訊的 Markdown 表格行"""
        lines = []
        
        # 當前區段
        direct_cases = len(section.test_cases)
        total_cases = section.get_total_cases_count()
        subsection_count = len(section.subsections)
        
        # 根據層級添加縮排
        indent = "  " * (section.level - 1)
        section_name = f"{indent}{section.name}"
        
        lines.append(f"| {section_name} | {section.level} | {direct_cases} | {total_cases} | {subsection_count} |")
        
        # 遞迴處理子區段
        for subsection in section.subsections:
            lines.extend(self._generate_stats_markdown(subsection))
        
        return lines
    
    def _generate_detailed_section_markdown(self, section: Section) -> List[str]:
        """生成詳細的區段資訊 (Markdown 格式)"""
        lines = []
        
        if section.test_cases:
            lines.append(f"### {section.name} (Level {section.level})")
            lines.append("")
            
            for i, case in enumerate(section.test_cases, 1):
                lines.append(f"#### {i}. {case.title}")
                lines.append("")
                lines.append(f"- **ID:** {case.id}")
                lines.append(f"- **類型:** {case.type.value}")
                lines.append(f"- **優先級:** {case.priority.value}")
                
                if case.preconds:
                    lines.append(f"- **前置條件:** {case.preconds[:200]}...")
                if case.steps:
                    lines.append(f"- **測試步驟:** {case.steps[:200]}...")
                if case.expected:
                    lines.append(f"- **預期結果:** {case.expected[:200]}...")
                
                lines.append("")
        
        # 遞迴處理子區段
        for subsection in section.subsections:
            lines.extend(self._generate_detailed_section_markdown(subsection))
        
        return lines