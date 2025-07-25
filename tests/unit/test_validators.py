"""
資料驗證模組測試

測試各種資料驗證函數的功能，包括：
- 檔案路徑驗證
- 測試案例編號格式驗證
- 優先級值驗證
- 通用資料格式驗證
- 欄位完整性檢查
"""

import pytest
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# 加入 src 目錄到 Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from utils.validators import (
    validate_file_path,
    validate_test_case_number,
    validate_priority_value,
    validate_required_fields,
    validate_email_format,
    validate_url_format,
    ValidationError,
    FieldValidator,
    add_validation_rule,
    validate_field,
    validate_data
)


class TestValidateFilePath:
    """檔案路徑驗證測試"""
    
    def test_validate_existing_file(self):
        """測試驗證存在的檔案"""
        # 創建臨時檔案
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(b"test content")
        
        try:
            # 驗證存在的檔案
            assert validate_file_path(temp_path) is True
        finally:
            # 清理臨時檔案
            os.unlink(temp_path)
    
    def test_validate_nonexistent_file(self):
        """測試驗證不存在的檔案"""
        nonexistent_path = "/path/to/nonexistent/file.txt"
        assert validate_file_path(nonexistent_path) is False
    
    def test_validate_directory_as_file(self):
        """測試將目錄當作檔案驗證"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 目錄不應被視為有效檔案
            assert validate_file_path(temp_dir) is False
    
    def test_validate_file_with_extension_filter(self):
        """測試帶副檔名過濾的檔案驗證"""
        # 創建不同副檔名的檔案
        with tempfile.NamedTemporaryFile(suffix='.xml', delete=False) as xml_file:
            xml_path = xml_file.name
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as txt_file:
            txt_path = txt_file.name
        
        try:
            # 測試允許的副檔名
            assert validate_file_path(xml_path, allowed_extensions=['.xml']) is True
            assert validate_file_path(txt_path, allowed_extensions=['.xml']) is False
            
            # 測試多個允許的副檔名
            assert validate_file_path(xml_path, allowed_extensions=['.xml', '.txt']) is True
            assert validate_file_path(txt_path, allowed_extensions=['.xml', '.txt']) is True
        finally:
            os.unlink(xml_path)
            os.unlink(txt_path)
    
    def test_validate_file_size_limit(self):
        """測試檔案大小限制驗證"""
        # 創建大小已知的檔案
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = b"a" * 1024  # 1KB
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # 測試大小限制
            assert validate_file_path(temp_path, max_size_mb=1) is True  # 1MB 限制
            assert validate_file_path(temp_path, max_size_mb=0.0001) is False  # 0.0001MB 限制 (約100字節)
        finally:
            os.unlink(temp_path)
    
    def test_validate_empty_or_none_path(self):
        """測試空路徑或 None 值"""
        assert validate_file_path("") is False
        assert validate_file_path(None) is False
        assert validate_file_path("   ") is False  # 空白字串
    
    def test_validate_file_permissions(self):
        """測試檔案權限驗證"""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(b"test content")
        
        try:
            # 測試可讀檔案
            assert validate_file_path(temp_path, check_readable=True) is True
            
            # 模擬權限錯誤（在某些環境下可能無法測試）
            with patch('os.access', return_value=False):
                assert validate_file_path(temp_path, check_readable=True) is False
        finally:
            os.unlink(temp_path)


class TestValidateTestCaseNumber:
    """測試案例編號驗證測試"""
    
    def test_validate_standard_format(self):
        """測試標準格式驗證"""
        # 有效的測試案例編號
        valid_numbers = [
            "TCG-001.002.003",
            "TCG-123.456.789",
            "TCG-999.999.999",
            "TCG-001.001.001"
        ]
        
        for number in valid_numbers:
            assert validate_test_case_number(number) is True, f"應該通過: {number}"
    
    def test_validate_invalid_format(self):
        """測試無效格式"""
        invalid_numbers = [
            "TCG001.002.003",    # 缺少 hyphen
            "TC-001.002.003",    # 錯誤前綴
            "TCG-1.2.3",         # 數字太短
            "TCG-001.002",       # 缺少第三段
            "TCG-001.002.003.004",  # 多了一段
            "TCG-abc.def.ghi",   # 非數字
            "",                  # 空字串
            None,               # None 值
            "TCG-001.002.003.extra"  # 額外內容
        ]
        
        for number in invalid_numbers:
            assert validate_test_case_number(number) is False, f"應該失敗: {number}"
    
    def test_validate_with_custom_pattern(self):
        """測試自訂模式驗證"""
        custom_pattern = r"TEST-\d{2}\.\d{2}\.\d{2}"
        
        # 使用自訂模式的有效編號
        valid_custom = [
            "TEST-12.34.56",
            "TEST-00.00.00",
            "TEST-99.99.99"
        ]
        
        for number in valid_custom:
            assert validate_test_case_number(number, pattern=custom_pattern) is True
        
        # 原始標準格式在自訂模式下應該失敗
        assert validate_test_case_number("TCG-001.002.003", pattern=custom_pattern) is False
    
    def test_validate_case_sensitivity(self):
        """測試大小寫敏感性"""
        # 測試小寫
        assert validate_test_case_number("tcg-001.002.003") is False
        
        # 測試混合大小寫
        assert validate_test_case_number("Tcg-001.002.003") is False
        assert validate_test_case_number("TCg-001.002.003") is False
    
    def test_validate_whitespace_handling(self):
        """測試空白字符處理"""
        # 前後空白應該被清理並通過驗證
        assert validate_test_case_number("  TCG-001.002.003  ", strip_whitespace=True) is True
        
        # 不清理空白時應該失敗
        assert validate_test_case_number("  TCG-001.002.003  ", strip_whitespace=False) is False
        
        # 中間空白應該失敗
        assert validate_test_case_number("TCG-001. 002.003") is False
        assert validate_test_case_number("TCG-001.002 .003") is False


class TestValidatePriorityValue:
    """優先級值驗證測試"""
    
    def test_validate_standard_priorities(self):
        """測試標準優先級值"""
        valid_priorities = ["High", "Medium", "Low"]
        
        for priority in valid_priorities:
            assert validate_priority_value(priority) is True, f"應該通過: {priority}"
    
    def test_validate_case_insensitive(self):
        """測試大小寫不敏感"""
        case_variations = [
            "high", "HIGH", "High", "HiGh",
            "medium", "MEDIUM", "Medium", "MeDiUm",
            "low", "LOW", "Low", "LoW"
        ]
        
        for priority in case_variations:
            assert validate_priority_value(priority) is True, f"應該通過: {priority}"
    
    def test_validate_invalid_priorities(self):
        """測試無效優先級值"""
        invalid_priorities = [
            "Critical",    # 不在標準列表中
            "Normal",      # 不在標準列表中
            "Urgent",      # 不在標準列表中
            "",           # 空字串
            None,         # None 值
            "123",        # 數字
            "High-Priority"  # 包含特殊字符
        ]
        
        for priority in invalid_priorities:
            assert validate_priority_value(priority) is False, f"應該失敗: {priority}"
    
    def test_validate_with_custom_values(self):
        """測試自訂優先級值"""
        custom_values = ["Critical", "High", "Normal", "Low"]
        
        # 測試自訂值列表
        assert validate_priority_value("Critical", allowed_values=custom_values) is True
        assert validate_priority_value("Normal", allowed_values=custom_values) is True
        
        # 原本有效的 Medium 在自訂列表中無效
        assert validate_priority_value("Medium", allowed_values=custom_values) is False
    
    def test_validate_whitespace_handling(self):
        """測試空白字符處理"""
        # 前後空白應該被處理
        assert validate_priority_value("  High  ") is True
        assert validate_priority_value("\tMedium\n") is True
        
        # 中間空白應該失敗
        assert validate_priority_value("Hi gh") is False


class TestValidateRequiredFields:
    """必要欄位驗證測試"""
    
    def test_validate_complete_data(self):
        """測試完整資料驗證"""
        complete_data = {
            "test_case_number": "TCG-001.002.003",
            "title": "測試標題",
            "priority": "High",
            "precondition": "前置條件",
            "steps": "測試步驟",
            "expected_result": "預期結果"
        }
        
        required_fields = ["test_case_number", "title", "priority", "steps", "expected_result"]
        
        assert validate_required_fields(complete_data, required_fields) is True
    
    def test_validate_missing_fields(self):
        """測試缺失欄位"""
        incomplete_data = {
            "test_case_number": "TCG-001.002.003",
            "title": "測試標題",
            # 缺少 priority
            "steps": "測試步驟",
            "expected_result": "預期結果"
        }
        
        required_fields = ["test_case_number", "title", "priority", "steps", "expected_result"]
        
        assert validate_required_fields(incomplete_data, required_fields) is False
    
    def test_validate_empty_values(self):
        """測試空值處理"""
        data_with_empty = {
            "test_case_number": "TCG-001.002.003",
            "title": "",  # 空字串
            "priority": "High",
            "steps": None,  # None 值
            "expected_result": "   "  # 只有空白
        }
        
        required_fields = ["test_case_number", "title", "priority", "steps", "expected_result"]
        
        # 預設情況下，空值應該導致驗證失敗
        assert validate_required_fields(data_with_empty, required_fields) is False
        
        # 允許空值時應該通過
        assert validate_required_fields(data_with_empty, required_fields, allow_empty=True) is True
    
    def test_validate_extra_fields(self):
        """測試額外欄位處理"""
        data_with_extra = {
            "test_case_number": "TCG-001.002.003",
            "title": "測試標題",
            "priority": "High",
            "steps": "測試步驟",
            "expected_result": "預期結果",
            "extra_field": "額外資料"  # 額外欄位
        }
        
        required_fields = ["test_case_number", "title", "priority", "steps", "expected_result"]
        
        # 額外欄位不應影響驗證結果
        assert validate_required_fields(data_with_extra, required_fields) is True


class TestValidateEmailFormat:
    """電子郵件格式驗證測試"""
    
    def test_validate_valid_emails(self):
        """測試有效的電子郵件地址"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "test123@test-domain.org",
            "user+tag@example.com",
            "test_user@subdomain.example.com"
        ]
        
        for email in valid_emails:
            assert validate_email_format(email) is True, f"應該通過: {email}"
    
    def test_validate_invalid_emails(self):
        """測試無效的電子郵件地址"""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "test@.com",
            "test..test@example.com",
            "",
            None
        ]
        
        for email in invalid_emails:
            assert validate_email_format(email) is False, f"應該失敗: {email}"


