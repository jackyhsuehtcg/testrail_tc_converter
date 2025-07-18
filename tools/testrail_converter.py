#!/usr/bin/env python3
"""
TestRail 測試案例轉換器命令行工具
支援將 TestRail XML 檔案轉換為多種格式
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import List, Optional

# 設定路徑以便導入模組
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parser import TestRailXMLParser
from src.exporters import TreeVisualizer, TextExporter


def setup_logging(verbose: bool = False) -> None:
    """設定日誌"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def parse_xml_file(file_path: str) -> Optional[object]:
    """解析 XML 檔案"""
    parser = TestRailXMLParser()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"正在解析檔案: {file_path}")
        suite = parser.parse_file(file_path)
        logger.info(f"解析成功: {suite.name} (ID: {suite.id})")
        logger.info(f"總測試案例數: {suite.get_total_cases_count()}")
        return suite
    except Exception as e:
        logger.error(f"解析檔案失敗: {e}")
        return None


def export_tree_view(suite: object, output_path: str, detailed: bool = False) -> None:
    """輸出樹狀圖"""
    visualizer = TreeVisualizer()
    logger = logging.getLogger(__name__)
    
    try:
        if detailed:
            content = visualizer.generate_detailed_tree(suite, show_test_cases=False)
        else:
            content = visualizer.generate_ascii_tree(suite)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"樹狀圖已儲存至: {output_path}")
    except Exception as e:
        logger.error(f"輸出樹狀圖失敗: {e}")


def export_text_formats(suite: object, output_dir: str, formats: List[str], 
                       include_details: bool = True) -> None:
    """輸出文字格式"""
    exporter = TextExporter()
    logger = logging.getLogger(__name__)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    base_name = f"{suite.name}_{suite.id}"
    # 清理檔案名稱中的特殊字符
    safe_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_name = safe_name.replace(' ', '_')
    
    try:
        if 'txt' in formats:
            txt_path = output_path / f"{safe_name}.txt"
            exporter.export_to_txt(suite, str(txt_path), include_details)
            logger.info(f"TXT 檔案已儲存至: {txt_path}")
        
        if 'md' in formats or 'markdown' in formats:
            md_path = output_path / f"{safe_name}.md"
            exporter.export_to_markdown(suite, str(md_path), include_details)
            logger.info(f"Markdown 檔案已儲存至: {md_path}")
        
        if 'tree' in formats:
            tree_path = output_path / f"{safe_name}_tree.txt"
            export_tree_view(suite, str(tree_path), detailed=False)
        
        if 'detailed_tree' in formats:
            detailed_tree_path = output_path / f"{safe_name}_detailed_tree.txt"
            export_tree_view(suite, str(detailed_tree_path), detailed=True)
            
    except Exception as e:
        logger.error(f"輸出文字格式失敗: {e}")


def main():
    """主程式"""
    parser = argparse.ArgumentParser(
        description='TestRail 測試案例轉換器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
範例用法:
  # 將 XML 檔案轉換為 TXT 和 Markdown 格式
  python testrail_converter.py input.xml -o output/ -f txt md
  
  # 只輸出樹狀圖
  python testrail_converter.py input.xml -o output/ -f tree
  
  # 輸出包含詳細資訊的報告
  python testrail_converter.py input.xml -o output/ -f txt md --details
  
  # 處理多個檔案
  python testrail_converter.py file1.xml file2.xml -o output/ -f txt md tree
        '''
    )
    
    parser.add_argument(
        'input_files',
        nargs='+',
        help='TestRail XML 檔案路徑 (可指定多個檔案)'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='output',
        help='輸出目錄 (預設: output)'
    )
    
    parser.add_argument(
        '-f', '--format',
        nargs='+',
        choices=['txt', 'md', 'markdown', 'tree', 'detailed_tree'],
        default=['txt', 'md', 'tree'],
        help='輸出格式 (預設: txt md tree)'
    )
    
    parser.add_argument(
        '--details',
        action='store_true',
        help='包含詳細的測試案例資訊'
    )
    
    parser.add_argument(
        '--no-details',
        action='store_true',
        help='不包含詳細的測試案例資訊'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='詳細輸出模式'
    )
    
    args = parser.parse_args()
    
    # 設定日誌
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # 處理詳細資訊參數
    include_details = True
    if args.no_details:
        include_details = False
    elif args.details:
        include_details = True
    
    logger.info(f"開始處理 {len(args.input_files)} 個檔案")
    logger.info(f"輸出目錄: {args.output}")
    logger.info(f"輸出格式: {', '.join(args.format)}")
    logger.info(f"包含詳細資訊: {include_details}")
    
    # 處理每個輸入檔案
    success_count = 0
    for input_file in args.input_files:
        logger.info(f"\n處理檔案: {input_file}")
        
        # 檢查檔案是否存在
        if not Path(input_file).exists():
            logger.error(f"檔案不存在: {input_file}")
            continue
        
        # 解析檔案
        suite = parse_xml_file(input_file)
        if suite is None:
            logger.error(f"跳過檔案: {input_file}")
            continue
        
        # 輸出格式
        try:
            export_text_formats(suite, args.output, args.format, include_details)
            success_count += 1
            logger.info(f"檔案處理完成: {input_file}")
        except Exception as e:
            logger.error(f"輸出檔案失敗: {input_file}, 錯誤: {e}")
    
    logger.info(f"\n處理完成! 成功處理 {success_count}/{len(args.input_files)} 個檔案")
    
    if success_count == 0:
        sys.exit(1)


if __name__ == '__main__':
    main()