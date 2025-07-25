"""
工具函數模組整合測試

測試工具函數模組之間的整合和與其他模組的相容性，包括：
- 日誌管理和資料驗證的整合
- 與配置管理的整合
- 實際使用場景的完整流程測試
- 錯誤處理和恢復機制
"""

import pytest
import sys
import os
import tempfile
import logging
from pathlib import Path
from unittest.mock import Mock, patch

# 加入 src 目錄到 Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from utils.logger import setup_logger, LoggerManager, get_logger_manager
from utils.validators import (
    validate_file_path, validate_test_case_number, validate_priority_value,
    validate_required_fields, FieldValidator, ValidationError
)
from config.config_manager import ConfigManager


class TestLoggerValidatorIntegration:
    """日誌管理器和驗證器整合測試"""
    
    def setup_method(self):
        """每個測試方法前的設定"""
        # 清理日誌管理器
        get_logger_manager().cleanup()
        # 重置全域格式
        manager = get_logger_manager()
        manager._global_format = None
        manager._global_level = None
    
    def test_logger_with_validation_workflow(self):
        """測試日誌記錄驗證工作流程"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "validation_workflow.log")
            logger = setup_logger("validation_workflow", log_file=log_file)
            
            # 模擬一個驗證工作流程
            test_data = {
                "test_case_number": "TCG-001.002.003",
                "title": "整合測試案例",
                "priority": "High",
                "steps": "執行整合測試",
                "expected_result": "測試通過"
            }
            
            logger.info("開始驗證測試資料")
            
            # 驗證測試案例編號
            if validate_test_case_number(test_data["test_case_number"]):
                logger.info(f"測試案例編號驗證通過: {test_data['test_case_number']}")
            else:
                logger.error(f"測試案例編號驗證失敗: {test_data['test_case_number']}")
            
            # 驗證優先級
            if validate_priority_value(test_data["priority"]):
                logger.info(f"優先級驗證通過: {test_data['priority']}")
            else:
                logger.error(f"優先級驗證失敗: {test_data['priority']}")
            
            # 驗證必要欄位
            required_fields = ["test_case_number", "title", "steps", "expected_result"]
            if validate_required_fields(test_data, required_fields):
                logger.info("必要欄位驗證通過")
            else:
                logger.error("必要欄位驗證失敗")
            
            logger.info("驗證工作流程完成")
            
            # 檢查日誌檔案內容
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            # 驗證日誌包含預期內容
            assert "開始驗證測試資料" in log_content
            assert "測試案例編號驗證通過" in log_content
            assert "優先級驗證通過" in log_content
            assert "必要欄位驗證通過" in log_content
            assert "驗證工作流程完成" in log_content
    
    def test_logger_with_validation_errors(self):
        """測試日誌記錄驗證錯誤"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "validation_errors.log")
            logger = setup_logger("validation_errors", log_file=log_file, level=logging.WARNING)
            
            # 模擬無效資料
            invalid_data = {
                "test_case_number": "INVALID-001",  # 無效格式
                "priority": "Critical",  # 不在預設列表中
                "title": ""  # 空標題
            }
            
            # 驗證並記錄錯誤
            if not validate_test_case_number(invalid_data["test_case_number"]):
                logger.warning(f"測試案例編號格式錯誤: {invalid_data['test_case_number']}")
            
            if not validate_priority_value(invalid_data["priority"]):
                logger.warning(f"優先級值無效: {invalid_data['priority']}")
            
            required_fields = ["test_case_number", "title", "priority"]
            if not validate_required_fields(invalid_data, required_fields):
                logger.error("必要欄位驗證失敗")
            
            # 檢查日誌檔案內容
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            assert "測試案例編號格式錯誤" in log_content
            assert "優先級值無效" in log_content
            assert "必要欄位驗證失敗" in log_content
    
    def test_field_validator_with_logging(self):
        """測試 FieldValidator 與日誌記錄整合"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "field_validation.log")
            logger = setup_logger("field_validation", log_file=log_file)
            
            validator = FieldValidator()
            
            # 測試資料和規則
            test_data = {
                "name": "測試用戶",
                "email": "test@example.com",
                "age": 25,
                "score": 85.5
            }
            
            validation_rules = {
                "name": ["required", "string", "min_length:2"],
                "email": ["required", "email"],
                "age": ["required", "integer", "min:0", "max:150"],
                "score": ["required", "float", "min:0", "max:100"]
            }
            
            logger.info("開始批次驗證")
            result = validator.validate_batch(test_data, validation_rules)
            
            if result.is_valid:
                logger.info("所有欄位驗證通過")
            else:
                logger.error("驗證失敗:")
                for field, errors in result.errors.items():
                    for error in errors:
                        logger.error(f"  {field}: {error}")
            
            # 檢查日誌內容
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            assert "開始批次驗證" in log_content
            assert "所有欄位驗證通過" in log_content


class TestUtilsConfigIntegration:
    """工具函數與配置管理整合測試"""
    
    def setup_method(self):
        """每個測試方法前的設定"""
        # 清理日誌管理器
        get_logger_manager().cleanup()
        # 重置全域格式
        manager = get_logger_manager()
        manager._global_format = None
        manager._global_level = None
    
    def test_logger_with_config_manager(self):
        """測試日誌管理器與配置管理器整合"""
        # 模擬配置資料
        mock_logging_config = {
            "level": "DEBUG",
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "file": "logs/config_integration.log"
        }
        
        with patch('config.config_manager.ConfigManager') as mock_config_manager_class:
            mock_config_manager = Mock()
            mock_config_manager.load_config.return_value = None
            mock_config_manager.get_logging_config.return_value = mock_logging_config
            mock_config_manager_class.return_value = mock_config_manager
            
            # 使用配置檔案創建 logger
            logger = setup_logger("config_integration", config_path="test_config.yaml")
            
            # 驗證配置被正確使用
            assert logger.level == logging.DEBUG
            mock_config_manager.load_config.assert_called_once_with("test_config.yaml")
            mock_config_manager.get_logging_config.assert_called_once()
    
    def test_validator_with_config_patterns(self):
        """測試驗證器使用配置管理中的模式"""
        # 模擬配置管理器
        with patch('config.config_manager.ConfigManager') as mock_config_manager_class:
            mock_config = Mock()
            mock_processing_config = {
                "test_case_number_pattern": "CUSTOM-\\d{2}\\.\\d{2}\\.\\d{2}",
                "required_fields": ["id", "name", "description"]
            }
            mock_config.get_processing_config.return_value = mock_processing_config
            mock_config_manager_class.return_value = mock_config
            
            # 從配置載入自訂模式
            config_manager = mock_config_manager_class()
            processing_config = config_manager.get_processing_config()
            custom_pattern = processing_config["test_case_number_pattern"]
            
            # 使用自訂模式驗證
            valid_number = "CUSTOM-12.34.56"
            invalid_number = "TCG-001.002.003"
            
            assert validate_test_case_number(valid_number, pattern=custom_pattern) is True
            assert validate_test_case_number(invalid_number, pattern=custom_pattern) is False


class TestFileValidationWithLogging:
    """檔案驗證與日誌記錄整合測試"""
    
    def setup_method(self):
        """每個測試方法前的設定"""
        # 清理日誌管理器
        get_logger_manager().cleanup()
        # 重置全域格式
        manager = get_logger_manager()
        manager._global_format = None
        manager._global_level = None
    
    def test_file_validation_workflow(self):
        """測試檔案驗證工作流程"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "file_validation.log")
            logger = setup_logger("file_validation", log_file=log_file)
            
            # 創建測試檔案
            test_file_path = os.path.join(temp_dir, "test.xml")
            with open(test_file_path, 'w', encoding='utf-8') as f:
                f.write("<test>測試內容</test>")
            
            # 模擬檔案驗證流程
            files_to_validate = [
                test_file_path,
                "/non/existent/file.xml",
                os.path.join(temp_dir, "test.txt")  # 錯誤副檔名
            ]
            
            # 創建 .txt 檔案用於測試
            txt_file = os.path.join(temp_dir, "test.txt")
            with open(txt_file, 'w') as f:
                f.write("text file")
            
            allowed_extensions = ['.xml']
            max_size_mb = 1
            
            logger.info("開始檔案驗證流程")
            
            valid_files = []
            for file_path in files_to_validate:
                logger.info(f"驗證檔案: {file_path}")
                
                if validate_file_path(file_path, allowed_extensions=allowed_extensions, max_size_mb=max_size_mb):
                    logger.info(f"檔案驗證通過: {file_path}")
                    valid_files.append(file_path)
                else:
                    logger.warning(f"檔案驗證失敗: {file_path}")
            
            logger.info(f"驗證完成，有效檔案數量: {len(valid_files)}")
            
            # 檢查結果
            assert len(valid_files) == 1
            assert test_file_path in valid_files
            
            # 檢查日誌內容
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            assert "開始檔案驗證流程" in log_content
            assert "檔案驗證通過" in log_content
            assert "檔案驗證失敗" in log_content
            assert "有效檔案數量: 1" in log_content