class TestValidateUrlFormat:
    """URL 格式驗證測試"""
    
    def test_validate_valid_urls(self):
        """測試有效的 URL"""
        valid_urls = [
            "http://example.com",
            "https://www.example.com",
            "https://subdomain.example.com/path",
            "http://example.com:8080/path?query=value",
            "https://example.com/path#anchor"
        ]
        
        for url in valid_urls:
            assert validate_url_format(url) is True, f"應該通過: {url}"
    
    def test_validate_invalid_urls(self):
        """測試無效的 URL"""
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",  # 不支援的協議
            "http://",
            "https://",
            "",
            None
        ]
        
        for url in invalid_urls:
            assert validate_url_format(url) is False, f"應該失敗: {url}"


class TestFieldValidator:
    """FieldValidator 類別測試"""
    
    def test_field_validator_initialization(self):
        """測試 FieldValidator 初始化"""
        validator = FieldValidator()
        
        assert hasattr(validator, 'add_rule')
        assert hasattr(validator, 'validate')
        assert hasattr(validator, 'validate_batch')
    
    def test_add_custom_rule(self):
        """測試添加自訂驗證規則"""
        validator = FieldValidator()
        
        # 添加自訂規則
        def custom_rule(value):
            return isinstance(value, str) and len(value) >= 5
        
        validator.add_rule("min_length_5", custom_rule)
        
        # 測試自訂規則
        assert validator.validate("test field", ["min_length_5"]) is True
        assert validator.validate("abc", ["min_length_5"]) is False
    
    def test_validate_with_multiple_rules(self):
        """測試多重規則驗證"""
        validator = FieldValidator()
        
        # 使用多個內建規則
        rules = ["required", "string", "min_length:3"]
        
        assert validator.validate("valid", rules) is True
        assert validator.validate("", rules) is False  # 不滿足 required
        assert validator.validate(123, rules) is False  # 不滿足 string
        assert validator.validate("ab", rules) is False  # 不滿足 min_length:3
    
    def test_validate_batch(self):
        """測試批次驗證"""
        validator = FieldValidator()
        
        data = {
            "name": "測試名稱",
            "email": "test@example.com",
            "age": 25
        }
        
        rules = {
            "name": ["required", "string"],
            "email": ["required", "email"],
            "age": ["required", "integer", "min:0"]
        }
        
        result = validator.validate_batch(data, rules)
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_batch_with_errors(self):
        """測試批次驗證錯誤處理"""
        validator = FieldValidator()
        
        data = {
            "name": "",  # 空名稱
            "email": "invalid-email",  # 無效電子郵件
            "age": -5  # 負數年齡
        }
        
        rules = {
            "name": ["required", "string"],
            "email": ["required", "email"],
            "age": ["required", "integer", "min:0"]
        }
        
        result = validator.validate_batch(data, rules)
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert "name" in result.errors
        assert "email" in result.errors
        assert "age" in result.errors


