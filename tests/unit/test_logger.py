"""
日誌管理模組測試

測試 Logger 工具函數的各項功能，包括：
- 日誌初始化和設定
- 不同級別的日誌輸出
- 日誌檔案寫入功能
- 設定檔整合
- 多個 Logger 實例管理
"""

import pytest
import sys
import os
import tempfile
import logging
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

# 加入 src 目錄到 Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from utils.logger import (
    setup_logger, LoggerManager, get_logger_manager,
    set_global_log_level, set_global_log_format, cleanup_loggers
)


class TestSetupLogger:
    """setup_logger 函數測試"""
    
    def setup_method(self):
        """每個測試方法前的設定"""
        # 清理已存在的 loggers 避免測試間互相影響
        for logger_name in list(logging.Logger.manager.loggerDict.keys()):
            if logger_name.startswith('test_'):
                logging.getLogger(logger_name).handlers.clear()
    
    def test_setup_logger_basic(self):
        """測試基本日誌設定"""
        logger = setup_logger("test_basic")
        
        # 驗證 logger 物件
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_basic"
        assert logger.level == logging.INFO  # 預設級別
        
        # 驗證至少有一個 handler
        assert len(logger.handlers) > 0
    
    def test_setup_logger_with_different_names(self):
        """測試不同名稱的 logger"""
        logger1 = setup_logger("test_module1")
        logger2 = setup_logger("test_module2")
        
        assert logger1.name == "test_module1"
        assert logger2.name == "test_module2"
        assert logger1 is not logger2
    
    def test_setup_logger_same_name_returns_same_instance(self):
        """測試相同名稱返回相同實例"""
        logger1 = setup_logger("test_same")
        logger2 = setup_logger("test_same")
        
        assert logger1 is logger2
    
    def test_setup_logger_with_custom_level(self):
        """測試自訂日誌級別"""
        logger = setup_logger("test_custom_level", level=logging.DEBUG)
        
        assert logger.level == logging.DEBUG
    
    def test_setup_logger_with_file_handler(self):
        """測試檔案處理器設定"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.log")
            logger = setup_logger("test_file", log_file=log_file)
            
            # 檢查是否有檔案處理器
            file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) > 0
            
            # 測試寫入日誌
            logger.info("測試訊息")
            
            # 確保檔案被創建且有內容
            assert os.path.exists(log_file)
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "測試訊息" in content
    
    def test_setup_logger_with_config_file(self):
        """測試使用設定檔"""
        config_data = {
            "logging": {
                "level": "DEBUG",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "logs/test_config.log"
            }
        }
        
        with patch('config.config_manager.ConfigManager') as mock_config_manager:
            mock_config = Mock()
            mock_config.get_logging_config.return_value = config_data["logging"]
            mock_config_manager.return_value = mock_config
            
            logger = setup_logger("test_config", config_path="test_config.yaml")
            
            # 驗證設定被正確載入
            assert logger.level == logging.DEBUG
            mock_config_manager.assert_called_once()
            mock_config.load_config.assert_called_once_with("test_config.yaml")
    
    def test_setup_logger_error_handling(self):
        """測試錯誤處理"""
        # 測試無效的日誌級別
        logger = setup_logger("test_invalid_level", level="INVALID")
        # 應該回退到預設級別
        assert logger.level == logging.INFO
        
        # 測試無效的檔案路徑
        invalid_path = "/invalid/path/that/does/not/exist/test.log"
        logger = setup_logger("test_invalid_path", log_file=invalid_path)
        # 應該仍然創建 logger，但只有 console handler
        console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(console_handlers) > 0
    
    def test_logger_output_levels(self):
        """測試不同級別的日誌輸出"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "levels_test.log")
            logger = setup_logger("test_levels", log_file=log_file, level=logging.DEBUG)
            
            # 測試各種級別的日誌
            logger.debug("Debug 訊息")
            logger.info("Info 訊息")
            logger.warning("Warning 訊息")
            logger.error("Error 訊息")
            logger.critical("Critical 訊息")
            
            # 讀取檔案內容
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 驗證所有級別的訊息都被記錄
            assert "Debug 訊息" in content
            assert "Info 訊息" in content
            assert "Warning 訊息" in content
            assert "Error 訊息" in content
            assert "Critical 訊息" in content
    
    def test_logger_format(self):
        """測試日誌格式"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "format_test.log")
            custom_format = "%(levelname)s - %(name)s - %(message)s"
            logger = setup_logger("test_format", log_file=log_file, 
                                format_string=custom_format)
            
            logger.info("格式測試訊息")
            
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 驗證格式正確
            assert "INFO - test_format - 格式測試訊息" in content
    
    def test_logger_unicode_support(self):
        """測試 Unicode 字符支援"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "unicode_test.log")
            logger = setup_logger("test_unicode", log_file=log_file)
            
            # 測試各種 Unicode 字符
            test_messages = [
                "中文測試訊息",
                "English test message",
                "日本語テストメッセージ",
                "한글 테스트 메시지",
                "Ελληνικά τεστ μήνυμα",
                "🚀 Emoji test 📝"
            ]
            
            for msg in test_messages:
                logger.info(msg)
            
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 驗證所有訊息都正確記錄
            for msg in test_messages:
                assert msg in content


