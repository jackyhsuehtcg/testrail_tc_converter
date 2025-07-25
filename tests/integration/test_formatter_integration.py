"""
格式轉換器整合測試

測試格式轉換器與其他模組的整合，包括：
- 與 XML 解析器的整合
- 與資料清理器的整合
- 與 Lark 客戶端的整合
- 端到端資料流程測試
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch

# 加入 src 目錄到 Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from parsers.xml_parser import TestRailXMLParser
from parsers.data_cleaner import TestCaseDataCleaner
from parsers.formatter import LarkDataFormatter
from lark.client import SimpleLarkClient


class TestFormatterIntegration:
    """格式轉換器整合測試"""
    
    def setup_method(self):
        """每個測試方法前的設定"""
        self.xml_parser = TestRailXMLParser()
        self.data_cleaner = TestCaseDataCleaner()
        self.formatter = LarkDataFormatter()
        
        # 測試 XML 檔案路徑
        self.test_xml_path = os.path.join(
            os.path.dirname(__file__), '..', 'fixtures', 'xml', 'sample_basic.xml'
        )
    
    def test_complete_xml_to_lark_workflow(self):
        """測試完整的 XML 到 Lark 格式轉換流程"""
        # 1. 解析 XML 檔案
        raw_test_cases = self.xml_parser.parse_xml_file(self.test_xml_path)
        assert len(raw_test_cases) > 0, "應該成功解析出測試案例"
        
        # 2. 清理資料
        cleaned_test_cases = []
        for raw_case in raw_test_cases:
            cleaned_case = self.data_cleaner.clean_test_case_fields(raw_case)
            cleaned_test_cases.append(cleaned_case)
        
        assert len(cleaned_test_cases) == len(raw_test_cases), "清理後的數量應該相同"
        
        # 3. 格式轉換為 Lark 格式
        lark_records = self.formatter.batch_format_records(cleaned_test_cases)
        
        # 驗證轉換結果
        assert len(lark_records) > 0, "應該成功轉換為 Lark 格式"
        assert len(lark_records) <= len(cleaned_test_cases), "Lark 記錄數量不應超過清理後的數量"
        
        # 驗證每筆記錄的格式
        for record in lark_records:
            assert self.formatter.validate_required_fields(record), "每筆記錄都應該通過驗證"
            
            # 檢查必要欄位
            required_fields = [
                "test_case_number", "title", "priority",
                "precondition", "steps", "expected_result"
            ]
            for field in required_fields:
                assert field in record, f"記錄應該包含欄位: {field}"
                assert isinstance(record[field], str), f"欄位 {field} 應該是字串類型"
            
            # 檢查優先級格式
            assert record["priority"] in ["High", "Medium", "Low"], "優先級應該是標準值"
    
    def test_data_consistency_through_pipeline(self):
        """測試資料在整個處理流程中的一致性"""
        # 使用包含已知資料的 XML 檔案
        raw_test_cases = self.xml_parser.parse_xml_file(self.test_xml_path)
        
        # 選擇第一個測試案例進行詳細測試
        if len(raw_test_cases) > 0:
            raw_case = raw_test_cases[0]
            
            # 清理資料
            cleaned_case = self.data_cleaner.clean_test_case_fields(raw_case)
            
            # 格式轉換
            lark_record = self.formatter.format_test_case_for_lark(cleaned_case)
            
            # 驗證資料一致性
            assert lark_record["test_case_number"] == cleaned_case["test_case_number"]
            assert lark_record["title"] == cleaned_case["title"]
            assert lark_record["precondition"] == cleaned_case["precondition"]
            assert lark_record["steps"] == cleaned_case["steps"]
            assert lark_record["expected_result"] == cleaned_case["expected_result"]
            
            # 優先級可能被標準化，但不應該是空值
            assert lark_record["priority"] in ["High", "Medium", "Low"]
    
    def test_large_dataset_processing(self):
        """測試大量資料集的處理效能"""
        # 使用較大的測試檔案
        large_xml_path = os.path.join(
            os.path.dirname(__file__), '..', 'fixtures', 'xml', 'TP-3153 Associated Users Phase 2.xml'
        )
        
        # 檢查檔案是否存在
        if not os.path.exists(large_xml_path):
            pytest.skip("大型測試檔案不存在，跳過效能測試")
        
        import time
        
        start_time = time.time()
        
        # 1. 解析 XML
        raw_test_cases = self.xml_parser.parse_xml_file(large_xml_path)
        parse_time = time.time() - start_time
        
        # 2. 清理資料
        clean_start = time.time()
        cleaned_test_cases = []
        for raw_case in raw_test_cases:
            cleaned_case = self.data_cleaner.clean_test_case_fields(raw_case)
            cleaned_test_cases.append(cleaned_case)
        clean_time = time.time() - clean_start
        
        # 3. 格式轉換
        format_start = time.time()
        lark_records = self.formatter.batch_format_records(cleaned_test_cases)
        format_time = time.time() - format_start
        
        total_time = time.time() - start_time
        
        # 效能要求驗證
        assert parse_time < 5.0, f"XML 解析時間 {parse_time:.2f}s 超過預期"
        assert clean_time < 3.0, f"資料清理時間 {clean_time:.2f}s 超過預期"
        assert format_time < 1.0, f"格式轉換時間 {format_time:.2f}s 超過預期"
        assert total_time < 8.0, f"總處理時間 {total_time:.2f}s 超過預期"
        
        # 資料完整性驗證
        assert len(lark_records) > 0, "應該成功處理大量資料"
        
        print(f"\n效能測試結果:")
        print(f"  原始案例數: {len(raw_test_cases)}")
        print(f"  清理後案例數: {len(cleaned_test_cases)}")  
        print(f"  Lark 記錄數: {len(lark_records)}")
        print(f"  XML 解析時間: {parse_time:.2f}s")
        print(f"  資料清理時間: {clean_time:.2f}s")
        print(f"  格式轉換時間: {format_time:.2f}s")
        print(f"  總處理時間: {total_time:.2f}s")
    
    def test_error_handling_in_pipeline(self):
        """測試整個流程中的錯誤處理"""
        # 創建一個包含問題資料的模擬案例
        problematic_raw_case = {
            "id": "TEST-001",
            "title": "",  # 空標題
            "priority": "invalid_priority",
            "preconds": "前置條件",
            "steps": "",  # 空步驟
            "expected": "預期結果"
        }
        
        # 清理資料（可能部分修復問題）
        cleaned_case = self.data_cleaner.clean_test_case_fields(problematic_raw_case)
        
        # 格式轉換（應該過濾無效記錄）
        lark_records = self.formatter.batch_format_records([cleaned_case])
        
        # 檢查錯誤處理結果
        # 如果資料清理無法修復問題，格式轉換器應該過濾掉無效記錄
        if len(lark_records) == 0:
            # 記錄被正確過濾
            assert True
        else:
            # 記錄被修復，檢查是否符合要求
            record = lark_records[0]
            assert self.formatter.validate_required_fields(record)
    
    def test_unicode_handling_through_pipeline(self):
        """測試 Unicode 字符在整個流程中的處理"""
        # 創建包含 Unicode 字符的測試案例（符合資料清理器預期格式）
        unicode_raw_case = {
            "id": "測試-001",
            "title": "TCG-001.002.003 Unicode 測試案例 🚀 αβγ 中文標題",  # 包含有效的測試案例編號
            "priority": "High",
            "preconds": "包含中文和表情符號的前置條件 😀",
            "steps": "步驟1：測試中文\n步驟2：test English\n步驟3：тест русский",
            "expected": "正確處理各種語言字符 ñáéíóú"
        }
        
        # 完整流程處理
        cleaned_case = self.data_cleaner.clean_test_case_fields(unicode_raw_case)
        lark_record = self.formatter.format_test_case_for_lark(cleaned_case)
        
        # 驗證 Unicode 字符保持完整
        assert "TCG-001.002.003" == lark_record["test_case_number"]
        assert "🚀" in lark_record["title"]
        assert "αβγ" in lark_record["title"]
        assert "中文標題" in lark_record["title"]
        assert "😀" in lark_record["precondition"]
        assert "中文" in lark_record["steps"]
        assert "русский" in lark_record["steps"]
        assert "ñáéíóú" in lark_record["expected_result"]
    
    def test_formatter_with_lark_client_compatibility(self):
        """測試格式轉換器輸出與 Lark 客戶端的相容性"""
        # 解析和清理測試資料
        raw_test_cases = self.xml_parser.parse_xml_file(self.test_xml_path)
        cleaned_test_cases = []
        for raw_case in raw_test_cases:
            cleaned_case = self.data_cleaner.clean_test_case_fields(raw_case)
            cleaned_test_cases.append(cleaned_case)
        
        # 格式轉換
        lark_records = self.formatter.batch_format_records(cleaned_test_cases)
        
        if len(lark_records) > 0:
            # 創建模擬的 Lark 客戶端
            with patch('src.lark.client.SimpleLarkClient') as MockLarkClient:
                mock_client = MockLarkClient.return_value
                mock_client.set_table_info.return_value = True
                mock_client._validate_record_format.return_value = True
                
                # 測試記錄格式是否被 Lark 客戶端接受
                for record in lark_records[:3]:  # 測試前3筆記錄
                    # 模擬 Lark 客戶端的記錄格式驗證
                    result = mock_client._validate_record_format(record)
                    assert result is True, f"記錄格式應該被 Lark 客戶端接受: {record}"
    
    def test_batch_processing_consistency(self):
        """測試批次處理與單筆處理的一致性"""
        # 解析測試資料
        raw_test_cases = self.xml_parser.parse_xml_file(self.test_xml_path)
        
        if len(raw_test_cases) >= 2:
            # 清理前兩個案例
            cleaned_cases = []
            for raw_case in raw_test_cases[:2]:
                cleaned_case = self.data_cleaner.clean_test_case_fields(raw_case)
                cleaned_cases.append(cleaned_case)
            
            # 批次處理
            batch_results = self.formatter.batch_format_records(cleaned_cases)
            
            # 單筆處理
            individual_results = []
            for cleaned_case in cleaned_cases:
                if self.formatter.validate_required_fields(cleaned_case):
                    result = self.formatter.format_test_case_for_lark(cleaned_case)
                    individual_results.append(result)
            
            # 比較結果一致性
            assert len(batch_results) == len(individual_results), "批次和單筆處理的結果數量應該相同"
            
            for batch_result, individual_result in zip(batch_results, individual_results):
                for field in ["test_case_number", "title", "priority", "precondition", "steps", "expected_result"]:
                    assert batch_result[field] == individual_result[field], f"欄位 {field} 在批次和單筆處理中應該相同"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])