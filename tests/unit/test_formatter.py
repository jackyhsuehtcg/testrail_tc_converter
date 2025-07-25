"""
格式轉換器模組測試

測試 LarkDataFormatter 類別的各項功能，包括：
- 單筆測試案例格式轉換
- 批次資料格式轉換  
- Lark 欄位格式驗證
- 資料完整性檢查
- 優先級欄位標準化
- 必要欄位驗證
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch

# 加入 src 目錄到 Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from parsers.formatter import LarkDataFormatter, ValidationError


class TestLarkDataFormatter:
    """LarkDataFormatter 類別測試"""
    
    def setup_method(self):
        """每個測試方法前的設定"""
        self.formatter = LarkDataFormatter()
        
        # 標準測試案例資料
        self.valid_test_case = {
            "test_case_number": "TCG-001.002.003",
            "title": "登入功能測試",
            "priority": "High",
            "precondition": "用戶已註冊",
            "steps": "1. 開啟登入頁面\n2. 輸入帳號密碼\n3. 點擊登入",
            "expected_result": "成功登入系統"
        }
        
        # 邊界條件測試案例
        self.edge_case_test = {
            "test_case_number": "TCG-999.888.777",
            "title": "特殊字符測試 @#$%^&*()",
            "priority": "medium",  # 測試小寫優先級
            "precondition": "",  # 空前置條件
            "steps": "測試步驟包含中文與 English 混合",
            "expected_result": "處理特殊字符正確"
        }
    
    def test_init(self):
        """測試初始化"""
        formatter = LarkDataFormatter()
        assert formatter is not None
        assert hasattr(formatter, 'format_test_case_for_lark')
        assert hasattr(formatter, 'validate_required_fields')
        assert hasattr(formatter, 'format_priority_field')
        assert hasattr(formatter, 'batch_format_records')
    
    def test_format_test_case_for_lark_valid_input(self):
        """測試有效輸入的格式轉換"""
        result = self.formatter.format_test_case_for_lark(self.valid_test_case)
        
        # 檢查回傳的資料結構
        assert isinstance(result, dict)
        
        # 檢查所有必要欄位都存在
        expected_fields = [
            "test_case_number", "title", "priority", 
            "precondition", "steps", "expected_result"
        ]
        for field in expected_fields:
            assert field in result
        
        # 檢查欄位值正確轉換
        assert result["test_case_number"] == "TCG-001.002.003"
        assert result["title"] == "登入功能測試"
        assert result["priority"] == "High"  # 優先級標準化
        assert result["precondition"] == "用戶已註冊"
        assert result["steps"] == "1. 開啟登入頁面\n2. 輸入帳號密碼\n3. 點擊登入"
        assert result["expected_result"] == "成功登入系統"
    
    def test_format_test_case_for_lark_edge_cases(self):
        """測試邊界條件的格式轉換"""
        result = self.formatter.format_test_case_for_lark(self.edge_case_test)
        
        # 檢查特殊字符處理
        assert result["title"] == "特殊字符測試 @#$%^&*()"
        
        # 檢查優先級標準化（小寫轉換）
        assert result["priority"] == "Medium"
        
        # 檢查空前置條件處理
        assert result["precondition"] == ""
        
        # 檢查中英文混合內容
        assert "中文" in result["steps"]
        assert "English" in result["steps"]
    
    def test_format_priority_field_standard_values(self):
        """測試優先級欄位標準化 - 標準值"""
        test_cases = [
            ("High", "High"),
            ("high", "High"),
            ("HIGH", "High"),
            ("Medium", "Medium"),
            ("medium", "Medium"),
            ("MEDIUM", "Medium"),
            ("Low", "Low"),
            ("low", "Low"),
            ("LOW", "Low")
        ]
        
        for input_val, expected in test_cases:
            result = self.formatter.format_priority_field(input_val)
            assert result == expected, f"輸入 '{input_val}' 應該轉換為 '{expected}'"
    
    def test_format_priority_field_invalid_values(self):
        """測試優先級欄位標準化 - 無效值使用預設值"""
        invalid_values = ["", None, "unknown", "critical", "urgent", "123"]
        
        for invalid_val in invalid_values:
            result = self.formatter.format_priority_field(invalid_val)
            assert result == "Medium", f"無效值 '{invalid_val}' 應該使用預設值 'Medium'"
    
    def test_validate_required_fields_valid_case(self):
        """測試必要欄位驗證 - 有效案例"""
        result = self.formatter.validate_required_fields(self.valid_test_case)
        assert result is True
    
    def test_validate_required_fields_missing_fields(self):
        """測試必要欄位驗證 - 缺少欄位"""
        required_fields = [
            "test_case_number", "title", "priority", 
            "precondition", "steps", "expected_result"
        ]
        
        for field in required_fields:
            incomplete_case = self.valid_test_case.copy()
            del incomplete_case[field]
            
            result = self.formatter.validate_required_fields(incomplete_case)
            assert result is False, f"缺少欄位 '{field}' 應該驗證失敗"
    
    def test_validate_required_fields_empty_critical_fields(self):
        """測試必要欄位驗證 - 關鍵欄位為空"""
        critical_fields = ["test_case_number", "title", "steps", "expected_result"]
        
        for field in critical_fields:
            empty_case = self.valid_test_case.copy()
            empty_case[field] = ""
            
            result = self.formatter.validate_required_fields(empty_case)
            assert result is False, f"關鍵欄位 '{field}' 為空應該驗證失敗"
    
    def test_validate_required_fields_whitespace_only(self):
        """測試必要欄位驗證 - 只有空白字符"""
        whitespace_case = self.valid_test_case.copy()
        whitespace_case["title"] = "   \t\n   "
        
        result = self.formatter.validate_required_fields(whitespace_case)
        assert result is False
    
    def test_validate_required_fields_allows_empty_precondition(self):
        """測試必要欄位驗證 - 允許空前置條件"""
        empty_precondition_case = self.valid_test_case.copy()
        empty_precondition_case["precondition"] = ""
        
        result = self.formatter.validate_required_fields(empty_precondition_case)
        assert result is True, "空前置條件應該被允許"
    
    def test_batch_format_records_valid_input(self):
        """測試批次格式化 - 有效輸入"""
        test_cases = [self.valid_test_case, self.edge_case_test]
        
        results = self.formatter.batch_format_records(test_cases)
        
        # 檢查回傳列表
        assert isinstance(results, list)
        assert len(results) == 2
        
        # 檢查每筆記錄都正確格式化
        for result in results:
            assert isinstance(result, dict)
            assert "test_case_number" in result
            assert "title" in result
            assert "priority" in result
    
    def test_batch_format_records_filters_invalid(self):
        """測試批次格式化 - 過濾無效記錄"""
        invalid_case = {"title": "無效案例"}  # 缺少必要欄位
        test_cases = [self.valid_test_case, invalid_case, self.edge_case_test]
        
        results = self.formatter.batch_format_records(test_cases)
        
        # 只有有效記錄被格式化
        assert len(results) == 2
        
        # 確認都是有效記錄
        for result in results:
            validation_result = self.formatter.validate_required_fields(result)
            assert validation_result is True
    
    def test_batch_format_records_empty_input(self):
        """測試批次格式化 - 空輸入"""
        results = self.formatter.batch_format_records([])
        assert results == []
    
    def test_batch_format_records_all_invalid(self):
        """測試批次格式化 - 全部無效記錄"""
        invalid_cases = [
            {"title": "只有標題"},
            {"test_case_number": "TCG-001"},
            {}
        ]
        
        results = self.formatter.batch_format_records(invalid_cases)
        assert results == []
    
    def test_format_test_case_for_lark_none_input(self):
        """測試格式轉換 - None 輸入"""
        with pytest.raises(TypeError):
            self.formatter.format_test_case_for_lark(None)
    
    def test_format_test_case_for_lark_invalid_type(self):
        """測試格式轉換 - 錯誤類型輸入"""
        with pytest.raises(TypeError):
            self.formatter.format_test_case_for_lark("not a dict")
    
    def test_large_batch_processing(self):
        """測試大批次資料處理效能"""
        # 創建大量測試資料
        large_batch = []
        for i in range(100):
            test_case = self.valid_test_case.copy()
            test_case["test_case_number"] = f"TCG-{i:03d}.001.001"
            test_case["title"] = f"測試案例 {i}"
            large_batch.append(test_case)
        
        # 測試處理時間（應該在合理範圍內）
        import time
        start_time = time.time()
        results = self.formatter.batch_format_records(large_batch)
        processing_time = time.time() - start_time
        
        # 驗證結果
        assert len(results) == 100
        assert processing_time < 1.0, f"處理 100 筆資料耗時 {processing_time:.2f}s，超過預期"
    
    def test_unicode_and_special_characters(self):
        """測試 Unicode 和特殊字符處理"""
        unicode_case = {
            "test_case_number": "TCG-測試.001.001",
            "title": "測試中文標題 🚀 emoji test",
            "priority": "HIGH",
            "precondition": "包含特殊符號：@#$%^&*()_+-=[]{}|;':\"<>?,./",
            "steps": "步驟1：測試\n步驟2：验证\n步骤3：確認",
            "expected_result": "正確處理 Unicode: αβγδ 和 表情符號: 😀😃😄"
        }
        
        result = self.formatter.format_test_case_for_lark(unicode_case)
        
        # 檢查 Unicode 字符保持完整
        assert "測試中文標題" in result["title"]
        assert "🚀" in result["title"]
        assert "😀😃😄" in result["expected_result"]
        assert "αβγδ" in result["expected_result"]
    
    def test_field_length_limits(self):
        """測試欄位長度限制處理"""
        long_content_case = self.valid_test_case.copy()
        
        # 創建超長內容
        long_title = "超長標題 " * 100  # 約 500 字符
        long_steps = "測試步驟 " * 200   # 約 800 字符
        
        long_content_case["title"] = long_title
        long_content_case["steps"] = long_steps
        
        result = self.formatter.format_test_case_for_lark(long_content_case)
        
        # 內容應該被保留（由 Lark API 決定長度限制）
        assert result["title"] == long_title
        assert result["steps"] == long_steps
    
    def test_priority_field_normalization_edge_cases(self):
        """測試優先級欄位標準化的邊界情況"""
        edge_cases = [
            ("  High  ", "High"),  # 含空白
            ("hIGh", "High"),      # 混合大小寫
            ("MeDiUm", "Medium"),  # 混合大小寫
            ("lOW", "Low"),        # 混合大小寫
            ("", "Medium"),        # 空字串
            ("   ", "Medium"),     # 只有空白
        ]
        
        for input_val, expected in edge_cases:
            result = self.formatter.format_priority_field(input_val)
            assert result == expected, f"輸入 '{input_val}' 應該轉換為 '{expected}'"
    
    def test_data_type_consistency(self):
        """測試資料類型一致性"""
        # 測試數值型輸入
        numeric_case = self.valid_test_case.copy()
        numeric_case["test_case_number"] = 123  # 數值型
        
        result = self.formatter.format_test_case_for_lark(numeric_case)
        
        # 應該轉換為字串
        assert isinstance(result["test_case_number"], str)
        assert result["test_case_number"] == "123"
    
    def test_integration_with_data_cleaner_output(self):
        """測試與資料清理器輸出的整合"""
        # 模擬資料清理器的輸出格式
        cleaned_case = {
            "test_case_number": "TCG-001.002.003",
            "title": "登入功能測試",  # 已清理的標題
            "priority": "High",
            "precondition": "用戶已註冊",  # 已清理的前置條件
            "steps": "1. 開啟登入頁面\n2. 輸入帳號密碼",  # 已清理的步驟
            "expected_result": "成功登入系統"  # 已清理的預期結果
        }
        
        result = self.formatter.format_test_case_for_lark(cleaned_case)
        
        # 檢查格式轉換正確
        assert self.formatter.validate_required_fields(result)
        assert result["priority"] == "High"
        
        # 確保資料完整性
        for key, value in cleaned_case.items():
            assert result[key] == str(value)
    
    def test_format_test_case_for_lark_with_validation_error(self):
        """測試格式轉換時驗證錯誤的處理"""
        incomplete_case = {
            "title": "只有標題的案例"
            # 缺少其他必要欄位
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.formatter.format_test_case_for_lark(incomplete_case)
        
        assert "缺少必要欄位" in str(exc_info.value)
    
    def test_validate_required_fields_non_dict_input(self):
        """測試驗證函數處理非字典輸入"""
        non_dict_inputs = ["string", 123, [], None, True]
        
        for input_val in non_dict_inputs:
            result = self.formatter.validate_required_fields(input_val)
            assert result is False
    
    def test_batch_format_records_with_exception(self):
        """測試批次格式化時的異常處理"""
        # 創建一個會導致異常的測試案例（使用 Mock 來模擬異常）
        with patch.object(self.formatter, 'format_test_case_for_lark') as mock_format:
            mock_format.side_effect = [
                self.valid_test_case,  # 第一個成功
                Exception("模擬格式化錯誤"),  # 第二個失敗
                self.edge_case_test    # 第三個成功
            ]
            
            test_cases = [self.valid_test_case, self.valid_test_case, self.edge_case_test]
            results = self.formatter.batch_format_records(test_cases)
            
            # 只有2筆成功（第一個和第三個）
            assert len(results) == 2


class TestValidationError:
    """ValidationError 異常測試"""
    
    def test_validation_error_creation(self):
        """測試 ValidationError 異常創建"""
        error_msg = "測試驗證錯誤"
        
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError(error_msg)
        
        assert str(exc_info.value) == error_msg
    
    def test_validation_error_inheritance(self):
        """測試 ValidationError 繼承關係"""
        error = ValidationError("測試錯誤")
        assert isinstance(error, Exception)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])