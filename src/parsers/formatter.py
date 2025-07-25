"""
格式轉換器模組

將清理後的測試案例資料轉換為 Lark 可接受的格式
專注於資料格式標準化、必要欄位驗證和批次處理
"""

import logging
from typing import Dict, List, Any, Union


class ValidationError(Exception):
    """資料驗證錯誤"""
    pass


class LarkDataFormatter:
    """Lark 資料格式轉換器"""
    
    def __init__(self):
        """初始化格式轉換器"""
        self.logger = logging.getLogger(f"{__name__}.LarkDataFormatter")
        
        # 優先級標準值對應表
        self._priority_mapping = {
            "high": "High",
            "medium": "Medium", 
            "low": "Low"
        }
        
        # 必要欄位定義
        self._required_fields = [
            "test_case_number", "title", "priority",
            "precondition", "steps", "expected_result"
        ]
        
        # 關鍵欄位（不可為空）
        self._critical_fields = [
            "test_case_number", "title", "steps", "expected_result"
        ]
        
        self.logger.debug("LarkDataFormatter 初始化完成")
    
    def format_test_case_for_lark(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        將清理後的測試案例轉換為 Lark 可接受的格式
        
        Args:
            test_case: 清理後的測試案例資料
            
        Returns:
            Lark 格式的記錄資料
            
        Raises:
            TypeError: 當輸入不是字典類型時
            ValidationError: 當必要欄位缺失時
        """
        if not isinstance(test_case, dict):
            raise TypeError("輸入必須是字典類型")
        
        # 驗證必要欄位
        if not self.validate_required_fields(test_case):
            missing_fields = [
                field for field in self._required_fields 
                if field not in test_case
            ]
            raise ValidationError(f"缺少必要欄位: {missing_fields}")
        
        # 格式化每個欄位
        formatted_record = {}
        
        # 直接複製並轉換為字串類型
        formatted_record["test_case_number"] = str(test_case["test_case_number"])
        formatted_record["title"] = str(test_case["title"])
        formatted_record["precondition"] = str(test_case["precondition"])
        formatted_record["steps"] = str(test_case["steps"])
        formatted_record["expected_result"] = str(test_case["expected_result"])
        
        # 特殊處理優先級欄位
        formatted_record["priority"] = self.format_priority_field(test_case["priority"])
        
        self.logger.debug(f"成功格式化測試案例: {formatted_record['test_case_number']}")
        return formatted_record
    
    def format_priority_field(self, priority: Union[str, Any]) -> str:
        """
        格式化優先級欄位為 Lark 單選欄位可接受的值
        
        Args:
            priority: 原始優先級值
            
        Returns:
            標準化的優先級值 (High/Medium/Low)
        """
        if priority is None:
            return "Medium"
        
        # 轉換為字串並清理空白
        priority_str = str(priority).strip().lower()
        
        # 空值處理
        if not priority_str:
            return "Medium"
        
        # 根據對應表轉換
        return self._priority_mapping.get(priority_str, "Medium")
    
    def validate_required_fields(self, test_case: Dict[str, Any]) -> bool:
        """
        驗證測試案例是否包含所有必要欄位
        
        Args:
            test_case: 測試案例資料
            
        Returns:
            是否通過驗證
        """
        if not isinstance(test_case, dict):
            return False
        
        # 檢查必要欄位存在
        for field in self._required_fields:
            if field not in test_case:
                self.logger.warning(f"缺少必要欄位: {field}")
                return False
        
        # 檢查關鍵欄位不為空
        for field in self._critical_fields:
            value = test_case.get(field)
            if not value or not str(value).strip():
                self.logger.warning(f"關鍵欄位 '{field}' 不能為空")
                return False
        
        return True
    
    def batch_format_records(self, test_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批次格式化多筆測試案例
        
        Args:
            test_cases: 測試案例列表
            
        Returns:
            格式化後的記錄列表
        """
        if not test_cases:
            return []
        
        formatted_records = []
        error_count = 0
        
        for i, test_case in enumerate(test_cases):
            try:
                # 驗證必要欄位
                if not self.validate_required_fields(test_case):
                    error_count += 1
                    self.logger.warning(f"跳過無效記錄 {i+1}: 欄位驗證失敗")
                    continue
                
                # 格式化記錄
                formatted_record = self.format_test_case_for_lark(test_case)
                formatted_records.append(formatted_record)
                
            except Exception as e:
                error_count += 1
                self.logger.error(f"格式化記錄 {i+1} 時發生錯誤: {str(e)}")
                continue
        
        success_count = len(formatted_records)
        self.logger.info(f"批次格式化完成: 成功 {success_count} 筆，錯誤 {error_count} 筆")
        
        return formatted_records