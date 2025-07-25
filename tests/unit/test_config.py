"""
設定管理模組測試

測試 ConfigManager 類別的各項功能，包括：
- 設定檔載入功能
- 環境變數讀取
- 設定驗證功能
- 預設值處理
- YAML 格式解析
- 敏感資訊保護
"""

import pytest
import sys
import os
import tempfile
import yaml
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

# 加入 src 目錄到 Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from config.config_manager import ConfigManager, ConfigError


class TestConfigManager:
    """ConfigManager 類別測試"""
    
    def setup_method(self):
        """每個測試方法前的設定"""
        # 清理所有可能的環境變數污染
        env_keys_to_clean = [k for k in os.environ.keys() if k.startswith(('LARK_', 'PROCESSING_', 'LOGGING_'))]
        for key in env_keys_to_clean:
            if key in os.environ:
                del os.environ[key]
        
        self.config_manager = ConfigManager()
        
        # 標準設定檔內容
        self.valid_config_data = {
            "lark": {
                "app_id": "cli_test123456789",
                "app_secret": "test_secret_key_12345",
                "rate_limit": {
                    "max_requests": 100,
                    "window_seconds": 60
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
                    "batch_size": 500,
                    "max_retries": 3,
                    "retry_delay": 1.0
                }
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "logs/converter.log"
            }
        }
    
    def test_init(self):
        """測試初始化"""
        config_manager = ConfigManager()
        assert config_manager is not None
        assert hasattr(config_manager, 'load_config')
        assert hasattr(config_manager, 'get_lark_config')
        assert hasattr(config_manager, 'get_processing_config')
        assert hasattr(config_manager, 'get_logging_config')
    
    def test_load_config_from_file(self):
        """測試從檔案載入設定"""
        # 創建臨時設定檔
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(self.valid_config_data, f)
            temp_config_path = f.name
        
        try:
            # 載入設定
            config = self.config_manager.load_config(temp_config_path)
            
            # 驗證設定內容
            assert config is not None
            assert "lark" in config
            assert "processing" in config
            assert config["lark"]["app_id"] == "cli_test123456789"
            assert config["processing"]["batch_processing"]["batch_size"] == 500
            
        finally:
            # 清理臨時檔案
            os.unlink(temp_config_path)
    
    def test_load_config_default_path(self):
        """測試使用預設路徑載入設定"""
        with patch('builtins.open', mock_open(read_data=yaml.safe_dump(self.valid_config_data))):
            with patch('os.path.exists', return_value=True):
                config = self.config_manager.load_config()
                
                assert config is not None
                assert "lark" in config
                assert "processing" in config
    
    def test_load_config_file_not_exists(self):
        """測試設定檔不存在的情況"""
        non_existent_path = "/path/to/non_existent_config.yaml"
        
        with pytest.raises(ConfigError) as exc_info:
            self.config_manager.load_config(non_existent_path)
        
        assert "設定檔不存在" in str(exc_info.value)
    
    def test_load_config_invalid_yaml(self):
        """測試無效的 YAML 格式"""
        invalid_yaml = "invalid: yaml: content: ["
        
        with patch('builtins.open', mock_open(read_data=invalid_yaml)):
            with patch('os.path.exists', return_value=True):
                with pytest.raises(ConfigError) as exc_info:
                    self.config_manager.load_config("test.yaml")
                
                assert "YAML 格式錯誤" in str(exc_info.value)
    
    def test_load_config_with_environment_variables(self):
        """測試環境變數整合"""
        # 設定環境變數
        test_env_vars = {
            "LARK_APP_ID": "env_app_id_123456",
            "LARK_APP_SECRET": "env_secret_key_789",
            "PROCESSING_BATCH_SIZE": "1000"
        }
        
        with patch.dict(os.environ, test_env_vars):
            with patch('builtins.open', mock_open(read_data=yaml.safe_dump(self.valid_config_data))):
                with patch('os.path.exists', return_value=True):
                    config = self.config_manager.load_config()
                    
                    # 環境變數應該覆蓋設定檔的值
                    assert config["lark"]["app_id"] == "env_app_id_123456"
                    assert config["lark"]["app_secret"] == "env_secret_key_789"
                    assert config["processing"]["batch_processing"]["batch_size"] == 1000
    
    def test_get_lark_config(self):
        """測試取得 Lark 設定"""
        # 先載入設定
        with patch('builtins.open', mock_open(read_data=yaml.safe_dump(self.valid_config_data))):
            with patch('os.path.exists', return_value=True):
                self.config_manager.load_config()
        
        lark_config = self.config_manager.get_lark_config()
        
        # 驗證 Lark 設定
        assert "app_id" in lark_config
        assert "app_secret" in lark_config
        assert "rate_limit" in lark_config
        assert "field_mapping" in lark_config
        
        assert lark_config["app_id"] == "cli_test123456789"
        assert lark_config["rate_limit"]["max_requests"] == 100
        assert "測試案例編號" in lark_config["field_mapping"].values()
    
    def test_get_lark_config_with_defaults(self):
        """測試 Lark 設定的預設值處理"""
        minimal_config = {
            "lark": {
                "app_id": "test_app_id",
                "app_secret": "test_secret"
            }
        }
        
        with patch('builtins.open', mock_open(read_data=yaml.safe_dump(minimal_config))):
            with patch('os.path.exists', return_value=True):
                self.config_manager.load_config()
        
        lark_config = self.config_manager.get_lark_config()
        
        # 檢查預設值
        assert lark_config["rate_limit"]["max_requests"] == 100  # 預設值
        assert lark_config["rate_limit"]["window_seconds"] == 60  # 預設值
        assert "test_case_number" in lark_config["field_mapping"]  # 預設欄位映射
    
    def test_get_processing_config(self):
        """測試取得處理設定"""
        with patch('builtins.open', mock_open(read_data=yaml.safe_dump(self.valid_config_data))):
            with patch('os.path.exists', return_value=True):
                self.config_manager.load_config()
        
        processing_config = self.config_manager.get_processing_config()
        
        # 驗證處理設定
        assert "test_case_number_pattern" in processing_config
        assert "required_fields" in processing_config
        assert "batch_processing" in processing_config
        
        assert processing_config["test_case_number_pattern"] == "TCG-\\d+\\.\\d+\\.\\d+"
        assert len(processing_config["required_fields"]) == 6
        assert processing_config["batch_processing"]["batch_size"] == 500
    
    def test_get_logging_config(self):
        """測試取得日誌設定"""
        with patch('builtins.open', mock_open(read_data=yaml.safe_dump(self.valid_config_data))):
            with patch('os.path.exists', return_value=True):
                self.config_manager.load_config()
        
        logging_config = self.config_manager.get_logging_config()
        
        # 驗證日誌設定
        assert "level" in logging_config
        assert "format" in logging_config
        assert "file" in logging_config
        
        assert logging_config["level"] == "INFO"
        assert "%(asctime)s" in logging_config["format"]
        assert logging_config["file"] == "logs/converter.log"
    
    def test_validate_config_valid(self):
        """測試設定驗證 - 有效設定"""
        with patch('builtins.open', mock_open(read_data=yaml.safe_dump(self.valid_config_data))):
            with patch('os.path.exists', return_value=True):
                config = self.config_manager.load_config()
                
                # 驗證應該通過
                is_valid = self.config_manager.validate_config(config)
                assert is_valid is True
    
    def test_validate_config_missing_required_sections(self):
        """測試設定驗證 - 缺少必要區段"""
        # 直接測試驗證方法，不使用預設值合併
        invalid_configs = [
            {},  # 空設定
            {"lark": {}},  # 缺少 processing 區段
            {"processing": {}},  # 缺少 lark 區段
        ]
        
        for invalid_config in invalid_configs:
            with pytest.raises(ConfigError) as exc_info:
                self.config_manager.validate_config(invalid_config)
            
            assert "缺少必要的設定區段" in str(exc_info.value)
    
    def test_validate_config_missing_required_fields(self):
        """測試設定驗證 - 缺少必要欄位"""
        # Lark 區段缺少 app_id
        incomplete_lark_config = {
            "lark": {
                "app_secret": "test_secret"
            },
            "processing": self.valid_config_data["processing"]
        }
        
        with patch('builtins.open', mock_open(read_data=yaml.safe_dump(incomplete_lark_config))):
            with patch('os.path.exists', return_value=True):
                with pytest.raises(ConfigError) as exc_info:
                    self.config_manager.load_config()
                
                assert "缺少必要的設定欄位" in str(exc_info.value)
    
    def test_sensitive_information_protection(self):
        """測試敏感資訊保護"""
        with patch('builtins.open', mock_open(read_data=yaml.safe_dump(self.valid_config_data))):
            with patch('os.path.exists', return_value=True):
                self.config_manager.load_config()
        
        # 取得字串表示
        config_str = str(self.config_manager)
        
        # 敏感資訊應該被遮罩
        assert "test_secret_key_12345" not in config_str
        assert "***" in config_str or "[MASKED]" in config_str
    
    def test_config_not_loaded_error(self):
        """測試設定未載入時的錯誤處理"""
        # 未載入設定就嘗試取得設定
        with pytest.raises(ConfigError) as exc_info:
            self.config_manager.get_lark_config()
        
        assert "設定尚未載入" in str(exc_info.value)
    
    def test_reload_config(self):
        """測試重新載入設定"""
        # 第一次載入
        with patch('builtins.open', mock_open(read_data=yaml.safe_dump(self.valid_config_data))):
            with patch('os.path.exists', return_value=True):
                config1 = self.config_manager.load_config()
        
        # 修改設定
        modified_config = self.valid_config_data.copy()
        modified_config["lark"]["app_id"] = "modified_app_id"
        
        # 重新載入
        with patch('builtins.open', mock_open(read_data=yaml.safe_dump(modified_config))):
            with patch('os.path.exists', return_value=True):
                config2 = self.config_manager.load_config()
        
        # 設定應該被更新
        assert config2["lark"]["app_id"] == "modified_app_id"
    
    def test_environment_variable_types(self):
        """測試環境變數類型轉換"""
        env_vars = {
            "PROCESSING_BATCH_SIZE": "250",  # 字串數字
            "LARK_RATE_LIMIT_MAX_REQUESTS": "50",  # 字串數字
            "PROCESSING_MAX_RETRIES": "5",  # 字串數字
            "PROCESSING_RETRY_DELAY": "2.5"  # 字串浮點數
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('builtins.open', mock_open(read_data=yaml.safe_dump(self.valid_config_data))):
                with patch('os.path.exists', return_value=True):
                    config = self.config_manager.load_config()
                    
                    # 檢查類型轉換
                    assert isinstance(config["processing"]["batch_processing"]["batch_size"], int)
                    assert config["processing"]["batch_processing"]["batch_size"] == 250
                    assert isinstance(config["lark"]["rate_limit"]["max_requests"], int)
                    assert config["lark"]["rate_limit"]["max_requests"] == 50
    
    def test_config_file_permissions(self):
        """測試設定檔權限處理"""
        # 模擬權限錯誤
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with patch('os.path.exists', return_value=True):
                with pytest.raises(ConfigError) as exc_info:
                    self.config_manager.load_config("test.yaml")
                
                assert "設定檔存取權限不足" in str(exc_info.value)
    
    def test_nested_environment_variable_override(self):
        """測試巢狀設定的環境變數覆蓋"""
        nested_env_vars = {
            "LARK_FIELD_MAPPING_TITLE": "自訂標題欄位",
            "PROCESSING_BATCH_PROCESSING_BATCH_SIZE": "750"
        }
        
        with patch.dict(os.environ, nested_env_vars):
            with patch('builtins.open', mock_open(read_data=yaml.safe_dump(self.valid_config_data))):
                with patch('os.path.exists', return_value=True):
                    config = self.config_manager.load_config()
                    
                    # 檢查巢狀覆蓋
                    assert config["lark"]["field_mapping"]["title"] == "自訂標題欄位"
                    assert config["processing"]["batch_processing"]["batch_size"] == 750
    
    def test_config_backup_and_restore(self):
        """測試設定備份和還原"""
        # 載入初始設定
        with patch('builtins.open', mock_open(read_data=yaml.safe_dump(self.valid_config_data))):
            with patch('os.path.exists', return_value=True):
                self.config_manager.load_config()
        
        # 記錄初始app_id值
        initial_app_id = self.config_manager.get_lark_config()["app_id"]
        
        # 備份設定
        backup = self.config_manager.backup_config()
        
        # 直接修改內部配置來模擬配置變更
        self.config_manager._config["lark"]["app_id"] = "modified_app_id"
        
        # 驗證修改生效
        lark_config = self.config_manager.get_lark_config()
        assert lark_config["app_id"] == "modified_app_id"
        
        # 還原設定
        self.config_manager.restore_config(backup)
        
        # 驗證還原
        lark_config = self.config_manager.get_lark_config()
        assert lark_config["app_id"] == initial_app_id
    
    def test_config_merge_strategies(self):
        """測試設定合併策略"""
        base_config = {
            "lark": {
                "app_id": "base_id",
                "rate_limit": {"max_requests": 50}
            }
        }
        
        override_config = {
            "lark": {
                "app_secret": "override_secret",
                "rate_limit": {"window_seconds": 30}
            }
        }
        
        merged = self.config_manager._merge_configs(base_config, override_config)
        
        # 檢查合併結果
        assert merged["lark"]["app_id"] == "base_id"  # 保留原值
        assert merged["lark"]["app_secret"] == "override_secret"  # 新增值
        assert merged["lark"]["rate_limit"]["max_requests"] == 50  # 保留原值
        assert merged["lark"]["rate_limit"]["window_seconds"] == 30  # 新增值


class TestConfigError:
    """ConfigError 異常測試"""
    
    def test_config_error_creation(self):
        """測試 ConfigError 異常創建"""
        error_msg = "測試設定錯誤"
        
        with pytest.raises(ConfigError) as exc_info:
            raise ConfigError(error_msg)
        
        assert str(exc_info.value) == error_msg
    
    def test_config_error_inheritance(self):
        """測試 ConfigError 繼承關係"""
        error = ConfigError("測試錯誤")
        assert isinstance(error, Exception)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])