class TestCompleteWorkflowIntegration:
    """完整工作流程整合測試"""
    
    def setup_method(self):
        """每個測試方法前的設定"""
        # 清理日誌管理器
        get_logger_manager().cleanup()
        # 重置全域格式
        manager = get_logger_manager()
        manager._global_format = None
        manager._global_level = None
    
    def test_complete_data_processing_workflow(self):
        """測試完整的資料處理工作流程"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "complete_workflow.log")
            logger = setup_logger("complete_workflow", log_file=log_file)
            
            # 模擬完整的資料處理流程
            logger.info("=== 開始完整資料處理工作流程 ===")
            
            # 步驟 1: 檔案驗證
            logger.info("步驟 1: 檔案驗證")
            test_file = os.path.join(temp_dir, "input.xml")
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write("<testcases><case>test</case></testcases>")
            
            if validate_file_path(test_file, allowed_extensions=['.xml'], max_size_mb=10):
                logger.info("檔案驗證通過")
            else:
                logger.error("檔案驗證失敗")
                return
            
            # 步驟 2: 資料驗證
            logger.info("步驟 2: 資料驗證")
            test_cases = [
                {
                    "test_case_number": "TCG-001.002.003",
                    "title": "登入功能測試",
                    "priority": "High",
                    "precondition": "用戶已註冊",
                    "steps": "1. 打開登入頁面\\n2. 輸入憑證",
                    "expected_result": "成功登入"
                },
                {
                    "test_case_number": "TCG-001.002.004",
                    "title": "登出功能測試",
                    "priority": "Medium",
                    "precondition": "用戶已登入",
                    "steps": "點擊登出按鈕",
                    "expected_result": "成功登出"
                }
            ]
            
            validator = FieldValidator()
            validation_rules = {
                "test_case_number": ["required", "string"],
                "title": ["required", "string", "min_length:1"],
                "priority": ["required", "string"],
                "steps": ["required", "string"],
                "expected_result": ["required", "string"]
            }
            
            valid_cases = []
            for i, test_case in enumerate(test_cases):
                logger.info(f"驗證測試案例 {i+1}")
                
                # 驗證編號格式
                if not validate_test_case_number(test_case["test_case_number"]):
                    logger.error(f"測試案例編號格式錯誤: {test_case['test_case_number']}")
                    continue
                
                # 驗證優先級
                if not validate_priority_value(test_case["priority"]):
                    logger.error(f"優先級值無效: {test_case['priority']}")
                    continue
                
                # 批次驗證欄位
                result = validator.validate_batch(test_case, validation_rules)
                if not result.is_valid:
                    logger.error(f"欄位驗證失敗: {result.errors}")
                    continue
                
                logger.info(f"測試案例 {i+1} 驗證通過")
                valid_cases.append(test_case)
            
            # 步驟 3: 處理結果
            logger.info("步驟 3: 處理結果")
            logger.info(f"總共處理 {len(test_cases)} 個測試案例")
            logger.info(f"有效測試案例 {len(valid_cases)} 個")
            logger.info(f"無效測試案例 {len(test_cases) - len(valid_cases)} 個")
            
            if len(valid_cases) > 0:
                logger.info("資料處理成功完成")
            else:
                logger.warning("沒有有效的測試案例")
            
            logger.info("=== 完整資料處理工作流程結束 ===")
            
            # 驗證結果
            assert len(valid_cases) == 2  # 兩個測試案例都應該通過
            
            # 檢查日誌內容
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            assert "開始完整資料處理工作流程" in log_content
            assert "檔案驗證通過" in log_content
            assert "測試案例 1 驗證通過" in log_content
            assert "測試案例 2 驗證通過" in log_content
            assert "有效測試案例 2 個" in log_content
            assert "資料處理成功完成" in log_content
    
    def teardown_method(self):
        """每個測試方法後的清理"""
        # 清理日誌管理器
        get_logger_manager().cleanup()


class TestErrorHandlingIntegration:
    """錯誤處理整合測試"""
    
    def setup_method(self):
        """每個測試方法前的設定"""
        # 清理日誌管理器
        get_logger_manager().cleanup()
        # 重置全域格式
        manager = get_logger_manager()
        manager._global_format = None
        manager._global_level = None
    
    def test_validation_error_with_logging(self):
        """測試驗證錯誤與日誌記錄整合"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "error_handling.log")
            logger = setup_logger("error_handling", log_file=log_file)
            
            # 模擬會產生驗證錯誤的情況
            try:
                logger.info("開始高風險驗證操作")
                
                # 模擬複雜驗證邏輯
                test_data = {
                    "test_case_number": None,  # 會導致錯誤
                    "priority": "Invalid"
                }
                
                if not validate_test_case_number(test_data["test_case_number"]):
                    error_msg = f"測試案例編號無效: {test_data['test_case_number']}"
                    logger.error(error_msg)
                    raise ValidationError(error_msg, field="test_case_number", value=test_data["test_case_number"])
                
            except ValidationError as e:
                logger.critical(f"驗證錯誤: {str(e)}")
                logger.critical(f"錯誤欄位: {e.field}")
                logger.info("錯誤處理完成，繼續執行")
            
            # 檢查日誌內容
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            assert "開始高風險驗證操作" in log_content
            assert "測試案例編號無效" in log_content
            assert "驗證錯誤" in log_content
            assert "錯誤欄位: test_case_number" in log_content
            assert "錯誤處理完成" in log_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])