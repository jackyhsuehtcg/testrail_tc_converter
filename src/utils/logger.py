"""
日誌管理模組

提供統一的日誌設定和管理功能，包括：
- 日誌初始化和設定
- 多種輸出模式（控制台、檔案）
- 不同級別的日誌輸出
- 格式化設定
- 與配置管理整合
- Logger 實例管理
"""

import os
import logging
import logging.handlers
from typing import Optional, Dict, Any
from pathlib import Path


class LoggerManager:
    """日誌管理器，統一管理所有 Logger 實例"""
    
    def __init__(self):
        """初始化日誌管理器"""
        self._loggers: Dict[str, logging.Logger] = {}
        self._global_level: Optional[int] = None
        self._global_format: Optional[str] = None
    
    def get_logger(self, name: str, log_file: Optional[str] = None, 
                   level: int = logging.INFO, 
                   format_string: Optional[str] = None) -> logging.Logger:
        """
        取得或創建 Logger 實例
        
        Args:
            name: Logger 名稱
            log_file: 日誌檔案路徑（可選）
            level: 日誌級別
            format_string: 格式字串（可選）
            
        Returns:
            Logger 實例
        """
        if name in self._loggers:
            return self._loggers[name]
        
        logger = logging.getLogger(name)
        
        # 設定級別（優先使用全域級別）
        if self._global_level is not None:
            logger.setLevel(self._global_level)
        else:
            logger.setLevel(level)
        
        # 清除現有 handlers（避免重複）
        logger.handlers.clear()
        
        # 設定格式
        if self._global_format:
            format_string = self._global_format
        elif not format_string:
            format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        formatter = logging.Formatter(format_string)
        
        # 添加控制台處理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 添加檔案處理器（如果指定）
        if log_file:
            try:
                # 確保目錄存在
                log_path = Path(log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except (OSError, PermissionError) as e:
                # 檔案處理器創建失敗時，記錄到控制台
                logger.warning(f"無法創建檔案處理器 {log_file}: {e}")
        
        # 防止日誌向上傳播
        logger.propagate = False
        
        # 快取 Logger
        self._loggers[name] = logger
        
        return logger
    
    def set_global_level(self, level: int):
        """
        設定所有 Logger 的全域級別
        
        Args:
            level: 日誌級別
        """
        self._global_level = level
        
        # 更新所有現有 Logger 的級別
        for logger in self._loggers.values():
            logger.setLevel(level)
    
    def set_global_format(self, format_string: str):
        """
        設定所有 Logger 的全域格式
        
        Args:
            format_string: 格式字串
        """
        self._global_format = format_string
        formatter = logging.Formatter(format_string)
        
        # 更新所有現有 Logger 的格式
        for logger in self._loggers.values():
            for handler in logger.handlers:
                handler.setFormatter(formatter)
    
    def cleanup(self):
        """清理所有 Logger 的處理器"""
        for logger in self._loggers.values():
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
        
        self._loggers.clear()


# 全域 Logger 管理器實例
_logger_manager = LoggerManager()


def setup_logger(name: str, 
                 log_file: Optional[str] = None,
                 level: int = logging.INFO,
                 format_string: Optional[str] = None,
                 config_path: Optional[str] = None) -> logging.Logger:
    """
    設定並取得 Logger 實例
    
    Args:
        name: Logger 名稱
        log_file: 日誌檔案路徑（可選）
        level: 日誌級別，預設為 INFO
        format_string: 格式字串（可選）
        config_path: 配置檔案路徑（可選）
        
    Returns:
        Logger 實例
        
    Examples:
        >>> logger = setup_logger("my_module")
        >>> logger.info("這是一條資訊日誌")
        
        >>> logger = setup_logger("file_logger", log_file="logs/app.log")
        >>> logger.warning("這會寫入檔案")
        
        >>> logger = setup_logger("debug_logger", level=logging.DEBUG)
        >>> logger.debug("除錯資訊")
    """
    # 如果提供配置檔案路徑，嘗試從配置中載入設定
    if config_path:
        try:
            from config.config_manager import ConfigManager
            
            config_manager = ConfigManager()
            config_manager.load_config(config_path)
            logging_config = config_manager.get_logging_config()
            
            # 從配置中提取設定
            if 'level' in logging_config:
                level_str = logging_config['level'].upper()
                if hasattr(logging, level_str):
                    level = getattr(logging, level_str)
                else:
                    # 無效級別時使用預設值
                    level = logging.INFO
            
            if 'format' in logging_config and not format_string:
                format_string = logging_config['format']
            
            if 'file' in logging_config and not log_file:
                log_file = logging_config['file']
                
        except Exception as e:
            # 配置載入失敗時，使用預設設定並記錄警告
            temp_logger = logging.getLogger(f"{name}_temp")
            temp_logger.warning(f"配置載入失敗，使用預設設定: {e}")
    
    # 處理無效的日誌級別
    if isinstance(level, str):
        level_str = level.upper()
        if hasattr(logging, level_str):
            level = getattr(logging, level_str)
        else:
            level = logging.INFO
    
    return _logger_manager.get_logger(name, log_file, level, format_string)


def get_logger_manager() -> LoggerManager:
    """
    取得全域 Logger 管理器實例
    
    Returns:
        LoggerManager 實例
    """
    return _logger_manager


def set_global_log_level(level: int):
    """
    設定所有 Logger 的全域級別
    
    Args:
        level: 日誌級別
    """
    _logger_manager.set_global_level(level)


def set_global_log_format(format_string: str):
    """
    設定所有 Logger 的全域格式
    
    Args:
        format_string: 格式字串
    """
    _logger_manager.set_global_format(format_string)


def cleanup_loggers():
    """清理所有 Logger 的處理器"""
    _logger_manager.cleanup()


class RotatingLogger:
    """帶日誌輪轉功能的 Logger 包裝器"""
    
    def __init__(self, name: str, log_file: str, 
                 max_bytes: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5,
                 level: int = logging.INFO):
        """
        初始化輪轉 Logger
        
        Args:
            name: Logger 名稱
            log_file: 日誌檔案路徑
            max_bytes: 單個檔案最大大小（位元組）
            backup_count: 備份檔案數量
            level: 日誌級別
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # 清除現有 handlers
        self.logger.handlers.clear()
        
        # 創建目錄
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 設定輪轉檔案處理器
        handler = logging.handlers.RotatingFileHandler(
            log_file, 
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        
        # 設定格式
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        self.logger.propagate = False
    
    def __getattr__(self, name):
        """代理所有方法到內部 logger"""
        return getattr(self.logger, name)


class TimedRotatingLogger:
    """帶時間輪轉功能的 Logger 包裝器"""
    
    def __init__(self, name: str, log_file: str,
                 when: str = 'midnight',
                 interval: int = 1,
                 backup_count: int = 30,
                 level: int = logging.INFO):
        """
        初始化時間輪轉 Logger
        
        Args:
            name: Logger 名稱
            log_file: 日誌檔案路徑
            when: 輪轉時間單位 ('S', 'M', 'H', 'D', 'midnight')
            interval: 輪轉間隔
            backup_count: 備份檔案數量
            level: 日誌級別
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # 清除現有 handlers
        self.logger.handlers.clear()
        
        # 創建目錄
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 設定時間輪轉檔案處理器
        handler = logging.handlers.TimedRotatingFileHandler(
            log_file,
            when=when,
            interval=interval,
            backupCount=backup_count,
            encoding='utf-8'
        )
        
        # 設定格式
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        self.logger.propagate = False
    
    def __getattr__(self, name):
        """代理所有方法到內部 logger"""
        return getattr(self.logger, name)