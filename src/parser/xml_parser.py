"""
TestRail XML 解析器
專門處理 TestRail 匯出的 XML 格式，支援巢狀 section 結構
"""

import xml.etree.ElementTree as ET
from typing import Optional, List
import logging

from ..models.testrail_models import TestSuite, Section, TestCase, Priority, CaseType


class TestRailXMLParser:
    """TestRail XML 解析器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse_file(self, xml_file_path: str) -> TestSuite:
        """解析 XML 檔案"""
        try:
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            return self._parse_suite(root)
        except ET.ParseError as e:
            self.logger.error(f"XML 解析錯誤: {e}")
            raise
        except Exception as e:
            self.logger.error(f"檔案讀取錯誤: {e}")
            raise
    
    def parse_string(self, xml_string: str) -> TestSuite:
        """解析 XML 字串"""
        try:
            root = ET.fromstring(xml_string)
            return self._parse_suite(root)
        except ET.ParseError as e:
            self.logger.error(f"XML 解析錯誤: {e}")
            raise
    
    def _parse_suite(self, suite_element: ET.Element) -> TestSuite:
        """解析測試套件"""
        suite_id = self._get_text(suite_element, 'id', '')
        suite_name = self._get_text(suite_element, 'name', '')
        suite_description = self._get_text(suite_element, 'description')
        
        suite = TestSuite(
            id=suite_id,
            name=suite_name,
            description=suite_description
        )
        
        # 解析根層級的 sections
        sections_element = suite_element.find('sections')
        if sections_element is not None:
            for section_element in sections_element.findall('section'):
                section = self._parse_section(section_element, level=1)
                suite.add_section(section)
        
        return suite
    
    def _parse_section(self, section_element: ET.Element, level: int = 1) -> Section:
        """
        遞迴解析 section 和其巢狀的 sub-sections
        
        Args:
            section_element: XML section 元素
            level: 當前層級深度
        """
        name = self._get_text(section_element, 'name', '')
        description = self._get_text(section_element, 'description')
        
        section = Section(
            name=name,
            description=description,
            level=level
        )
        
        self.logger.debug(f"解析 Section (Level {level}): {name}")
        
        # 解析測試案例 (如果存在)
        cases_element = section_element.find('cases')
        if cases_element is not None:
            for case_element in cases_element.findall('case'):
                test_case = self._parse_test_case(case_element)
                section.add_test_case(test_case)
        
        # 遞迴解析子 sections (巢狀結構的關鍵)
        subsections_element = section_element.find('sections')
        if subsections_element is not None:
            for subsection_element in subsections_element.findall('section'):
                subsection = self._parse_section(subsection_element, level + 1)
                section.add_subsection(subsection)
        
        self.logger.debug(f"Section '{name}' 完成解析: "
                         f"{len(section.test_cases)} 測試案例, "
                         f"{len(section.subsections)} 子區段")
        
        return section
    
    def _parse_test_case(self, case_element: ET.Element) -> TestCase:
        """解析測試案例"""
        case_id = self._get_text(case_element, 'id', '')
        title = self._get_text(case_element, 'title', '')
        template = self._get_text(case_element, 'template', '')
        
        # 解析列舉值
        case_type = self._parse_case_type(self._get_text(case_element, 'type', 'Other'))
        priority = self._parse_priority(self._get_text(case_element, 'priority', 'Medium'))
        
        estimate = self._get_text(case_element, 'estimate')
        references = self._get_text(case_element, 'references')
        
        # 解析自定義欄位
        custom_element = case_element.find('custom')
        preconds = None
        steps = None
        expected = None
        custom_fields = {}
        
        if custom_element is not None:
            preconds = self._get_text(custom_element, 'preconds')
            steps = self._get_text(custom_element, 'steps')
            expected = self._get_text(custom_element, 'expected')
            
            # 收集其他自定義欄位
            for child in custom_element:
                if child.tag not in ['preconds', 'steps', 'expected']:
                    custom_fields[child.tag] = child.text
        
        return TestCase(
            id=case_id,
            title=title,
            template=template,
            type=case_type,
            priority=priority,
            estimate=estimate,
            references=references,
            preconds=preconds,
            steps=steps,
            expected=expected,
            custom_fields=custom_fields
        )
    
    def _get_text(self, parent: ET.Element, tag: str, default: Optional[str] = None) -> Optional[str]:
        """安全取得元素文字內容"""
        element = parent.find(tag)
        if element is not None and element.text:
            return element.text.strip()
        return default
    
    def _parse_case_type(self, type_str: str) -> CaseType:
        """解析測試案例類型"""
        try:
            # 處理可能的類型映射
            type_mapping = {
                'other': CaseType.OTHER,
                'functional': CaseType.FUNCTIONAL,
                'acceptance': CaseType.ACCEPTANCE,
                'automated': CaseType.AUTOMATED,
                'compatibility': CaseType.COMPATIBILITY,
                'destructive': CaseType.DESTRUCTIVE,
                'performance': CaseType.PERFORMANCE,
                'regression': CaseType.REGRESSION,
                'security': CaseType.SECURITY,
                'smoke & sanity': CaseType.SMOKE_SANITY,
                'usability': CaseType.USABILITY,
                'accessibility': CaseType.ACCESSIBILITY
            }
            
            return type_mapping.get(type_str.lower(), CaseType.OTHER)
        except:
            return CaseType.OTHER
    
    def _parse_priority(self, priority_str: str) -> Priority:
        """解析優先級"""
        try:
            priority_mapping = {
                'low': Priority.LOW,
                'medium': Priority.MEDIUM,
                'high': Priority.HIGH,
                'critical': Priority.CRITICAL
            }
            
            return priority_mapping.get(priority_str.lower(), Priority.MEDIUM)
        except:
            return Priority.MEDIUM