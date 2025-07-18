#!/usr/bin/env python3
"""
TestRail 轉換並上傳至 Lark 多維表格
正式版本轉換腳本

使用方法:
    python convert_testrail_to_lark.py --input file.xml --table-url "https://xxx.larksuite.com/base/..."
    python convert_testrail_to_lark.py --input ./xml_files/ --table-url "https://xxx.larksuite.com/base/..."
"""

import sys
import os
import argparse
import yaml
import glob
from pathlib import Path
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse, parse_qs
import logging

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models.lark_client import LarkClient
from models.lark_field_mapping import lark_processor
from parser.xml_parser import TestRailXMLParser

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('convert_testrail_to_lark.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LarkTableURLParser:
    """Lark 表格 URL 解析器"""
    
    @staticmethod
    def parse_table_url(url: str) -> Optional[Dict[str, str]]:
        """
        解析 Lark 表格 URL
        
        範例 URL:
        https://xxx.larksuite.com/base/Q4XxwaS2Cif80DkAku9lMKuAgof?table=tblkN8BxqYwxjc3S&view=vewJHSwJVd
        https://xxx.larksuite.com/wiki/Q4XxwaS2Cif80DkAku9lMKuAgof?table=tblkN8BxqYwxjc3S&view=vewJHSwJVd
        
        返回:
        {
            'wiki_token': 'Q4XxwaS2Cif80DkAku9lMKuAgof',
            'table_id': 'tblkN8BxqYwxjc3S'
        }
        """
        try:
            parsed = urlparse(url)
            
            # 從路徑中提取 wiki_token
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) >= 2 and path_parts[0] in ['base', 'wiki']:
                wiki_token = path_parts[1]
            else:
                logger.error(f"無法從 URL 路徑中提取 wiki_token: {url}")
                return None
            
            # 從查詢參數中提取 table_id
            query_params = parse_qs(parsed.query)
            table_id = query_params.get('table', [None])[0]
            
            if not table_id:
                logger.error(f"無法從 URL 查詢參數中提取 table_id: {url}")
                return None
            
            return {
                'wiki_token': wiki_token,
                'table_id': table_id
            }
            
        except Exception as e:
            logger.error(f"解析 URL 異常: {e}")
            return None