class TestLoggerManager:
    """LoggerManager 類別測試"""
    
    def setup_method(self):
        """每個測試方法前的設定"""
        # 清理已存在的 loggers
        for logger_name in list(logging.Logger.manager.loggerDict.keys()):
            if logger_name.startswith('test_manager_'):
                logging.getLogger(logger_name).handlers.clear()
    
    def test_logger_manager_initialization(self):
        """測試 LoggerManager 初始化"""
        manager = LoggerManager()
        
        assert hasattr(manager, 'get_logger')
        assert hasattr(manager, 'set_global_level')
        assert hasattr(manager, 'set_global_format')
    
    def test_get_logger_basic(self):
        """測試基本 logger 獲取"""
        manager = LoggerManager()
        logger = manager.get_logger("test_manager_basic")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_manager_basic"
    
    def test_get_logger_with_module_path(self):
        """測試使用模組路徑獲取 logger"""
        manager = LoggerManager()
        logger = manager.get_logger("test_manager.module.submodule")
        
        assert logger.name == "test_manager.module.submodule"
    
    def test_set_global_level(self):
        """測試設定全域日誌級別"""
        manager = LoggerManager()
        
        # 創建幾個 logger
        logger1 = manager.get_logger("test_manager_level1")
        logger2 = manager.get_logger("test_manager_level2")
        
        # 設定全域級別
        manager.set_global_level(logging.WARNING)
        
        # 驗證所有 logger 的級別都被更新
        assert logger1.level == logging.WARNING
        assert logger2.level == logging.WARNING
    
    def test_set_global_format(self):
        """測試設定全域日誌格式"""
        manager = LoggerManager()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "global_format_test.log")
            logger = manager.get_logger("test_manager_format", log_file=log_file)
            
            # 設定全域格式
            new_format = "GLOBAL: %(levelname)s - %(message)s"
            manager.set_global_format(new_format)
            
            logger.info("全域格式測試")
            
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            assert "GLOBAL: INFO - 全域格式測試" in content
    
    def test_logger_manager_caching(self):
        """測試 LoggerManager 快取機制"""
        manager = LoggerManager()
        
        # 多次獲取相同名稱的 logger
        logger1 = manager.get_logger("test_manager_cache")
        logger2 = manager.get_logger("test_manager_cache")
        
        # 應該返回相同的實例
        assert logger1 is logger2
    
    def test_logger_manager_cleanup(self):
        """測試 LoggerManager 清理功能"""
        manager = LoggerManager()
        
        # 創建一些 logger
        logger1 = manager.get_logger("test_manager_cleanup1")
        logger2 = manager.get_logger("test_manager_cleanup2")
        
        # 清理
        manager.cleanup()
        
        # 驗證 handlers 被清理
        assert len(logger1.handlers) == 0
        assert len(logger2.handlers) == 0


