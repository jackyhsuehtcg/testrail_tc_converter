#!/usr/bin/env python3
"""
TestRail 轉換器主程式

整合所有模組，提供完整的 TestRail XML 到 Lark 表格轉換功能。
支援互動模式和命令列模式兩種使用方式。

使用方式：
1. 互動模式：python main.py
2. 轉換模式：python main.py --xml-file file.xml --wiki-token docXXX --table-id tblXXX
3. 測試模式：python main.py --mode test --wiki-token docXXX --table-id tblXXX

作者：Claude (Anthropic)
版本：1.0.0
"""

import sys
import argparse
import logging
from typing import Optional, Tuple
from pathlib import Path

# 導入所有必要的模組
from parsers.xml_parser import TestRailXMLParser
from parsers.data_cleaner import TestCaseDataCleaner
from parsers.formatter import LarkDataFormatter
from lark.client import SimpleLarkClient
from cli.interface import InteractiveCLI, ValidationError
from config.config_manager import ConfigManager
from utils.logger import setup_logger
from utils.validators import validate_file_path


def main_conversion_flow(xml_file_path: str, 
                        wiki_token: str, 
                        table_id: str,
                        config_path: Optional[str] = None) -> bool:
    """
    執行完整的 TestRail 到 Lark 轉換流程
    
    Args:
        xml_file_path: TestRail XML 檔案路徑
        wiki_token: Lark Wiki Token
        table_id: Lark 表格 ID
        config_path: 配置檔案路徑（可選）
        
    Returns:
        轉換是否成功
    """
    config_file = config_path or "config/config.yaml"
    
    try:
        # 步驟 1: 載入配置並設定 logger
        config_manager = ConfigManager()
        logger = setup_logger("main", level=logging.INFO)
        
        logger.info("=== 開始 TestRail 轉換流程 ===")
        logger.info(f"XML 檔案: {xml_file_path}")
        logger.info(f"Wiki Token: {wiki_token[:10]}...")
        logger.info(f"Table ID: {table_id}")
        logger.info("步驟 1: 載入應用程式配置")
        
        # 載入配置檔案，並捕獲錯誤
        try:
            logger.info(f"載入配置檔案: {config_file}")
            config_manager.load_config(config_file)
            logger.info("配置檔案載入完成")
        except Exception as config_error:
            logger.warning(f"配置檔案載入失敗: {config_error}")
            # 嘗試載入預設配置或使用範例配置
            fallback_config = config_file.replace(".yaml", ".yaml.example")
            try:
                logger.info(f"嘗試載入範例配置檔案: {fallback_config}")
                config_manager.load_config(fallback_config)
                logger.info("範例配置檔案載入成功")
            except Exception as fallback_error:
                logger.error(f"範例配置檔案也載入失敗: {fallback_error}")
                raise Exception(f"配置載入失敗: {config_error}. 範例配置也無法載入: {fallback_error}")
        
        # 取得 Lark 配置
        lark_config = config_manager.get_lark_config()
        logger.info(f"Lark 配置已載入: {len(lark_config)} 個設定")
        
        # 步驟 2: 解析 XML 檔案
        logger.info("步驟 2: 解析 TestRail XML 檔案")
        parser = TestRailXMLParser()
        raw_test_cases = parser.parse_xml_file(xml_file_path)
        logger.info(f"成功解析 {len(raw_test_cases)} 個測試案例")
        
        # 步驟 3: 清理資料
        logger.info("步驟 3: 清理測試案例資料")
        cleaner = TestCaseDataCleaner()
        cleaned_test_cases = []
        
        for i, raw_case in enumerate(raw_test_cases):
            try:
                cleaned_case = cleaner.clean_test_case_fields(raw_case)
                cleaned_test_cases.append(cleaned_case)
                logger.debug(f"清理測試案例 {i+1}: {cleaned_case.get('test_case_number', 'Unknown')}")
            except Exception as e:
                logger.warning(f"清理測試案例 {i+1} 時發生錯誤: {e}")
                continue
        
        logger.info(f"成功清理 {len(cleaned_test_cases)} 個測試案例")
        
        # 步驟 4: 格式轉換
        logger.info("步驟 4: 轉換為 Lark 格式")
        formatter = LarkDataFormatter()
        lark_records = formatter.batch_format_records(cleaned_test_cases)
        logger.info(f"成功格式轉換 {len(lark_records)} 個記錄")
        
        # 步驟 5: 寫入 Lark 表格
        logger.info("步驟 5: 寫入 Lark 表格")
        client = SimpleLarkClient(
            app_id=lark_config["app_id"],
            app_secret=lark_config["app_secret"]
        )
        
        # 設定表格資訊
        if not client.set_table_info(wiki_token, table_id):
            logger.error("設定 Lark 表格資訊失敗")
            return False
        
        # 批次建立記錄
        success, record_ids = client.batch_create_records(lark_records)
        
        if success:
            logger.info(f"=== 轉換成功完成 ===")
            logger.info(f"成功建立 {len(record_ids)} 筆記錄")
            logger.info(f"處理成功率: {len(record_ids)}/{len(raw_test_cases)} ({len(record_ids)/len(raw_test_cases)*100:.1f}%)")
            return True
        else:
            logger.error("寫入 Lark 表格失敗")
            return False
            
    except Exception as e:
        # 如果 logger 還沒有設定，直接 print 錯誤
        if 'logger' in locals():
            logger.error(f"轉換流程執行失敗: {e}")
            logger.debug("詳細錯誤資訊:", exc_info=True)
        else:
            print(f"ERROR: 轉換流程執行失敗: {e}")
            import traceback
            traceback.print_exc()
        return False