class TestValidationError:
    """ValidationError 異常測試"""
    
    def test_validation_error_creation(self):
        """測試 ValidationError 創建"""
        error_msg = "驗證失敗"
        
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError(error_msg)
        
        assert str(exc_info.value) == error_msg
    
    def test_validation_error_with_field_info(self):
        """測試帶欄位資訊的 ValidationError"""
        error = ValidationError("驗證失敗", field="test_field", value="invalid_value")
        
        assert error.field == "test_field"
        assert error.value == "invalid_value"
        assert "驗證失敗" in str(error)
    
    def test_validation_error_inheritance(self):
        """測試 ValidationError 繼承關係"""
        error = ValidationError("測試錯誤")
        assert isinstance(error, Exception)


class TestGlobalValidatorFunctions:
    """全域驗證函數測試"""
    
    def test_add_validation_rule(self):
        """測試添加全域驗證規則"""
        # 添加自訂規則
        def custom_length_rule(value, min_len="5"):
            try:
                min_length = int(min_len)
                return isinstance(value, str) and len(value) >= min_length
            except (ValueError, TypeError):
                return False
        
        add_validation_rule("custom_min_length", custom_length_rule)
        
        # 測試使用自訂規則
        assert validate_field("test_value", ["custom_min_length:4"]) is True
        assert validate_field("test", ["custom_min_length:5"]) is False
    
    def test_validate_field(self):
        """測試全域欄位驗證"""
        # 測試基本規則
        assert validate_field("test@example.com", ["required", "email"]) is True
        assert validate_field("", ["required"]) is False
        assert validate_field(123, ["required", "integer"]) is True
        assert validate_field("123", ["integer"]) is False
    
    def test_validate_data(self):
        """測試全域資料驗證"""
        test_data = {
            "name": "測試用戶",
            "email": "test@example.com",
            "age": 25
        }
        
        validation_rules = {
            "name": ["required", "string"],
            "email": ["required", "email"],
            "age": ["required", "integer", "min:0"]
        }
        
        result = validate_data(test_data, validation_rules)
        assert result.is_valid is True
        assert len(result.errors) == 0
        
        # 測試錯誤情況
        invalid_data = {
            "name": "",  # 空名稱
            "email": "invalid-email",  # 無效電子郵件
            "age": -5  # 負數
        }
        
        result = validate_data(invalid_data, validation_rules)
        assert result.is_valid is False
        assert len(result.errors) > 0


