"""
TestRail XML 解析器模組

提供 TestRail XML 檔案解析功能，提取測試案例資料
"""

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional


class TestRailParseError(Exception):
    """TestRail XML 解析錯誤"""
    pass


class TestRailXMLParser:
    """TestRail XML 檔案解析器"""
    
    def __init__(self):
        """初始化解析器"""
        self.logger = logging.getLogger(f"{__name__}.TestRailXMLParser")
        self.logger.debug("TestRail XML 解析器初始化完成")
    
    def parse_xml_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        解析 TestRail XML 檔案並提取測試案例資料
        
        Args:
            file_path: XML 檔案的絕對路徑
            
        Returns:
            測試案例資料列表，每個字典包含原始 XML 資料
            
        Raises:
            FileNotFoundError: 檔案不存在
            ET.ParseError: XML 格式錯誤
            ValueError: 檔案內容格式不符
        """
        if not file_path:
            raise ValueError("檔案路徑不能為空")
        
        file_path_obj = Path(file_path)
        
        # 檢查檔案是否存在
        if not file_path_obj.exists():
            error_msg = f"XML 檔案不存在: {file_path}"
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # 檢查檔案是否為 XML 格式
        if file_path_obj.suffix.lower() != '.xml':
            error_msg = f"檔案不是 XML 格式: {file_path}"
            self.logger.warning(error_msg)
        
        self.logger.info(f"開始解析 XML 檔案: {file_path}")
        
        try:
            # 解析 XML 檔案
            tree = ET.parse(file_path)
            xml_root = tree.getroot()
            
            # 驗證 XML 結構
            if not self.validate_xml_structure(xml_root):
                error_msg = f"XML 檔案結構不符合 TestRail 格式: {file_path}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            # 提取測試案例
            test_cases = self.extract_test_cases(xml_root)
            
            self.logger.info(f"成功解析 XML 檔案，提取到 {len(test_cases)} 個測試案例")
            return test_cases
            
        except ET.ParseError as e:
            error_msg = f"XML 檔案格式錯誤: {file_path}, 錯誤: {str(e)}"
            self.logger.error(error_msg)
            raise ET.ParseError(error_msg)
        
        except Exception as e:
            error_msg = f"解析 XML 檔案時發生未預期錯誤: {file_path}, 錯誤: {str(e)}"
            self.logger.error(error_msg)
            raise TestRailParseError(error_msg)
    
    def extract_test_cases(self, xml_root: ET.Element) -> List[Dict[str, Any]]:
        """
        從 XML 根元素中提取測試案例清單
        
        Args:
            xml_root: XML 根元素
            
        Returns:
            提取的測試案例資料，僅包含必要的 5 個欄位
        """
        if xml_root is None:
            self.logger.warning("XML 根元素為空")
            return []
        
        test_cases = []
        
        # 遞迴搜尋所有的 case 元素（支援巢狀結構）
        case_elements = self._find_all_case_elements(xml_root)
        
        self.logger.debug(f"找到 {len(case_elements)} 個測試案例元素")
        
        for case_elem in case_elements:
            try:
                test_case = self._extract_single_test_case(case_elem)
                if test_case:  # 只添加有效的測試案例
                    test_cases.append(test_case)
            except Exception as e:
                case_id = self._get_element_text(case_elem, "id", "未知")
                self.logger.warning(f"提取測試案例失敗 (ID: {case_id}): {str(e)}")
                # 繼續處理其他案例，不中斷整個流程
        
        self.logger.info(f"成功提取 {len(test_cases)} 個有效測試案例")
        return test_cases
    
    def validate_xml_structure(self, xml_root: ET.Element) -> bool:
        """
        驗證 XML 結構是否符合 TestRail 標準格式
        
        Args:
            xml_root: XML 根元素
            
        Returns:
            結構是否有效
        """
        if xml_root is None:
            self.logger.error("XML 根元素為空")
            return False
        
        # 檢查根元素是否為 suite
        if xml_root.tag != "suite":
            self.logger.warning(f"XML 根元素不是 'suite'，而是 '{xml_root.tag}'")
            # 不一定要求嚴格的 suite 根元素，可能有其他格式
        
        # 檢查是否包含 sections 元素
        sections = xml_root.find("sections")
        if sections is None:
            # 嘗試直接在根元素下尋找 case 元素
            cases = xml_root.findall(".//case")
            if not cases:
                self.logger.error("XML 中找不到任何測試案例")
                return False
            else:
                self.logger.debug("在根元素下直接找到測試案例")
        
        self.logger.debug("XML 結構驗證通過")
        return True
    
    def _find_all_case_elements(self, xml_root: ET.Element) -> List[ET.Element]:
        """
        遞迴搜尋所有的 case 元素
        
        Args:
            xml_root: 搜尋的根元素
            
        Returns:
            所有找到的 case 元素列表
        """
        # 使用 XPath 表達式搜尋所有深度的 case 元素
        return xml_root.findall(".//case")
    
    def _extract_single_test_case(self, case_elem: ET.Element) -> Optional[Dict[str, Any]]:
        """
        從單個 case 元素中提取測試案例資料
        
        Args:
            case_elem: case XML 元素
            
        Returns:
            測試案例資料字典，包含必要的 5 個欄位
        """
        if case_elem is None:
            return None
        
        try:
            # 提取基本資訊
            test_case = {
                "id": self._get_element_text(case_elem, "id", ""),
                "title": self._get_element_text(case_elem, "title", ""),
                "priority": self._get_element_text(case_elem, "priority", "Medium")
            }
            
            # 提取 custom 欄位中的詳細資訊
            custom_elem = case_elem.find("custom")
            if custom_elem is not None:
                test_case.update({
                    "preconds": self._get_element_text(custom_elem, "preconds", ""),
                    "steps": self._get_element_text(custom_elem, "steps", ""),
                    "expected": self._get_element_text(custom_elem, "expected", "")
                })
            else:
                # 如果沒有 custom 元素，設定預設值
                test_case.update({
                    "preconds": "",
                    "steps": "",
                    "expected": ""
                })
                self.logger.debug(f"測試案例 {test_case['id']} 缺少 custom 元素")
            
            # 驗證基本必要欄位
            if not test_case["title"]:
                self.logger.warning(f"測試案例 {test_case['id']} 缺少標題")
                return None
            
            self.logger.debug(f"成功提取測試案例: {test_case['id']} - {test_case['title'][:50]}...")
            return test_case
            
        except Exception as e:
            self.logger.error(f"提取單個測試案例時發生錯誤: {str(e)}")
            return None
    
    def _get_element_text(self, parent: ET.Element, tag_name: str, default: str = "") -> str:
        """
        安全地取得 XML 元素的文字內容
        
        Args:
            parent: 父元素
            tag_name: 標籤名稱
            default: 預設值
            
        Returns:
            元素的文字內容，如果不存在則回傳預設值
        """
        if parent is None:
            return default
        
        element = parent.find(tag_name)
        if element is not None and element.text is not None:
            # 清理文字內容（移除前後空白）
            return element.text.strip()
        
        return default
    
    def get_parser_stats(self) -> Dict[str, Any]:
        """
        取得解析器統計資訊
        
        Returns:
            解析器統計資料
        """
        return {
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