def handle_conversion_request() -> bool:
    """
    處理轉換請求（互動模式）
    
    Returns:
        處理是否成功
    """
    logger = logging.getLogger("main")
    cli = InteractiveCLI()
    
    try:
        # 取得使用者輸入
        logger.info("取得使用者輸入...")
        xml_file_path = cli.get_file_path_input()
        lark_config = cli.get_lark_config_input()
        
        # 執行轉換流程
        logger.info("開始執行轉換流程...")
        success = main_conversion_flow(
            xml_file_path=xml_file_path,
            wiki_token=lark_config["wiki_token"],
            table_id=lark_config["table_id"],
            config_path="config/config.yaml"
        )
        
        # 顯示結果
        if success:
            cli.show_results(1, 0)  # 1成功，0錯誤
        else:
            cli.show_results(0, 1)  # 0成功，1錯誤
            
        return success
        
    except ValidationError:
        logger.info("用戶取消操作")
        return False
    except Exception as e:
        logger.error(f"處理轉換請求時發生錯誤: {e}")
        cli.show_results(0, 1)  # 0成功，1錯誤
        return False


def handle_test_connection() -> bool:
    """
    處理連接測試請求（互動模式）
    
    Returns:
        測試是否成功
    """
    logger = logging.getLogger("main")
    cli = InteractiveCLI()
    
    try:
        # 取得使用者輸入
        logger.info("取得 Lark 連接設定...")
        lark_config = cli.get_lark_config_input()
        
        # 載入應用程式配置
        config_manager = ConfigManager()
        try:
            config_manager.load_config("config/config.yaml")
        except Exception as config_error:
            logger.error(f"配置檔案載入失敗: {config_error}")
            # 嘗試載入範例配置
            try:
                config_manager.load_config("config/config.yaml.example")
                logger.info("使用範例配置檔案")
            except Exception as fallback_error:
                logger.error(f"範例配置檔案也載入失敗: {fallback_error}")
                cli.show_results(0, 1)  # 0成功，1錯誤
                return False
        
        app_config = config_manager.get_lark_config()
        
        # 測試連接
        logger.info("測試 Lark API 連接...")
        client = SimpleLarkClient(
            app_id=app_config["app_id"],
            app_secret=app_config["app_secret"]
        )
        
        # 設定表格資訊
        if not client.set_table_info(lark_config["wiki_token"], lark_config["table_id"]):
            logger.error("設定表格資訊失敗")
            cli.show_results(0, 1)  # 0成功，1錯誤
            return False
        
        # 執行連接測試
        connection_ok = client.test_connection()
        
        # 顯示結果
        if connection_ok:
            logger.info("Lark API 連接測試成功")
            cli.show_results(1, 0)  # 1成功，0錯誤
        else:
            logger.error("Lark API 連接測試失敗")
            cli.show_results(0, 1)  # 0成功，1錯誤
        
        return connection_ok
        
    except ValidationError:
        logger.info("用戶取消操作")
        return False
    except Exception as e:
        logger.error(f"測試連接時發生錯誤: {e}")
        cli.show_results(0, 1)  # 0成功，1錯誤
        return False


