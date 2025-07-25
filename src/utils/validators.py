"""
資料驗證模組

提供各種資料驗證功能，包括：
- 檔案路徑驗證
- 測試案例編號格式驗證
- 優先級值驗證
- 通用資料格式驗證
- 欄位完整性檢查
- 電子郵件和 URL 格式驗證
"""

import os
import re
from typing import Dict, List, Any, Optional, Union, Callable
from pathlib import Path
from dataclasses import dataclass


class ValidationError(Exception):
    """資料驗證錯誤的自訂異常"""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        """
        初始化驗證錯誤
        
        Args:
            message: 錯誤訊息
            field: 相關欄位名稱
            value: 導致錯誤的值
        """
        super().__init__(message)
        self.field = field
        self.value = value


@dataclass
class ValidationResult:
    """驗證結果"""
    is_valid: bool
    errors: Dict[str, List[str]]
    
    def add_error(self, field: str, message: str):
        """添加錯誤訊息"""
        if field not in self.errors:
            self.errors[field] = []
        self.errors[field].append(message)
        self.is_valid = False


def validate_file_path(file_path: Union[str, Path, None], 
                      allowed_extensions: Optional[List[str]] = None,
                      max_size_mb: Optional[float] = None,
                      check_readable: bool = False) -> bool:
    """
    驗證檔案路徑有效性
    
    Args:
        file_path: 要驗證的檔案路徑
        allowed_extensions: 允許的副檔名列表（如 ['.xml', '.txt']）
        max_size_mb: 最大檔案大小（MB）
        check_readable: 是否檢查檔案可讀性
        
    Returns:
        檔案路徑是否有效
        
    Examples:
        >>> validate_file_path("/path/to/file.xml")
        True  # 如果檔案存在
        
        >>> validate_file_path("/path/to/file.txt", allowed_extensions=['.xml'])
        False  # 副檔名不符
        
        >>> validate_file_path("/path/to/large_file.xml", max_size_mb=1)
        False  # 如果檔案超過 1MB
    """
    # 檢查空值
    if not file_path or (isinstance(file_path, str) and not file_path.strip()):
        return False
    
    try:
        path = Path(file_path)
        
        # 檢查檔案是否存在
        if not path.exists():
            return False
        
        # 檢查是否為檔案（不是目錄）
        if not path.is_file():
            return False
        
        # 檢查副檔名
        if allowed_extensions:
            if path.suffix.lower() not in [ext.lower() for ext in allowed_extensions]:
                return False
        
        # 檢查檔案大小
        if max_size_mb is not None:
            file_size_mb = path.stat().st_size / (1024 * 1024)
            if file_size_mb > max_size_mb:
                return False
        
        # 檢查可讀性
        if check_readable:
            if not os.access(path, os.R_OK):
                return False
        
        return True
        
    except (OSError, ValueError, TypeError):
        return False


def validate_test_case_number(case_number: Union[str, None], 
                             pattern: Optional[str] = None,
                             strip_whitespace: bool = True) -> bool:
    """
    驗證測試案例編號格式
    
    Args:
        case_number: 測試案例編號
        pattern: 自訂正則表達式模式（預設為 TCG-XXX.YYY.ZZZ 格式）
        strip_whitespace: 是否清理前後空白
        
    Returns:
        編號格式是否有效
        
    Examples:
        >>> validate_test_case_number("TCG-001.002.003")
        True
        
        >>> validate_test_case_number("TCG001.002.003")
        False  # 缺少 hyphen
        
        >>> validate_test_case_number("TEST-12.34.56", pattern=r"TEST-\\d{2}\\.\\d{2}\\.\\d{2}")
        True
    """
    # 檢查空值
    if not case_number:
        return False
    
    # 清理空白字符
    if strip_whitespace and isinstance(case_number, str):
        case_number = case_number.strip()
    
    # 使用預設模式或自訂模式
    if pattern is None:
        # 標準 TCG-XXX.YYY.ZZZ 格式
        pattern = r'^TCG-\d{3}\.\d{3}\.\d{3}$'
    
    try:
        return bool(re.match(pattern, case_number))
    except (re.error, TypeError):
        return False


