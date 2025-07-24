"""
測試輔助工具函數

提供測試過程中需要的共用工具和輔助函數
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import Mock


class XMLTestHelper:
    """XML 測試輔助類別"""
    
    @staticmethod
    def load_xml_fixture(filename: str) -> ET.Element:
        """
        載入測試用 XML 檔案
        
        Args:
            filename: XML 檔案名稱（不含路徑）
            
        Returns:
            ET.Element: XML 根元素
        """
        fixture_path = Path(__file__).parent / "fixtures" / "xml" / filename
        tree = ET.parse(fixture_path)
        return tree.getroot()
    
    @staticmethod
    def create_test_xml_element(tag: str, text: str = None, **attributes) -> ET.Element:
        """
        建立測試用 XML 元素
        
        Args:
            tag: 元素標籤名稱
            text: 元素內容文字
            **attributes: 元素屬性
            
        Returns:
            ET.Element: XML 元素
        """
        element = ET.Element(tag, **attributes)
        if text:
            element.text = text
        return element
    
    @staticmethod
    def xml_to_string(element: ET.Element) -> str:
        """
        將 XML 元素轉換為字串
        
        Args:
            element: XML 元素
            
        Returns:
            str: XML 字串
        """
        return ET.tostring(element, encoding='unicode')


class LarkTestHelper:
    """Lark API 測試輔助類別"""
    
    @staticmethod
    def load_lark_response(filename: str) -> Dict[str, Any]:
        """
        載入測試用 Lark API 回應資料
        
        Args:
            filename: JSON 檔案名稱（不含路徑）
            
        Returns:
            Dict: Lark API 回應資料
        """
        fixture_path = Path(__file__).parent / "fixtures" / "lark_responses" / filename
        with open(fixture_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def create_mock_response(status_code: int, json_data: Dict[str, Any]) -> Mock:
        """
        建立模擬的 HTTP 回應物件
        
        Args:
            status_code: HTTP 狀態碼
            json_data: 回應的 JSON 資料
            
        Returns:
            Mock: 模擬的回應物件
        """
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.json.return_value = json_data
        mock_response.text = json.dumps(json_data, ensure_ascii=False)
        return mock_response
    
    @staticmethod
    def create_batch_records_payload(records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        建立批次記錄建立的請求負載
        
        Args:
            records: 記錄資料列表
            
        Returns:
            Dict: 請求負載
        """
        return {
            "records": [
                {"fields": record} for record in records
            ]
        }


class FileTestHelper:
    """檔案測試輔助類別"""
    
    @staticmethod
    def load_expected_output(filename: str) -> Any:
        """
        載入預期輸出資料
        
        Args:
            filename: 檔案名稱（不含路徑）
            
        Returns:
            Any: 預期輸出資料
        """
        fixture_path = Path(__file__).parent / "fixtures" / "expected_outputs" / filename
        
        if filename.endswith('.json'):
            with open(fixture_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            with open(fixture_path, 'r', encoding='utf-8') as f:
                return f.read()
    
    @staticmethod
    def create_temp_file(content: str, filename: str = "temp_test_file.txt") -> Path:
        """
        建立臨時測試檔案
        
        Args:
            content: 檔案內容
            filename: 檔案名稱
            
        Returns:
            Path: 臨時檔案路徑
        """
        temp_dir = Path(__file__).parent / "temp"
        temp_dir.mkdir(exist_ok=True)
        
        temp_file = temp_dir / filename
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return temp_file
    
    @staticmethod
    def cleanup_temp_files(temp_dir: Path = None):
        """
        清理臨時測試檔案
        
        Args:
            temp_dir: 臨時目錄路徑，預設為 tests/temp
        """
        if temp_dir is None:
            temp_dir = Path(__file__).parent / "temp"
        
        if temp_dir.exists():
            for file in temp_dir.glob("*"):
                if file.is_file():
                    file.unlink()


class DataTestHelper:
    """資料測試輔助類別"""
    
    @staticmethod
    def create_sample_test_case(**kwargs) -> Dict[str, Any]:
        """
        建立範例測試案例資料
        
        Args:
            **kwargs: 測試案例欄位值
            
        Returns:
            Dict: 測試案例資料
        """
        default_data = {
            "test_case_number": "TCG-000.000.000",
            "title": "範例測試案例",
            "priority": "Medium",
            "precondition": "範例前置條件",
            "steps": "1. 執行步驟一\n2. 執行步驟二",
            "expected_result": "範例預期結果"
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_sample_xml_case(**kwargs) -> ET.Element:
        """
        建立範例 XML 測試案例元素
        
        Args:
            **kwargs: 測試案例欄位值
            
        Returns:
            ET.Element: XML 測試案例元素
        """
        defaults = {
            "id": "C000",
            "title": "TCG-000.000.000 範例測試案例",
            "priority": "Medium",
            "preconds": "範例前置條件",
            "steps": "1. 執行步驟一\n2. 執行步驟二",
            "expected": "範例預期結果"
        }
        defaults.update(kwargs)
        
        case_elem = ET.Element("case")
        id_elem = ET.SubElement(case_elem, "id")
        id_elem.text = defaults["id"]
        
        title_elem = ET.SubElement(case_elem, "title")
        title_elem.text = defaults["title"]
        
        priority_elem = ET.SubElement(case_elem, "priority")
        priority_elem.text = defaults["priority"]
        
        custom_elem = ET.SubElement(case_elem, "custom")
        
        preconds_elem = ET.SubElement(custom_elem, "preconds")
        preconds_elem.text = defaults["preconds"]
        
        steps_elem = ET.SubElement(custom_elem, "steps")
        steps_elem.text = defaults["steps"]
        
        expected_elem = ET.SubElement(custom_elem, "expected")
        expected_elem.text = defaults["expected"]
        
        return case_elem
    
    @staticmethod
    def compare_test_case_data(actual: Dict[str, Any], expected: Dict[str, Any], 
                              ignore_fields: List[str] = None) -> bool:
        """
        比較測試案例資料
        
        Args:
            actual: 實際資料
            expected: 預期資料
            ignore_fields: 忽略的欄位列表
            
        Returns:
            bool: 是否相同
        """
        if ignore_fields is None:
            ignore_fields = []
        
        for key, expected_value in expected.items():
            if key in ignore_fields:
                continue
                
            if key not in actual:
                return False
                
            if actual[key] != expected_value:
                return False
        
        return True


# 全域輔助函數實例，方便測試使用
xml_helper = XMLTestHelper()
lark_helper = LarkTestHelper()
file_helper = FileTestHelper()
data_helper = DataTestHelper()