class TestValidationResultHelpers:
    """ValidationResult 輔助方法測試"""
    
    def test_validation_result_add_error(self):
        """測試 ValidationResult 添加錯誤"""
        from utils.validators import ValidationResult
        
        result = ValidationResult(is_valid=True, errors={})
        
        # 添加錯誤
        result.add_error("field1", "錯誤訊息1")
        assert result.is_valid is False
        assert "field1" in result.errors
        assert "錯誤訊息1" in result.errors["field1"]
        
        # 添加同一欄位的另一個錯誤
        result.add_error("field1", "錯誤訊息2")
        assert len(result.errors["field1"]) == 2
        assert "錯誤訊息2" in result.errors["field1"]


class TestFieldValidatorEdgeCases:
    """FieldValidator 邊界情況測試"""
    
    def test_field_validator_unknown_rule(self):
        """測試未知規則處理"""
        validator = FieldValidator()
        
        # 未知規則應該返回 False
        assert validator.validate("test", ["unknown_rule"]) is False
    
    def test_field_validator_rule_with_invalid_parameter(self):
        """測試帶無效參數的規則"""
        validator = FieldValidator()
        
        # 無效的數字參數
        assert validator.validate("test", ["min_length:invalid"]) is False
        assert validator.validate(25, ["min:invalid"]) is False
    
    def test_field_validator_edge_values(self):
        """測試邊界值"""
        validator = FieldValidator()
        
        # 測試空字串
        assert validator.validate("", ["string"]) is True
        assert validator.validate("", ["required"]) is False
        
        # 測試零值
        assert validator.validate(0, ["integer"]) is True
        assert validator.validate(0, ["min:0"]) is True
        assert validator.validate(0, ["min:1"]) is False
        
        # 測試布林值（不應被視為整數）
        assert validator.validate(True, ["integer"]) is False
        assert validator.validate(False, ["integer"]) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])