def parse_command_line_args(args: Optional[list] = None) -> argparse.Namespace:
    """
    解析命令列參數
    
    Args:
        args: 命令列參數列表（用於測試）
        
    Returns:
        解析後的參數物件
    """
    parser = argparse.ArgumentParser(
        description="TestRail 轉換器 - 將 TestRail XML 檔案轉換為 Lark 表格",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  互動模式:
    python main.py
    
  轉換模式:
    python main.py --xml-file test.xml --wiki-token docABC123 --table-id tblXYZ789
    
  連接測試:
    python main.py --mode test --wiki-token docABC123 --table-id tblXYZ789
    
  使用配置檔案:
    python main.py --xml-file test.xml --wiki-token docABC123 --table-id tblXYZ789 --config config.yaml
        """
    )
    
    parser.add_argument(
        "--xml-file",
        type=str,
        help="TestRail XML 檔案路徑"
    )
    
    parser.add_argument(
        "--wiki-token",
        type=str,
        help="Lark Wiki Token (格式: docXXXXXX)"
    )
    
    parser.add_argument(
        "--table-id",
        type=str,
        help="Lark 表格 ID (格式: tblXXXXXX)"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="配置檔案路徑 (預設: config/config.yaml)"
    )
    
    parser.add_argument(
        "--mode",
        choices=["interactive", "convert", "test"],
        default="interactive",
        help="執行模式 (預設: interactive)"
    )
    
    parsed_args = parser.parse_args(args)
    
    # 根據參數自動判斷模式
    if parsed_args.xml_file and parsed_args.wiki_token and parsed_args.table_id:
        parsed_args.mode = "convert"
    elif parsed_args.mode == "interactive" and (parsed_args.wiki_token or parsed_args.table_id):
        # 如果有部分 Lark 參數但沒有 XML 檔案，可能是測試模式
        if not parsed_args.xml_file:
            parsed_args.mode = "test"
    
    return parsed_args


def setup_application_logging(config_path: Optional[str] = None) -> logging.Logger:
    """
    設定應用程式日誌系統
    
    Args:
        config_path: 配置檔案路徑
        
    Returns:
        配置好的主程式 Logger
    """
    try:
        # 載入配置檔案
        config_manager = ConfigManager()
        if config_path:
            config_manager.load_config(config_path)
        else:
            config_manager.load_config("config/config.yaml")
        
        # 設定主程式 Logger
        logger = setup_logger("main", config_path=config_path or "config/config.yaml")
        return logger
        
    except Exception as e:
        # 如果配置載入失敗，使用預設設定
        logger = setup_logger("main", config_path=None)
        logger.warning(f"載入配置檔案失敗，使用預設設定: {e}")
        return logger


def main() -> int:
    """
    主程式入口點
    
    Returns:
        程式退出碼 (0=成功, 1=失敗)
    """
    try:
        # 解析命令列參數
        args = parse_command_line_args()
        
        # 設定日誌系統
        logger = setup_application_logging(args.config)
        logger.info("TestRail 轉換器啟動")
        logger.debug(f"執行模式: {args.mode}")
        
        # 根據模式執行不同邏輯
        if args.mode == "convert":
            # 命令列轉換模式
            logger.info("執行命令列轉換模式")
            
            # 驗證必要參數
            if not all([args.xml_file, args.wiki_token, args.table_id]):
                logger.error("轉換模式需要 --xml-file, --wiki-token, --table-id 參數")
                print("錯誤: 轉換模式需要 --xml-file, --wiki-token, --table-id 參數")
                return 1
            
            # 驗證檔案存在
            if not validate_file_path(args.xml_file, allowed_extensions=['.xml']):
                logger.error(f"XML 檔案不存在或格式不正確: {args.xml_file}")
                print(f"錯誤: XML 檔案不存在或格式不正確: {args.xml_file}")
                return 1
            
            # 執行轉換
            success = main_conversion_flow(
                xml_file_path=args.xml_file,
                wiki_token=args.wiki_token,
                table_id=args.table_id,
                config_path=args.config
            )
            
            return 0 if success else 1
            
        elif args.mode == "test":
            # 命令列測試模式
            logger.info("執行命令列測試模式")
            
            # 驗證必要參數
            if not all([args.wiki_token, args.table_id]):
                logger.error("測試模式需要 --wiki-token, --table-id 參數")
                print("錯誤: 測試模式需要 --wiki-token, --table-id 參數")
                return 1
            
            # 執行連接測試
            success = handle_test_connection()
            return 0 if success else 1
            
        else:
            # 互動模式（預設）
            logger.info("執行互動模式")
            
            cli = InteractiveCLI()
            
            while True:
                try:
                    choice = cli.show_main_menu()
                    
                    if choice == "convert":
                        logger.info("用戶選擇轉換功能")
                        handle_conversion_request()
                    elif choice == "test":
                        logger.info("用戶選擇連接測試")
                        handle_test_connection()
                    elif choice == "quit":
                        logger.info("用戶選擇退出")
                        print("\n謝謝使用 TestRail 轉換器！")
                        break
                    else:
                        logger.warning(f"未知的選擇: {choice}")
                        
                except KeyboardInterrupt:
                    logger.info("用戶中斷操作")
                    print("\n\n程式已中斷")
                    break
                except Exception as e:
                    logger.error(f"互動模式執行錯誤: {e}")
                    print(f"發生錯誤: {e}")
                    continue
            
            return 0
            
    except KeyboardInterrupt:
        print("\n\n程式已中斷")
        return 0
    except Exception as e:
        # 設定基本日誌（如果主日誌系統失敗）
        logging.basicConfig(level=logging.ERROR)
        logger = logging.getLogger("main")
        logger.error(f"主程式執行失敗: {e}")
        logger.debug("詳細錯誤資訊:", exc_info=True)
        
        print(f"程式執行失敗: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())