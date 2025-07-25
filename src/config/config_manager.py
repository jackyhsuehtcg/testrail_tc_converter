"""
設定管理模組

提供統一的設定載入、驗證和管理功能，包括：
- YAML 設定檔解析
- 環境變數整合
- 設定驗證和預設值處理
- 敏感資訊保護
"""

import os
import re
import yaml
import logging
from typing import Dict, Any, Optional
from copy import deepcopy


class ConfigError(Exception):
    """設定相關錯誤"""
    pass


class ConfigManager:
    """設定管理器"""
    
    def __init__(self):
        """初始化設定管理器"""
        self.logger = logging.getLogger(f"{__name__}.ConfigManager")
        self._config: Optional[Dict[str, Any]] = None
        self._config_backup: Optional[Dict[str, Any]] = None
        
        # 預設值
        self._defaults = {
            "lark": {
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
        
        # 必要的設定區段和欄位
        self._required_sections = ["lark", "processing"]
        self._required_fields = {
            "lark": ["app_id", "app_secret"],
            "processing": ["test_case_number_pattern", "required_fields"]
        }
        
        # 環境變數映射模式
        self._env_patterns = [
            (r'^LARK_(.+)', 'lark'),
            (r'^PROCESSING_(.+)', 'processing'),
            (r'^LOGGING_(.+)', 'logging')
        ]
        
        self.logger.debug("ConfigManager 初始化完成")
    
    def load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        載入設定檔案並整合環境變數
        
        Args:
            config_path: 設定檔路徑，預設為 'config/config.yaml'
            
        Returns:
            載入的設定資料
            
        Raises:
            ConfigError: 當設定載入或驗證失敗時
        """
        if config_path is None:
            config_path = "config/config.yaml"
        
        self.logger.info(f"載入設定檔: {config_path}")
        
        try:
            # 載入檔案設定
            file_config = self._load_from_file(config_path)
            
            # 合併預設值
            config = self._merge_configs(self._defaults, file_config)
            
            # 整合環境變數
            config = self._integrate_environment_variables(config)
            
            # 驗證設定
            self.validate_config(config)
            
            # 儲存設定
            self._config = config
            
            self.logger.info("設定載入完成")
            return config
            
        except Exception as e:
            error_msg = f"設定載入失敗: {str(e)}"
            self.logger.error(error_msg)
            raise ConfigError(error_msg)
    
    def _load_from_file(self, config_path: str) -> Dict[str, Any]:
        """從檔案載入設定"""
        if not os.path.exists(config_path):
            raise ConfigError(f"設定檔不存在: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            if not isinstance(config_data, dict):
                raise ConfigError("設定檔格式錯誤：根層級必須是字典")
            
            return config_data
            
        except PermissionError:
            raise ConfigError("設定檔存取權限不足")
        except yaml.YAMLError as e:
            raise ConfigError(f"YAML 格式錯誤: {str(e)}")
        except Exception as e:
            raise ConfigError(f"設定檔讀取失敗: {str(e)}")
    
    def _integrate_environment_variables(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """整合環境變數到設定中"""
        env_config = {}
        
        for env_key, env_value in os.environ.items():
            section_name = self._get_section_from_env_key(env_key)
            if section_name:
                field_path = self._get_field_path_from_env_key(env_key, section_name)
                if field_path:
                    # 類型轉換
                    converted_value = self._convert_env_value(env_value)
                    
                    # 設定巢狀值
                    self._set_nested_value(env_config, [section_name] + field_path, converted_value)
                    self.logger.debug(f"環境變數 {env_key} -> {section_name}.{'.'.join(field_path)} = {converted_value}")
        
        # 合併環境變數設定（環境變數優先）
        return self._merge_configs(config, env_config)
    
    def _get_section_from_env_key(self, env_key: str) -> Optional[str]:
        """從環境變數名稱取得對應的設定區段"""
        for pattern, section in self._env_patterns:
            if re.match(pattern, env_key):
                return section
        return None
    
    def _get_field_path_from_env_key(self, env_key: str, section_name: str) -> Optional[list]:
        """從環境變數名稱取得欄位路徑"""
        for pattern, pattern_section in self._env_patterns:
            if pattern_section == section_name:
                match = re.match(pattern, env_key)
                if match:
                    field_part = match.group(1).lower()
                    
                    # 特殊處理一些常見的巢狀欄位
                    if section_name == "processing" and field_part == "batch_size":
                        return ['batch_processing', 'batch_size']
                    elif section_name == "lark" and field_part.startswith("rate_limit_"):
                        sub_field = field_part.replace("rate_limit_", "")
                        return ['rate_limit', sub_field]
                    elif section_name == "lark" and field_part.startswith("field_mapping_"):
                        sub_field = field_part.replace("field_mapping_", "")
                        return ['field_mapping', sub_field]
                    elif section_name == "processing" and field_part.startswith("batch_processing_"):
                        sub_field = field_part.replace("batch_processing_", "")
                        return ['batch_processing', sub_field]
                    else:
                        # 直接使用完整的欄位名稱
                        # APP_ID -> app_id, APP_SECRET -> app_secret
                        return [field_part]
        return None
    
    def _convert_env_value(self, value: str) -> Any:
        """轉換環境變數值的類型"""
        # 嘗試轉換為數字
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # 嘗試轉換為布林值
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # 預設返回字串
        return value
    
    def _set_nested_value(self, config: Dict[str, Any], path: list, value: Any):
        """設定巢狀字典中的值"""
        current = config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """合併兩個設定字典"""
        result = deepcopy(base)
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        驗證設定的完整性和正確性
        
        Args:
            config: 設定資料
            
        Returns:
            驗證是否通過
            
        Raises:
            ConfigError: 當驗證失敗時
        """
        # 檢查必要區段
        for section in self._required_sections:
            if section not in config:
                raise ConfigError(f"缺少必要的設定區段: {section}")
        
        # 檢查必要欄位
        for section, fields in self._required_fields.items():
            if section in config:
                for field in fields:
                    if field not in config[section]:
                        raise ConfigError(f"缺少必要的設定欄位: {section}.{field}")
        
        # 驗證 Lark 設定
        self._validate_lark_config(config.get("lark", {}))
        
        # 驗證處理設定
        self._validate_processing_config(config.get("processing", {}))
        
        return True
    
    def _validate_lark_config(self, lark_config: Dict[str, Any]):
        """驗證 Lark 設定"""
        # 驗證 app_id 格式
        app_id = lark_config.get("app_id", "")
        if not app_id or not isinstance(app_id, str):
            raise ConfigError("Lark app_id 必須是非空字串")
        
        # 驗證 app_secret 格式
        app_secret = lark_config.get("app_secret", "")
        if not app_secret or not isinstance(app_secret, str):
            raise ConfigError("Lark app_secret 必須是非空字串")
        
        # 驗證 rate_limit 設定
        rate_limit = lark_config.get("rate_limit", {})
        if "max_requests" in rate_limit:
            if not isinstance(rate_limit["max_requests"], int) or rate_limit["max_requests"] <= 0:
                raise ConfigError("rate_limit.max_requests 必須是正整數")
    
    def _validate_processing_config(self, processing_config: Dict[str, Any]):
        """驗證處理設定"""
        # 驗證測試案例編號模式
        pattern = processing_config.get("test_case_number_pattern", "")
        if pattern:
            try:
                re.compile(pattern)
            except re.error:
                raise ConfigError("test_case_number_pattern 不是有效的正則表達式")
        
        # 驗證必要欄位列表
        required_fields = processing_config.get("required_fields", [])
        if not isinstance(required_fields, list) or len(required_fields) == 0:
            raise ConfigError("required_fields 必須是非空列表")
    
    def get_lark_config(self) -> Dict[str, Any]:
        """
        取得 Lark API 相關設定
        
        Returns:
            Lark 設定資料
            
        Raises:
            ConfigError: 當設定未載入時
        """
        if self._config is None:
            raise ConfigError("設定尚未載入，請先呼叫 load_config()")
        
        return self._config.get("lark", {})
    
    def get_processing_config(self) -> Dict[str, Any]:
        """
        取得資料處理相關設定
        
        Returns:
            處理設定資料
            
        Raises:
            ConfigError: 當設定未載入時
        """
        if self._config is None:
            raise ConfigError("設定尚未載入，請先呼叫 load_config()")
        
        return self._config.get("processing", {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        取得日誌相關設定
        
        Returns:
            日誌設定資料
            
        Raises:
            ConfigError: 當設定未載入時
        """
        if self._config is None:
            raise ConfigError("設定尚未載入，請先呼叫 load_config()")
        
        return self._config.get("logging", {})
    
    def backup_config(self) -> Dict[str, Any]:
        """
        備份當前設定
        
        Returns:
            設定備份
        """
        if self._config is None:
            raise ConfigError("設定尚未載入，無法備份")
        
        self._config_backup = deepcopy(self._config)
        return self._config_backup
    
    def restore_config(self, backup: Dict[str, Any]):
        """
        從備份還原設定
        
        Args:
            backup: 設定備份
        """
        self._config = deepcopy(backup)
        self.logger.info("設定已從備份還原")
    
    def __str__(self) -> str:
        """字串表示，隱藏敏感資訊"""
        if self._config is None:
            return "ConfigManager(未載入設定)"
        
        # 深度複製設定以避免修改原始資料
        safe_config = deepcopy(self._config)
        
        # 遮罩敏感資訊
        self._mask_sensitive_data(safe_config)
        
        return f"ConfigManager({safe_config})"
    
    def _mask_sensitive_data(self, config: Dict[str, Any]):
        """遮罩設定中的敏感資料"""
        sensitive_keys = ["app_secret", "secret", "password", "token", "key"]
        
        def mask_recursive(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                        if isinstance(value, str) and len(value) > 0:
                            obj[key] = "***"
                    else:
                        mask_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    mask_recursive(item)
        
        mask_recursive(config)