class TestLoggerIntegration:
    """日誌模組整合測試"""
    
    def test_multiple_loggers_different_files(self):
        """測試多個 logger 寫入不同檔案"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = os.path.join(temp_dir, "module1.log")
            file2 = os.path.join(temp_dir, "module2.log")
            
            logger1 = setup_logger("module1", log_file=file1)
            logger2 = setup_logger("module2", log_file=file2)
            
            logger1.info("Module1 訊息")
            logger2.info("Module2 訊息")
            
            # 驗證檔案內容
            with open(file1, 'r', encoding='utf-8') as f:
                content1 = f.read()
            with open(file2, 'r', encoding='utf-8') as f:
                content2 = f.read()
            
            assert "Module1 訊息" in content1
            assert "Module1 訊息" not in content2
            assert "Module2 訊息" in content2
            assert "Module2 訊息" not in content1
    
    def test_logger_with_config_integration(self):
        """測試 logger 與配置管理整合"""
        # 模擬配置管理器
        mock_config_data = {
            "level": "DEBUG",
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "file": "logs/integration_test.log"
        }
        
        with patch('config.config_manager.ConfigManager') as mock_config_manager_class:
            mock_config_manager = Mock()
            mock_config_manager.load_config.return_value = None
            mock_config_manager.get_logging_config.return_value = mock_config_data
            mock_config_manager_class.return_value = mock_config_manager
            
            logger = setup_logger("integration_test", config_path="test.yaml")
            
            # 驗證配置被正確使用
            assert logger.level == logging.DEBUG
            mock_config_manager.load_config.assert_called_once_with("test.yaml")
            mock_config_manager.get_logging_config.assert_called_once()
    
    def test_logger_error_recovery(self):
        """測試日誌模組錯誤恢復"""
        # 測試配置載入失敗的情況
        with patch('config.config_manager.ConfigManager') as mock_config_manager_class:
            mock_config_manager = Mock()
            mock_config_manager.load_config.side_effect = Exception("配置載入失敗")
            mock_config_manager_class.return_value = mock_config_manager
            
            # 應該能夠正常創建 logger，使用預設配置
            logger = setup_logger("error_recovery_test", config_path="invalid.yaml")
            
            assert isinstance(logger, logging.Logger)
            assert logger.level == logging.INFO  # 回退到預設級別
    
    def teardown_method(self):
        """每個測試方法後的清理"""
        # 清理測試產生的 loggers
        for logger_name in list(logging.Logger.manager.loggerDict.keys()):
            if logger_name.startswith(('test_', 'module', 'integration_', 'error_recovery_')):
                logger = logging.getLogger(logger_name)
                for handler in logger.handlers[:]:
                    handler.close()
                    logger.removeHandler(handler)


class TestRotatingLogger:
    """RotatingLogger 測試"""
    
    def test_rotating_logger_initialization(self):
        """測試 RotatingLogger 初始化"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "rotating.log")
            
            from utils.logger import RotatingLogger
            rotating_logger = RotatingLogger("test_rotating", log_file)
            
            assert rotating_logger.name == "test_rotating"
            assert len(rotating_logger.handlers) > 0
    
    def test_rotating_logger_logging(self):
        """測試 RotatingLogger 日誌記錄"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "rotating.log")
            
            from utils.logger import RotatingLogger
            rotating_logger = RotatingLogger("test_rotating", log_file, max_bytes=1024)
            
            rotating_logger.info("測試訊息")
            
            assert os.path.exists(log_file)
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "測試訊息" in content


class TestTimedRotatingLogger:
    """TimedRotatingLogger 測試"""
    
    def test_timed_rotating_logger_initialization(self):
        """測試 TimedRotatingLogger 初始化"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "timed_rotating.log")
            
            from utils.logger import TimedRotatingLogger
            timed_logger = TimedRotatingLogger("test_timed", log_file)
            
            assert timed_logger.name == "test_timed"
            assert len(timed_logger.handlers) > 0
    
    def test_timed_rotating_logger_logging(self):
        """測試 TimedRotatingLogger 日誌記錄"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "timed_rotating.log")
            
            from utils.logger import TimedRotatingLogger
            timed_logger = TimedRotatingLogger("test_timed", log_file, backup_count=3)
            
            timed_logger.warning("測試警告訊息")
            
            assert os.path.exists(log_file)
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "測試警告訊息" in content


class TestGlobalLoggerFunctions:
    """全域日誌管理函數測試"""
    
    def test_get_logger_manager(self):
        """測試取得全域日誌管理器"""
        manager = get_logger_manager()
        assert isinstance(manager, LoggerManager)
    
    def test_set_global_log_level(self):
        """測試設定全域日誌級別"""
        # 清理環境
        cleanup_loggers()
        
        # 創建測試 logger
        logger1 = setup_logger("test_global_level1")
        logger2 = setup_logger("test_global_level2")
        
        # 設定全域級別
        set_global_log_level(logging.WARNING)
        
        # 驗證級別被更新
        assert logger1.level == logging.WARNING
        assert logger2.level == logging.WARNING
    
    def test_set_global_log_format(self):
        """測試設定全域日誌格式"""
        # 清理環境
        cleanup_loggers()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "global_format.log")
            
            # 先設定全域格式，再創建 logger
            custom_format = "GLOBAL: %(levelname)s - %(message)s"
            set_global_log_format(custom_format)
            
            logger = setup_logger("test_global_format", log_file=log_file)
            logger.info("全域格式測試")
            
            # 確保所有 handlers 都被刷新
            for handler in logger.handlers:
                handler.flush()
            
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "GLOBAL: INFO - 全域格式測試" in content
        
        # 測試後清理全域格式設定
        cleanup_loggers()
        # 重置全域格式
        manager = get_logger_manager()
        manager._global_format = None
    
    def test_cleanup_loggers(self):
        """測試清理所有 logger"""
        # 先清理環境
        cleanup_loggers()
        
        # 創建一些 logger
        logger1 = setup_logger("test_cleanup1")
        logger2 = setup_logger("test_cleanup2")
        
        # 確認 handlers 存在
        assert len(logger1.handlers) > 0
        assert len(logger2.handlers) > 0
        
        # 清理
        cleanup_loggers()
        
        # 驗證 handlers 被清理
        # 注意：清理後的 logger 可能需要重新獲取
        manager = get_logger_manager()
        assert len(manager._loggers) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])