def validate_priority_value(priority: Union[str, None], 
                           allowed_values: Optional[List[str]] = None) -> bool:
    """
    驗證優先級值有效性
    
    Args:
        priority: 優先級值
        allowed_values: 允許的優先級值列表（預設為 ["High", "Medium", "Low"]）
        
    Returns:
        優先級值是否有效
        
    Examples:
        >>> validate_priority_value("High")
        True
        
        >>> validate_priority_value("high")
        True  # 大小寫不敏感
        
        >>> validate_priority_value("Critical")
        False  # 不在預設列表中
        
        >>> validate_priority_value("Critical", allowed_values=["Critical", "High", "Low"])
        True
    """
    # 檢查空值
    if not priority:
        return False
    
    # 使用預設值或自訂值
    if allowed_values is None:
        allowed_values = ["High", "Medium", "Low"]
    
    # 清理空白並轉換為小寫進行比較
    try:
        priority_clean = priority.strip().lower()
        allowed_lower = [val.lower() for val in allowed_values]
        return priority_clean in allowed_lower
    except (AttributeError, TypeError):
        return False


def validate_required_fields(data: Dict[str, Any], 
                            required_fields: List[str],
                            allow_empty: bool = False) -> bool:
    """
    驗證必要欄位完整性
    
    Args:
        data: 要驗證的資料字典
        required_fields: 必要欄位列表
        allow_empty: 是否允許空值
        
    Returns:
        所有必要欄位是否都存在且有效
        
    Examples:
        >>> data = {"name": "測試", "email": "test@example.com"}
        >>> validate_required_fields(data, ["name", "email"])
        True
        
        >>> validate_required_fields(data, ["name", "email", "phone"])
        False  # 缺少 phone 欄位
        
        >>> data_with_empty = {"name": "", "email": "test@example.com"}
        >>> validate_required_fields(data_with_empty, ["name", "email"])
        False  # name 為空
        
        >>> validate_required_fields(data_with_empty, ["name", "email"], allow_empty=True)
        True  # 允許空值
    """
    if not isinstance(data, dict) or not isinstance(required_fields, list):
        return False
    
    for field in required_fields:
        # 檢查欄位是否存在
        if field not in data:
            return False
        
        # 檢查值是否有效（如果不允許空值）
        if not allow_empty:
            value = data[field]
            if value is None:
                return False
            if isinstance(value, str) and not value.strip():
                return False
    
    return True


def validate_email_format(email: Union[str, None]) -> bool:
    """
    驗證電子郵件格式
    
    Args:
        email: 電子郵件地址
        
    Returns:
        電子郵件格式是否有效
        
    Examples:
        >>> validate_email_format("test@example.com")
        True
        
        >>> validate_email_format("invalid-email")
        False
    """
    if not email:
        return False
    
    # 基本電子郵件格式驗證（平衡版）
    # 允許 + 符號，但不允許連續的點
    if '..' in email:
        return False
    
    email_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9._+%-]*[a-zA-Z0-9])?@[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}$'
    
    try:
        return bool(re.match(email_pattern, email.strip()))
    except (AttributeError, TypeError):
        return False


def validate_url_format(url: Union[str, None], 
                       allowed_schemes: Optional[List[str]] = None) -> bool:
    """
    驗證 URL 格式
    
    Args:
        url: URL 地址
        allowed_schemes: 允許的協議列表（預設為 ["http", "https"]）
        
    Returns:
        URL 格式是否有效
        
    Examples:
        >>> validate_url_format("https://www.example.com")
        True
        
        >>> validate_url_format("ftp://example.com")
        False  # FTP 不在預設允許列表中
        
        >>> validate_url_format("ftp://example.com", allowed_schemes=["ftp", "http", "https"])
        True
    """
    if not url:
        return False
    
    if allowed_schemes is None:
        allowed_schemes = ["http", "https"]
    
    # 基本 URL 格式驗證
    url_pattern = r'^(' + '|'.join(allowed_schemes) + r')://[^\s/$.?#].[^\s]*$'
    
    try:
        return bool(re.match(url_pattern, url.strip(), re.IGNORECASE))
    except (AttributeError, TypeError):
        return False


