"""
TestRail 測試案例資料清理器模組

提供測試案例資料的格式清理和標準化功能
"""

import logging
import re
from typing import Dict, Any, Tuple


class DataCleaningError(Exception):
    """資料清理錯誤"""
    pass


class TestCaseDataCleaner:
    """TestRail 測試案例資料清理器"""
    
    def __init__(self):
        """初始化資料清理器"""
        self.logger = logging.getLogger(f"{__name__}.TestCaseDataCleaner")
        self.logger.debug("TestRail 資料清理器初始化完成")
        
        # 編譯正則表達式模式以提高效能
        self._case_number_pattern = re.compile(r'TCG-?(\d+)\.(\d+)\.(\d+)')
        self._hyphen_fix_pattern = re.compile(r'TCG(\d+)\.(\d+)\.(\d+)')
        self._markdown_bold_pattern = re.compile(r'\*\*([^*]+)\*\*')
        self._markdown_italic_pattern = re.compile(r'\*([^*]+)\*')
        self._markdown_code_pattern = re.compile(r'`([^`]+)`')
        self._markdown_code_block_pattern = re.compile(r'```([^`]+)```')
        self._url_link_pattern = re.compile(r'\[([^\]]+)\]\([^)]+\)')
    
    def extract_test_case_number_and_title(self, title: str) -> Tuple[str, str]:
        """
        從完整標題中提取測試案例編號和純標題
        
        Args:
            title: 完整標題，格式為 "TCG-XXX.YYY.ZZZ 標題內容"
            
        Returns:
            Tuple[str, str]: (test_case_number, clean_title)
            
        Raises:
            TypeError: 當title不是字串時
        """
        if title is None:
            raise TypeError("標題不能為None")
        
        if not isinstance(title, str):
            raise TypeError("標題必須是字串")
        
        title = title.strip()
        if not title:
            return "", ""
        
        self.logger.debug(f"提取測試案例編號和標題: {title[:50]}...")
        
        # 尋找TCG編號模式（包括缺失hyphen的情況）
        match = self._case_number_pattern.search(title)
        
        if match:
            # 提取匹配的編號部分
            full_match = match.group(0)
            
            # 確保格式正確（補上hyphen如果缺失）
            case_number = self.fix_missing_hyphen(full_match)
            
            # 移除編號部分，取得純標題
            clean_title = title.replace(full_match, "", 1).strip()
            
            self.logger.debug(f"成功提取 - 編號: {case_number}, 標題: {clean_title}")
            return case_number, clean_title
        else:
            self.logger.debug("未找到測試案例編號")
            return "", title
    
    def fix_missing_hyphen(self, case_number: str) -> str:
        """
        修正測試案例編號中缺失的 hyphen
        
        Args:
            case_number: 可能缺失 hyphen 的測試案例編號
            
        Returns:
            str: 修正後的標準格式編號
        """
        if not isinstance(case_number, str):
            return case_number
        
        # 檢查是否已經是正確格式
        if case_number.startswith("TCG-") and self._case_number_pattern.match(case_number):
            return case_number
        
        # 檢查是否是缺失hyphen的格式
        match = self._hyphen_fix_pattern.match(case_number)
        if match:
            num1, num2, num3 = match.groups()
            corrected = f"TCG-{num1}.{num2}.{num3}"
            self.logger.debug(f"修正缺失hyphen: {case_number} -> {corrected}")
            return corrected
        
        # 如果不符合任何已知格式，返回原值
        return case_number
    
    def clean_markdown_content(self, content: str) -> str:
        """
        清理內容中的 Markdown 格式
        
        Args:
            content: 包含 Markdown 格式的文字內容
            
        Returns:
            str: 清理後的純文字內容
            
        Raises:
            TypeError: 當content不是字串時
        """
        if content is None:
            raise TypeError("內容不能為None")
        
        if not isinstance(content, str):
            raise TypeError("內容必須是字串")
        
        if not content:
            return ""
        
        self.logger.debug(f"清理Markdown內容: {content[:50]}...")
        
        # 首先處理URL連結（保留說明文字）
        content = self.extract_url_description(content)
        
        # 清理程式碼區塊（```code```）
        content = self._markdown_code_block_pattern.sub(r'\1', content)
        
        # 清理行內程式碼（`code`）
        content = self._markdown_code_pattern.sub(r'\1', content)
        
        # 處理巢狀格式：重複清理直到沒有變化
        previous_content = ""
        while previous_content != content:
            previous_content = content
            # 清理粗體（**bold**），包括巢狀情況
            content = self._markdown_bold_pattern.sub(r'\1', content)
            # 清理斜體（*italic*），包括巢狀情況
            content = self._markdown_italic_pattern.sub(r'\1', content)
        
        self.logger.debug(f"Markdown清理完成: {content[:50]}...")
        return content.strip()
    
    def extract_url_description(self, url_content: str) -> str:
        """
        從 URL Markdown 格式中提取說明文字
        
        Args:
            url_content: 包含 URL 的內容
            
        Returns:
            str: 僅保留說明文字的內容
        """
        if not isinstance(url_content, str):
            return url_content
        
        if not url_content:
            return ""
        
        # 將 [說明文字](URL) 格式替換為 說明文字
        result = self._url_link_pattern.sub(r'\1', url_content)
        
        self.logger.debug(f"URL說明提取: {url_content[:30]}... -> {result[:30]}...")
        return result
    
    def clean_test_case_fields(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        清理整個測試案例的所有欄位
        
        Args:
            test_case: 原始測試案例資料
            
        Returns:
            Dict[str, Any]: 清理後的測試案例資料
        """
        if not isinstance(test_case, dict):
            raise TypeError("測試案例必須是字典型態")
        
        self.logger.debug(f"清理測試案例欄位: {test_case.get('id', 'unknown')}")
        
        # 取得並清理標題，提取編號
        original_title = test_case.get("title", "")
        if original_title is None:
            original_title = ""
        
        case_number, clean_title = self.extract_test_case_number_and_title(str(original_title))
        
        # 清理其他欄位
        priority = test_case.get("priority", "")
        if priority is None:
            priority = ""
        
        preconds = test_case.get("preconds", "")
        if preconds is None:
            preconds = ""
        
        steps = test_case.get("steps", "")
        if steps is None:
            steps = ""
        
        expected = test_case.get("expected", "")
        if expected is None:
            expected = ""
        
        # 應用Markdown清理到所有文字欄位
        cleaned_case = {
            "test_case_number": case_number,
            "title": self.clean_markdown_content(str(clean_title)),
            "priority": str(priority),
            "precondition": self.clean_markdown_content(str(preconds)),
            "steps": self.clean_markdown_content(str(steps)),
            "expected_result": self.clean_markdown_content(str(expected))
        }
        
        self.logger.debug(f"測試案例清理完成: {cleaned_case['test_case_number']} - {cleaned_case['title'][:30]}...")
        return cleaned_case
    
    def get_cleaner_stats(self) -> Dict[str, Any]:
        """
        取得資料清理器統計資訊
        
        Returns:
            Dict[str, Any]: 清理器統計資料
        """
        return {
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