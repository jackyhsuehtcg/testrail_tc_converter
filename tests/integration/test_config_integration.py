"""
配置管理整合測試

測試配置管理模組與其他模組的整合，包括：
- 配置文件和環境變數的完整整合
- 真實場景下的配置載入和使用
- 與其他模組的相容性測試
"""

import pytest
import sys
import os
import tempfile
import yaml
from unittest.mock import patch, mock_open
from pathlib import Path

# 加入 src 目錄到 Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from config.config_manager import ConfigManager, ConfigError


class TestConfigIntegration:
    """配置管理整合測試類別"""
    
    def setup_method(self):
        """每個測試方法前的設定"""
        # 清理環境變數
        env_keys_to_clean = [k for k in os.environ.keys() if k.startswith(('LARK_', 'PROCESSING_', 'LOGGING_'))]
        for key in env_keys_to_clean:
            if key in os.environ:
                del os.environ[key]
        
        self.config_manager = ConfigManager()
        
        # 完整的測試配置檔案
        self.complete_config = {
            "lark": {
                "app_id": "cli_integration_test_12345",
                "app_secret": "integration_secret_67890",
                "rate_limit": {
                    "max_requests": 150,
                    "window_seconds": 90
                },
                "field_mapping": {
                    "test_case_number": "測試案例編號",
                    "title": "標題",
                    "priority": "優先級",
                    "precondition": "前置條件",
                    "steps": "測試步驟",
                    "expected_result": "預期結果"
                }
            },
            "processing": {
                "test_case_number_pattern": "TCG-\\d+\\.\\d+\\.\\d+",
                "required_fields": [
                    "test_case_number", "title", "priority",
                    "precondition", "steps", "expected_result"
                ],
                "batch_processing": {
                    "batch_size": 300,
                    "max_retries": 5,
                    "retry_delay": 2.0
                }
            },
            "logging": {
                "level": "DEBUG",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "logs/integration_test.log"
            }
        }
    
    def test_complete_config_file_integration(self):
        """測試完整配置文件整合"""
        # 創建臨時配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(self.complete_config, f)
            temp_config_path = f.name
        
        try:
            # 載入配置
            config = self.config_manager.load_config(temp_config_path)
            
            # 驗證所有配置區段
            assert "lark" in config
            assert "processing" in config
            assert "logging" in config
            
            # 驗證 Lark 配置
            lark_config = self.config_manager.get_lark_config()
            assert lark_config["app_id"] == "cli_integration_test_12345"
            assert lark_config["app_secret"] == "integration_secret_67890"
            assert lark_config["rate_limit"]["max_requests"] == 150
            assert lark_config["rate_limit"]["window_seconds"] == 90
            
            # 驗證處理配置
            processing_config = self.config_manager.get_processing_config()
            assert processing_config["batch_processing"]["batch_size"] == 300
            assert processing_config["batch_processing"]["max_retries"] == 5
            assert processing_config["batch_processing"]["retry_delay"] == 2.0
            assert len(processing_config["required_fields"]) == 6
            
            # 驗證日誌配置
            logging_config = self.config_manager.get_logging_config()
            assert logging_config["level"] == "DEBUG"
            assert logging_config["file"] == "logs/integration_test.log"
            
        finally:
            # 清理臨時文件
            os.unlink(temp_config_path)
    
    def test_environment_variables_override_integration(self):
        """測試環境變數覆蓋整合"""
        # 環境變數設定
        env_vars = {
            "LARK_APP_ID": "env_override_app_id",
            "LARK_APP_SECRET": "env_override_secret",
            "LARK_RATE_LIMIT_MAX_REQUESTS": "200",
            "PROCESSING_BATCH_PROCESSING_BATCH_SIZE": "1000",
            "PROCESSING_BATCH_PROCESSING_MAX_RETRIES": "10",
            "LOGGING_LEVEL": "ERROR"
        }
        
        # 最小配置文件（只包含必要欄位）
        minimal_config = {
            "lark": {
                "app_id": "file_app_id",
                "app_secret": "file_secret"
            },
            "processing": {
                "test_case_number_pattern": "TCG-\\d+\\.\\d+\\.\\d+",
                "required_fields": ["test_case_number", "title"]
            }
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('builtins.open', mock_open(read_data=yaml.safe_dump(minimal_config))):
                with patch('os.path.exists', return_value=True):
                    config = self.config_manager.load_config()
                    
                    # 驗證環境變數覆蓋生效
                    assert config["lark"]["app_id"] == "env_override_app_id"
                    assert config["lark"]["app_secret"] == "env_override_secret"
                    assert config["lark"]["rate_limit"]["max_requests"] == 200
                    assert config["processing"]["batch_processing"]["batch_size"] == 1000
                    assert config["processing"]["batch_processing"]["max_retries"] == 10
                    assert config["logging"]["level"] == "ERROR"
    
    def test_mixed_config_sources_integration(self):
        """測試混合配置源整合（配置文件 + 預設值 + 環境變數）"""
        # 部分配置文件
        partial_config = {
            "lark": {
                "app_id": "partial_app_id",
                "app_secret": "partial_secret",
                "rate_limit": {
                    "max_requests": 75
                }
            },
            "processing": {
                "test_case_number_pattern": "CUSTOM-\\d+",
                "required_fields": ["title", "steps"]
            }
        }
        
        # 環境變數
        env_vars = {
            "LARK_RATE_LIMIT_WINDOW_SECONDS": "120",
            "PROCESSING_BATCH_PROCESSING_RETRY_DELAY": "3.5",
            "LOGGING_FILE": "logs/mixed_test.log"
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('builtins.open', mock_open(read_data=yaml.safe_dump(partial_config))):
                with patch('os.path.exists', return_value=True):
                    config = self.config_manager.load_config()
                    
                    # 驗證配置文件值
                    assert config["lark"]["app_id"] == "partial_app_id"
                    assert config["lark"]["rate_limit"]["max_requests"] == 75
                    assert config["processing"]["test_case_number_pattern"] == "CUSTOM-\\d+"
                    
                    # 驗證環境變數覆蓋
                    assert config["lark"]["rate_limit"]["window_seconds"] == 120
                    assert config["processing"]["batch_processing"]["retry_delay"] == 3.5
                    assert config["logging"]["file"] == "logs/mixed_test.log"
                    
                    # 驗證預設值
                    assert config["processing"]["batch_processing"]["batch_size"] == 500  # 預設值
                    assert config["logging"]["level"] == "INFO"  # 預設值
    
    def test_config_validation_integration(self):
        """測試配置驗證整合"""
        # 測試有效配置通過驗證
        with patch('builtins.open', mock_open(read_data=yaml.safe_dump(self.complete_config))):
            with patch('os.path.exists', return_value=True):
                config = self.config_manager.load_config()
                # 載入過程包含驗證，如果沒有異常則驗證通過
                assert config is not None
        
        # 測試無效配置被拒絕
        invalid_config = {
            "lark": {
                "app_id": "test_id"
                # 缺少 app_secret
            },
            "processing": {
                "test_case_number_pattern": "TCG-\\d+"
                # 缺少 required_fields
            }
        }
        
        with pytest.raises(ConfigError) as exc_info:
            with patch('builtins.open', mock_open(read_data=yaml.safe_dump(invalid_config))):
                with patch('os.path.exists', return_value=True):
                    self.config_manager.load_config()
        
        assert "設定載入失敗" in str(exc_info.value)
    
    def test_config_backup_restore_integration(self):
        """測試配置備份和恢復整合"""
        # 載入初始配置
        with patch('builtins.open', mock_open(read_data=yaml.safe_dump(self.complete_config))):
            with patch('os.path.exists', return_value=True):
                initial_config = self.config_manager.load_config()
        
        # 備份配置
        backup = self.config_manager.backup_config()
        
        # 修改配置（模擬運行時更改）
        self.config_manager._config["lark"]["app_id"] = "runtime_modified_id"
        self.config_manager._config["processing"]["batch_processing"]["batch_size"] = 999
        
        # 驗證修改生效
        assert self.config_manager.get_lark_config()["app_id"] == "runtime_modified_id"
        assert self.config_manager.get_processing_config()["batch_processing"]["batch_size"] == 999
        
        # 恢復配置
        self.config_manager.restore_config(backup)
        
        # 驗證恢復成功
        assert self.config_manager.get_lark_config()["app_id"] == "cli_integration_test_12345"
        assert self.config_manager.get_processing_config()["batch_processing"]["batch_size"] == 300
    
    def test_sensitive_data_protection_integration(self):
        """測試敏感資料保護整合"""
        # 載入包含敏感資料的配置
        sensitive_config = self.complete_config.copy()
        sensitive_config["lark"]["app_secret"] = "very_secret_key_12345"
        sensitive_config["lark"]["token"] = "secret_token_67890"
        
        with patch('builtins.open', mock_open(read_data=yaml.safe_dump(sensitive_config))):
            with patch('os.path.exists', return_value=True):
                self.config_manager.load_config()
        
        # 測試字串表示中敏感資料被遮罩
        config_str = str(self.config_manager)
        
        # 敏感資料不應出現在字串表示中
        assert "very_secret_key_12345" not in config_str
        assert "secret_token_67890" not in config_str
        
        # 但遮罩標記應該存在
        assert "***" in config_str
    
    def test_type_conversion_integration(self):
        """測試類型轉換整合"""
        # 使用字串形式的數值環境變數
        env_vars = {
            "LARK_RATE_LIMIT_MAX_REQUESTS": "250",      # int
            "PROCESSING_BATCH_PROCESSING_RETRY_DELAY": "1.5",  # float
            "PROCESSING_BATCH_PROCESSING_BATCH_SIZE": "750"    # int
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('builtins.open', mock_open(read_data=yaml.safe_dump(self.complete_config))):
                with patch('os.path.exists', return_value=True):
                    config = self.config_manager.load_config()
                    
                    # 驗證類型轉換正確
                    assert isinstance(config["lark"]["rate_limit"]["max_requests"], int)
                    assert config["lark"]["rate_limit"]["max_requests"] == 250
                    
                    assert isinstance(config["processing"]["batch_processing"]["retry_delay"], float)
                    assert config["processing"]["batch_processing"]["retry_delay"] == 1.5
                    
                    assert isinstance(config["processing"]["batch_processing"]["batch_size"], int)
                    assert config["processing"]["batch_processing"]["batch_size"] == 750
    
    def test_config_reload_integration(self):
        """測試配置重新載入整合"""
        # 第一次載入
        with patch('builtins.open', mock_open(read_data=yaml.safe_dump(self.complete_config))):
            with patch('os.path.exists', return_value=True):
                config1 = self.config_manager.load_config()
                initial_app_id = config1["lark"]["app_id"]
        
        # 修改配置內容
        modified_config = self.complete_config.copy()
        modified_config["lark"]["app_id"] = "reloaded_app_id_999"
        modified_config["processing"]["batch_processing"]["batch_size"] = 888
        
        # 重新載入
        with patch('builtins.open', mock_open(read_data=yaml.safe_dump(modified_config))):
            with patch('os.path.exists', return_value=True):
                config2 = self.config_manager.load_config()
        
        # 驗證配置已更新
        assert config2["lark"]["app_id"] == "reloaded_app_id_999"
        assert config2["processing"]["batch_processing"]["batch_size"] == 888
        assert config2["lark"]["app_id"] != initial_app_id
    
    def test_error_handling_integration(self):
        """測試錯誤處理整合"""
        # 測試文件不存在
        with pytest.raises(ConfigError) as exc_info:
            self.config_manager.load_config("/nonexistent/config.yaml")
        assert "設定檔不存在" in str(exc_info.value)
        
        # 測試無效的 YAML
        invalid_yaml = "invalid: yaml: content: ["
        with pytest.raises(ConfigError) as exc_info:
            with patch('builtins.open', mock_open(read_data=invalid_yaml)):
                with patch('os.path.exists', return_value=True):
                    self.config_manager.load_config()
        assert "YAML 格式錯誤" in str(exc_info.value)
        
        # 測試權限錯誤
        with pytest.raises(ConfigError) as exc_info:
            with patch('builtins.open', side_effect=PermissionError("Access denied")):
                with patch('os.path.exists', return_value=True):
                    self.config_manager.load_config()
        assert "設定檔存取權限不足" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])