class FieldValidator:
    """欄位驗證器，支援自訂規則和批次驗證"""
    
    def __init__(self):
        """初始化欄位驗證器"""
        self.rules: Dict[str, Callable] = {
            'required': self._validate_required,
            'string': self._validate_string,
            'integer': self._validate_integer,
            'float': self._validate_float,
            'email': self._validate_email,
            'url': self._validate_url,
            'min_length': self._validate_min_length,
            'max_length': self._validate_max_length,
            'min': self._validate_min_value,
            'max': self._validate_max_value
        }
    
    def add_rule(self, name: str, validator: Callable[[Any], bool]):
        """
        添加自訂驗證規則
        
        Args:
            name: 規則名稱
            validator: 驗證函數，接受值並返回布林結果
        """
        self.rules[name] = validator
    
    def validate(self, value: Any, rules: List[str]) -> bool:
        """
        驗證單個值
        
        Args:
            value: 要驗證的值
            rules: 規則列表（如 ["required", "string", "min_length:5"]）
            
        Returns:
            驗證是否通過
        """
        for rule in rules:
            if ':' in rule:
                rule_name, rule_param = rule.split(':', 1)
            else:
                rule_name, rule_param = rule, None
            
            if rule_name in self.rules:
                if rule_param:
                    # 帶參數的規則
                    if not self.rules[rule_name](value, rule_param):
                        return False
                else:
                    # 無參數的規則
                    if not self.rules[rule_name](value):
                        return False
            else:
                # 未知規則視為失敗
                return False
        
        return True
    
    def validate_batch(self, data: Dict[str, Any], 
                      rules: Dict[str, List[str]]) -> ValidationResult:
        """
        批次驗證多個欄位
        
        Args:
            data: 要驗證的資料
            rules: 規則字典，鍵為欄位名，值為規則列表
            
        Returns:
            ValidationResult 包含驗證結果和錯誤資訊
        """
        result = ValidationResult(is_valid=True, errors={})
        
        for field, field_rules in rules.items():
            if field in data:
                value = data[field]
                if not self.validate(value, field_rules):
                    result.add_error(field, f"欄位 {field} 驗證失敗")
            else:
                # 欄位不存在，檢查是否需要該欄位
                if 'required' in field_rules:
                    result.add_error(field, f"缺少必要欄位 {field}")
        
        return result
    
    # 內建驗證規則
    def _validate_required(self, value: Any) -> bool:
        """驗證值不為空"""
        if value is None:
            return False
        if isinstance(value, str) and not value.strip():
            return False
        return True
    
    def _validate_string(self, value: Any) -> bool:
        """驗證值為字串"""
        return isinstance(value, str)
    
    def _validate_integer(self, value: Any) -> bool:
        """驗證值為整數"""
        return isinstance(value, int) and not isinstance(value, bool)
    
    def _validate_float(self, value: Any) -> bool:
        """驗證值為浮點數"""
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    
    def _validate_email(self, value: Any) -> bool:
        """驗證電子郵件格式"""
        return validate_email_format(value)
    
    def _validate_url(self, value: Any) -> bool:
        """驗證 URL 格式"""
        return validate_url_format(value)
    
    def _validate_min_length(self, value: Any, min_length: str) -> bool:
        """驗證最小長度"""
        try:
            min_len = int(min_length)
            if hasattr(value, '__len__'):
                return len(value) >= min_len
            return False
        except (ValueError, TypeError):
            return False
    
    def _validate_max_length(self, value: Any, max_length: str) -> bool:
        """驗證最大長度"""
        try:
            max_len = int(max_length)
            if hasattr(value, '__len__'):
                return len(value) <= max_len
            return False
        except (ValueError, TypeError):
            return False
    
    def _validate_min_value(self, value: Any, min_value: str) -> bool:
        """驗證最小值"""
        try:
            min_val = float(min_value)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return value >= min_val
            return False
        except (ValueError, TypeError):
            return False
    
    def _validate_max_value(self, value: Any, max_value: str) -> bool:
        """驗證最大值"""
        try:
            max_val = float(max_value)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return value <= max_val
            return False
        except (ValueError, TypeError):
            return False


# 便利函數，創建全域驗證器實例
_global_validator = FieldValidator()


def add_validation_rule(name: str, validator: Callable[[Any], bool]):
    """添加全域驗證規則"""
    _global_validator.add_rule(name, validator)


def validate_field(value: Any, rules: List[str]) -> bool:
    """使用全域驗證器驗證欄位"""
    return _global_validator.validate(value, rules)


def validate_data(data: Dict[str, Any], rules: Dict[str, List[str]]) -> ValidationResult:
    """使用全域驗證器批次驗證資料"""
    return _global_validator.validate_batch(data, rules)