class TestRailToLarkConverter:
    """TestRail 轉換至 Lark 轉換器"""
    
    def __init__(self, config_path: str = 'config.yaml'):
        self.config = self._load_config(config_path)
        self.lark_client = None
        self.parser = TestRailXMLParser()
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """載入配置檔案"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.info(f"配置檔案載入成功: {config_path}")
                return config
        except Exception as e:
            logger.error(f"無法載入配置檔案 {config_path}: {e}")
            sys.exit(1)
    
    def _init_lark_client(self) -> bool:
        """初始化 Lark 客戶端"""
        try:
            lark_config = self.config.get('lark_base', {})
            app_id = lark_config.get('app_id')
            app_secret = lark_config.get('app_secret')
            
            if not app_id or not app_secret:
                logger.error("配置檔案中缺少 Lark app_id 或 app_secret")
                return False
            
            self.lark_client = LarkClient(app_id=app_id, app_secret=app_secret)
            
            # 測試連接
            if not self.lark_client.test_connection():
                logger.error("Lark 連接失敗")
                return False
            
            logger.info("Lark 客戶端初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"初始化 Lark 客戶端失敗: {e}")
            return False
    
    def _collect_xml_files(self, input_path: str) -> List[str]:
        """收集 XML 檔案"""
        xml_files = []
        
        if os.path.isfile(input_path):
            if input_path.lower().endswith('.xml'):
                xml_files.append(input_path)
            else:
                logger.warning(f"檔案不是 XML 格式: {input_path}")
        elif os.path.isdir(input_path):
            # 搜尋目錄中的所有 XML 檔案
            pattern = os.path.join(input_path, '**/*.xml')
            xml_files = glob.glob(pattern, recursive=True)
            logger.info(f"在目錄 {input_path} 中找到 {len(xml_files)} 個 XML 檔案")
        else:
            logger.error(f"輸入路徑不存在: {input_path}")
        
        return xml_files
    
    def _parse_xml_files(self, xml_files: List[str]) -> List[Any]:
        """解析 XML 檔案"""
        all_test_cases = []
        
        for xml_file in xml_files:
            try:
                logger.info(f"解析 XML 檔案: {xml_file}")
                test_suite = self.parser.parse_file(xml_file)
                
                if test_suite:
                    test_cases = test_suite.get_all_cases()
                    all_test_cases.extend(test_cases)
                    logger.info(f"✅ 解析成功: {xml_file} ({len(test_cases)} 個測試案例)")
                else:
                    logger.warning(f"❌ 解析失敗: {xml_file}")
                    
            except Exception as e:
                logger.error(f"❌ 解析異常 {xml_file}: {e}")
                continue
        
        logger.info(f"總計解析 {len(all_test_cases)} 個測試案例")
        return all_test_cases
    
    def _convert_to_lark_format(self, test_cases: List[Any]) -> List[Dict[str, Any]]:
        """轉換為 Lark 格式"""
        lark_records = []
        failed_count = 0
        
        for test_case in test_cases:
            try:
                lark_data = lark_processor.convert_test_case_to_lark(test_case)
                lark_records.append(lark_data)
            except Exception as e:
                logger.error(f"轉換失敗 {test_case.id}: {e}")
                failed_count += 1
                continue
        
        logger.info(f"成功轉換 {len(lark_records)} 個測試案例")
        if failed_count > 0:
            logger.warning(f"轉換失敗 {failed_count} 個測試案例")
        
        return lark_records
    
    def _verify_table_fields(self, obj_token: str, table_id: str) -> bool:
        """驗證表格欄位"""
        try:
            field_names = self.lark_client.get_field_names(obj_token, table_id)
            logger.info(f"表格欄位: {field_names}")
            
            # 檢查必要欄位
            required_fields = lark_processor.get_lark_field_names()
            missing_fields = [field for field in required_fields if field not in field_names]
            
            if missing_fields:
                logger.error(f"❌ 缺少必要欄位: {missing_fields}")
                return False
            
            logger.info("✅ 所有必要欄位都存在")
            return True
            
        except Exception as e:
            logger.error(f"驗證表格欄位失敗: {e}")
            return False
    
    def _upload_to_lark(self, obj_token: str, table_id: str, lark_records: List[Dict[str, Any]]) -> bool:
        """上傳到 Lark 表格"""
        try:
            logger.info(f"準備上傳 {len(lark_records)} 個測試案例到 Lark 表格")
            
            # 批次上傳
            success, record_ids, error_messages = self.lark_client.batch_create_records(
                obj_token, table_id, lark_records
            )
            
            if success:
                logger.info(f"✅ 上傳成功！創建了 {len(record_ids)} 筆記錄")
                return True
            else:
                logger.error(f"❌ 上傳失敗，創建了 {len(record_ids)} 筆記錄")
                if error_messages:
                    for error in error_messages:
                        logger.error(f"  - {error}")
                return False
                
        except Exception as e:
            logger.error(f"上傳異常: {e}")
            return False
    
    def convert_and_upload(self, input_path: str, table_url: str, dry_run: bool = False) -> bool:
        """執行轉換並上傳"""
        logger.info("=== TestRail 轉換並上傳至 Lark 表格 ===")
        
        # 1. 解析表格 URL
        logger.info("📋 解析表格 URL...")
        table_info = LarkTableURLParser.parse_table_url(table_url)
        if not table_info:
            logger.error("❌ 無法解析表格 URL")
            return False
        
        wiki_token = table_info['wiki_token']
        table_id = table_info['table_id']
        logger.info(f"✅ Wiki Token: {wiki_token}")
        logger.info(f"✅ Table ID: {table_id}")
        
        # 2. 初始化 Lark 客戶端
        logger.info("📋 初始化 Lark 客戶端...")
        if not self._init_lark_client():
            return False
        
        # 3. 獲取 obj_token
        logger.info("🔍 獲取 obj_token...")
        obj_token = self.lark_client.get_obj_token(wiki_token)
        if not obj_token:
            logger.error("❌ 無法獲取 obj_token")
            return False
        logger.info(f"✅ obj_token: {obj_token}")
        
        # 4. 驗證表格欄位
        logger.info("🔍 驗證表格欄位...")
        if not self._verify_table_fields(obj_token, table_id):
            return False
        
        # 5. 收集 XML 檔案
        logger.info("📋 收集 XML 檔案...")
        xml_files = self._collect_xml_files(input_path)
        if not xml_files:
            logger.error("❌ 沒有找到 XML 檔案")
            return False
        
        # 6. 解析 XML 檔案
        logger.info("📋 解析 XML 檔案...")
        all_test_cases = self._parse_xml_files(xml_files)
        if not all_test_cases:
            logger.error("❌ 沒有解析到測試案例")
            return False
        
        # 7. 轉換為 Lark 格式
        logger.info("🔄 轉換測試案例格式...")
        lark_records = self._convert_to_lark_format(all_test_cases)
        if not lark_records:
            logger.error("❌ 沒有成功轉換的測試案例")
            return False
        
        # 8. 顯示轉換摘要
        logger.info("📋 轉換摘要:")
        logger.info(f"  - 輸入檔案: {len(xml_files)} 個")
        logger.info(f"  - 原始測試案例: {len(all_test_cases)} 個")
        logger.info(f"  - 成功轉換: {len(lark_records)} 個")
        
        # 顯示轉換範例
        if lark_records:
            logger.info("📋 轉換範例:")
            example = lark_records[0]
            for key, value in example.items():
                display_value = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                logger.info(f"  {key}: {display_value}")
        
        # 9. 上傳到 Lark（或乾運行）
        if dry_run:
            logger.info("🔍 乾運行模式 - 跳過上傳")
            logger.info("🎉 轉換測試完成！")
            return True
        else:
            logger.info("📤 上傳到 Lark 表格...")
            success = self._upload_to_lark(obj_token, table_id, lark_records)
            if success:
                logger.info("🎉 轉換並上傳完成！")
            return success


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description='TestRail 轉換並上傳至 Lark 多維表格',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用範例:
  # 轉換單個檔案
  python convert_testrail_to_lark.py --input "test.xml" --table-url "https://xxx.larksuite.com/base/Q4XxwaS2Cif80DkAku9lMKuAgof?table=tblkN8BxqYwxjc3S"
  
  # 轉換目錄中的所有 XML 檔案
  python convert_testrail_to_lark.py --input "./xml_files/" --table-url "https://xxx.larksuite.com/base/Q4XxwaS2Cif80DkAku9lMKuAgof?table=tblkN8BxqYwxjc3S"
  
  # 乾運行模式（只轉換不上傳）
  python convert_testrail_to_lark.py --input "test.xml" --table-url "https://xxx.larksuite.com/base/Q4XxwaS2Cif80DkAku9lMKuAgof?table=tblkN8BxqYwxjc3S" --dry-run
        '''
    )
    
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='輸入檔案路徑（單個 XML 檔案）或目錄路徑（包含 XML 檔案的目錄）'
    )
    
    parser.add_argument(
        '--table-url', '-t',
        required=True,
        help='Lark 表格 URL（包含 wiki_token 和 table_id）'
    )
    
    parser.add_argument(
        '--config', '-c',
        default='config.yaml',
        help='配置檔案路徑（預設: config.yaml）'
    )
    
    parser.add_argument(
        '--dry-run', '-d',
        action='store_true',
        help='乾運行模式，只進行轉換測試，不實際上傳'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='顯示詳細日誌'
    )
    
    args = parser.parse_args()
    
    # 設定日誌等級
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 檢查配置檔案
    if not os.path.exists(args.config):
        logger.error(f"配置檔案不存在: {args.config}")
        sys.exit(1)
    
    # 檢查輸入路徑
    if not os.path.exists(args.input):
        logger.error(f"輸入路徑不存在: {args.input}")
        sys.exit(1)
    
    try:
        # 執行轉換
        converter = TestRailToLarkConverter(args.config)
        success = converter.convert_and_upload(
            input_path=args.input,
            table_url=args.table_url,
            dry_run=args.dry_run
        )
        
        if success:
            logger.info("程式執行成功")
            sys.exit(0)
        else:
            logger.error("程式執行失敗")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("用戶中斷操作")
        sys.exit(1)
    except Exception as e:
        logger.error(f"程式異常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()