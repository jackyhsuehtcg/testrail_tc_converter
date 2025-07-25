"""
端到端整合測試

測試完整的 TestRail 轉換器系統，包括：
- 完整轉換流程測試
- 大檔案處理測試
- 異常情況處理測試
- 各模組間協調整合測試
"""

import pytest
import sys
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, Mock

# 加入 src 目錄到 Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from main import main_conversion_flow, main
from config.config_manager import ConfigManager


class TestEndToEndConversion:
    """端到端轉換測試"""
    
    def setup_method(self):
        """每個測試方法前的設定"""
        self.test_xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<suite>
    <sections>
        <section name="Login Tests">
            <case id="1">
                <title>TCG-001.002.003 登入功能測試</title>
                <priority>High</priority>
                <custom>
                    <preconds>用戶已註冊</preconds>
                    <steps>1. 打開登入頁面
2. 輸入有效憑證
3. 點擊登入按鈕</steps>
                    <expected>成功登入系統</expected>
                </custom>
            </case>
            <case id="2">
                <title>TCG-001.002.004 登出功能測試</title>
                <priority>Medium</priority>
                <custom>
                    <preconds>用戶已登入</preconds>
                    <steps>1. 點擊登出按鈕</steps>
                    <expected>成功登出系統</expected>
                </custom>
            </case>
        </section>
    </sections>
</suite>'''
        
        self.config_content = {
            "lark": {
                "app_id": "test_app_id",
                "app_secret": "test_app_secret",
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
                "test_case_number_pattern": "^TCG-\\d{3}\\.\\d{3}\\.\\d{3}$",
                "required_fields": ["test_case_number", "title", "steps", "expected_result"],
                "batch_processing": {
                    "batch_size": 500,
                    "max_retries": 3,
                    "retry_delay": 1.0
                }
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "logs/conversion.log"
            }
        }
    
    @patch('main.SimpleLarkClient')
    def test_complete_conversion_flow(self, mock_client_class):
        """測試完整的轉換流程"""
        # 設定 Mock Lark 客戶端
        mock_client = Mock()
        mock_client.set_table_info.return_value = True
        mock_client.batch_create_records.return_value = (True, ["record_1", "record_2"])
        mock_client_class.return_value = mock_client
        
        # 創建臨時檔案
        with tempfile.TemporaryDirectory() as temp_dir:
            # 創建 XML 檔案
            xml_file = os.path.join(temp_dir, "test.xml")
            with open(xml_file, 'w', encoding='utf-8') as f:
                f.write(self.test_xml_content)
            
            # 創建配置檔案
            config_file = os.path.join(temp_dir, "config.yaml")
            import yaml
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config_content, f, allow_unicode=True)
            
            # 執行轉換流程
            result = main_conversion_flow(
                xml_file_path=xml_file,
                wiki_token="docABC123456789",
                table_id="tblXYZ123456",
                config_path=config_file
            )
            
            # 驗證結果
            assert result is True
            
            # 驗證 Lark 客戶端被正確調用
            mock_client.set_table_info.assert_called_once_with("docABC123456789", "tblXYZ123456")
            mock_client.batch_create_records.assert_called_once()
            
            # 驗證傳送到 Lark 的資料格式
            call_args = mock_client.batch_create_records.call_args[0][0]
            assert len(call_args) == 2  # 兩個測試案例
            
            # 驗證第一個測試案例
            first_record = call_args[0]
            assert first_record["test_case_number"] == "TCG-001.002.003"
            assert first_record["title"] == "登入功能測試"
            assert first_record["priority"] == "High"
            assert "打開登入頁面" in first_record["steps"]
            assert first_record["expected_result"] == "成功登入系統"
    
    @patch('main.SimpleLarkClient')
    def test_conversion_with_data_cleaning(self, mock_client_class):
        """測試包含資料清理的轉換流程"""
        # 包含需要清理的資料的 XML
        dirty_xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<suite>
    <sections>
        <section name="Test Cases">
            <case id="1">
                <title>TCG001.002.003 **粗體測試**標題</title>
                <priority>high</priority>
                <custom>
                    <preconds>前置條件包含 [連結說明](http://example.com)</preconds>
                    <steps>步驟包含 `程式碼` 和 *斜體* 文字</steps>
                    <expected>預期結果正常</expected>
                </custom>
            </case>
        </section>
    </sections>
</suite>'''
        
        # 設定 Mock
        mock_client = Mock()
        mock_client.set_table_info.return_value = True
        mock_client.batch_create_records.return_value = (True, ["record_1"])
        mock_client_class.return_value = mock_client
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # 創建包含需要清理資料的 XML 檔案
            xml_file = os.path.join(temp_dir, "dirty.xml")
            with open(xml_file, 'w', encoding='utf-8') as f:
                f.write(dirty_xml_content)
            
            # 創建配置檔案
            config_file = os.path.join(temp_dir, "config.yaml")
            import yaml
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config_content, f, allow_unicode=True)
            
            # 執行轉換
            result = main_conversion_flow(
                xml_file_path=xml_file,
                wiki_token="docABC123456789",
                table_id="tblXYZ123456",
                config_path=config_file
            )
            
            # 驗證結果
            assert result is True
            
            # 檢查資料清理效果
            call_args = mock_client.batch_create_records.call_args[0][0]
            cleaned_record = call_args[0]
            
            # 驗證測試案例編號修正（添加缺失的 hyphen）
            assert cleaned_record["test_case_number"] == "TCG-001.002.003"
            
            # 驗證標題清理（移除 Markdown 格式）
            assert "**" not in cleaned_record["title"]
            assert "粗體測試標題" in cleaned_record["title"]
            
            # 驗證優先級標準化
            assert cleaned_record["priority"] == "High"  # 從 "high" 標準化為 "High"
            
            # 驗證 Markdown 內容清理
            assert "`" not in cleaned_record["steps"]
            assert "*" not in cleaned_record["steps"]
            assert "程式碼" in cleaned_record["steps"]
            assert "斜體" in cleaned_record["steps"]
            
            # 驗證 URL 連結處理
            assert "連結說明" in cleaned_record["precondition"]
            assert "http://example.com" not in cleaned_record["precondition"]
    
    @patch('main.SimpleLarkClient')
    def test_large_file_processing(self, mock_client_class):
        """測試大檔案處理"""
        # 設定 Mock
        mock_client = Mock()
        mock_client.set_table_info.return_value = True
        mock_client.batch_create_records.return_value = (True, [f"record_{i}" for i in range(100)])
        mock_client_class.return_value = mock_client
        
        # 生成包含 100 個測試案例的大 XML 檔案
        large_xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<suite>
    <sections>
        <section name="Large Test Suite">'''
        
        for i in range(100):
            case_num = f"{i+1:03d}"
            large_xml_content += f'''
            <case id="{i+1}">
                <title>TCG-001.002.{case_num} 測試案例 {i+1}</title>
                <priority>Medium</priority>
                <custom>
                    <preconds>前置條件 {i+1}</preconds>
                    <steps>測試步驟 {i+1}</steps>
                    <expected>預期結果 {i+1}</expected>
                </custom>
            </case>'''
        
        large_xml_content += '''
        </section>
    </sections>
</suite>'''
        
        with tempfile.TemporaryDirectory() as temp_dir:
            xml_file = os.path.join(temp_dir, "large.xml")
            with open(xml_file, 'w', encoding='utf-8') as f:
                f.write(large_xml_content)
            
            # 創建配置檔案
            config_file = os.path.join(temp_dir, "config.yaml")
            import yaml
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config_content, f, allow_unicode=True)
            
            # 執行轉換
            result = main_conversion_flow(
                xml_file_path=xml_file,
                wiki_token="docABC123456789",
                table_id="tblXYZ123456",
                config_path=config_file
            )
            
            # 驗證結果
            assert result is True
            
            # 驗證處理了所有測試案例
            call_args = mock_client.batch_create_records.call_args[0][0]
            assert len(call_args) == 100
            
            # 驗證第一個和最後一個案例
            first_case = call_args[0]
            last_case = call_args[-1]
            
            assert first_case["test_case_number"] == "TCG-001.002.001"
            assert "測試案例 1" in first_case["title"]
            
            assert last_case["test_case_number"] == "TCG-001.002.100"
            assert "測試案例 100" in last_case["title"]
    
    def test_invalid_xml_file_handling(self):
        """測試無效 XML 檔案處理"""
        invalid_xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<suite>
    <sections>
        <section name="Invalid">
            <case id="1">
                <title>測試案例</title>
                <!-- 缺少結束標籤 -->
            </case>
        <!-- 缺少 section 結束標籤 -->
    </sections>
</suite>'''
        
        with tempfile.TemporaryDirectory() as temp_dir:
            xml_file = os.path.join(temp_dir, "invalid.xml")
            with open(xml_file, 'w', encoding='utf-8') as f:
                f.write(invalid_xml_content)
            
            # 執行轉換，應該失敗但不會崩潰
            result = main_conversion_flow(
                xml_file_path=xml_file,
                wiki_token="docABC123456789",
                table_id="tblXYZ123456"
            )
            
            # 驗證失敗結果
            assert result is False
    
    def test_nonexistent_file_handling(self):
        """測試不存在檔案的處理"""
        result = main_conversion_flow(
            xml_file_path="/nonexistent/path/file.xml",
            wiki_token="docABC123456789",
            table_id="tblXYZ123456"
        )
        
        # 驗證失敗結果
        assert result is False
    
    @patch('main.SimpleLarkClient')
    def test_lark_api_failure_handling(self, mock_client_class):
        """測試 Lark API 失敗處理"""
        # 設定 Mock 使 API 調用失敗
        mock_client = Mock()
        mock_client.set_table_info.return_value = True
        mock_client.batch_create_records.return_value = (False, [])
        mock_client_class.return_value = mock_client
        
        with tempfile.TemporaryDirectory() as temp_dir:
            xml_file = os.path.join(temp_dir, "test.xml")
            with open(xml_file, 'w', encoding='utf-8') as f:
                f.write(self.test_xml_content)
            
            # 執行轉換
            result = main_conversion_flow(
                xml_file_path=xml_file,
                wiki_token="docABC123456789",
                table_id="tblXYZ123456"
            )
            
            # 驗證失敗結果
            assert result is False
    
    @patch('main.SimpleLarkClient')  
    def test_partial_success_handling(self, mock_client_class):
        """測試部分成功的處理"""
        # 設定 Mock 使部分記錄建立成功
        mock_client = Mock()
        mock_client.set_table_info.return_value = True
        mock_client.batch_create_records.return_value = (True, ["record_1"])  # 只有一個成功
        mock_client_class.return_value = mock_client
        
        with tempfile.TemporaryDirectory() as temp_dir:
            xml_file = os.path.join(temp_dir, "test.xml")
            with open(xml_file, 'w', encoding='utf-8') as f:
                f.write(self.test_xml_content)  # 包含兩個測試案例
            
            # 創建配置檔案
            config_file = os.path.join(temp_dir, "config.yaml")
            import yaml
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config_content, f, allow_unicode=True)
            
            # 執行轉換
            result = main_conversion_flow(
                xml_file_path=xml_file,
                wiki_token="docABC123456789",
                table_id="tblXYZ123456",
                config_path=config_file
            )
            
            # 部分成功仍視為成功
            assert result is True


class TestEndToEndCommandLine:
    """端到端命令列測試"""
    
    def setup_method(self):
        """每個測試方法前的設定"""
        self.simple_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<suite>
    <sections>
        <section name="Simple">
            <case id="1">
                <title>TCG-001.002.003 簡單測試</title>
                <priority>High</priority>
                <custom>
                    <preconds>無</preconds>
                    <steps>執行測試</steps>
                    <expected>測試通過</expected>
                </custom>
            </case>
        </section>
    </sections>
</suite>'''
    
    @patch('main.SimpleLarkClient')
    def test_command_line_conversion_mode(self, mock_client_class):
        """測試命令列轉換模式"""
        # 設定 Mock
        mock_client = Mock()
        mock_client.set_table_info.return_value = True
        mock_client.batch_create_records.return_value = (True, ["record_1"])
        mock_client_class.return_value = mock_client
        
        with tempfile.TemporaryDirectory() as temp_dir:
            xml_file = os.path.join(temp_dir, "test.xml")
            with open(xml_file, 'w', encoding='utf-8') as f:
                f.write(self.simple_xml)
            
            # 創建配置檔案
            config_file = os.path.join(temp_dir, "config.yaml")
            config_content = {
                "lark": {
                    "app_id": "test_app_id",
                    "app_secret": "test_app_secret"
                }
            }
            import yaml
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_content, f, allow_unicode=True)
            
            # 設定命令列參數
            test_argv = [
                'main.py',
                '--xml-file', xml_file,
                '--wiki-token', 'docABC123456789',
                '--table-id', 'tblXYZ123456',
                '--config', config_file
            ]
            
            # 執行主程式
            with patch('sys.argv', test_argv):
                exit_code = main()
            
            # 驗證成功
            assert exit_code == 0
            mock_client.batch_create_records.assert_called_once()
    
    def test_command_line_invalid_file(self):
        """測試命令列模式無效檔案處理"""
        # 設定命令列參數指向不存在的檔案
        test_argv = [
            'main.py',
            '--xml-file', '/nonexistent/file.xml',
            '--wiki-token', 'docABC123456789',
            '--table-id', 'tblXYZ123456'
        ]
        
        # 執行主程式
        with patch('sys.argv', test_argv):
            exit_code = main()
        
        # 驗證失敗
        assert exit_code == 1
    
    def test_command_line_missing_arguments(self):
        """測試命令列模式缺失參數處理"""
        # 設定不完整的命令列參數
        test_argv = [
            'main.py',
            '--xml-file', '/some/file.xml'
            # 缺少 wiki-token 和 table-id
        ]
        
        # 執行主程式
        with patch('sys.argv', test_argv):
            exit_code = main()
        
        # 驗證失敗（因為缺少必要參數）
        assert exit_code == 1


class TestEndToEndErrorRecovery:
    """端到端錯誤恢復測試"""
    
    @patch('config.config_manager.ConfigManager')
    def test_config_error_recovery(self, mock_config_class):
        """測試配置錯誤恢復"""
        # 設定配置管理器拋出異常
        mock_config_manager = Mock()
        mock_config_manager.load_config.side_effect = Exception("配置載入失敗")
        mock_config_class.return_value = mock_config_manager
        
        # 執行轉換流程
        result = main_conversion_flow(
            xml_file_path="/some/file.xml",
            wiki_token="docABC123456789",
            table_id="tblXYZ123456",
            config_path="invalid_config.yaml"
        )
        
        # 驗證錯誤被正確處理
        assert result is False
    
    @patch('parsers.xml_parser.TestRailXMLParser')
    def test_parser_error_recovery(self, mock_parser_class):
        """測試解析器錯誤恢復"""
        # 設定解析器拋出異常
        mock_parser = Mock()
        mock_parser.parse_xml_file.side_effect = Exception("XML 解析失敗")
        mock_parser_class.return_value = mock_parser
        
        # 執行轉換流程
        result = main_conversion_flow(
            xml_file_path="/some/file.xml",
            wiki_token="docABC123456789",
            table_id="tblXYZ123456"
        )
        
        # 驗證錯誤被正確處理
        assert result is False
    
    @patch('parsers.data_cleaner.TestCaseDataCleaner')
    @patch('parsers.xml_parser.TestRailXMLParser')
    def test_data_cleaner_error_recovery(self, mock_parser_class, mock_cleaner_class):
        """測試資料清理器錯誤恢復"""
        # 設定解析器正常工作
        mock_parser = Mock()
        mock_parser.parse_xml_file.return_value = [{"title": "Test"}]
        mock_parser_class.return_value = mock_parser
        
        # 設定清理器拋出異常
        mock_cleaner = Mock()
        mock_cleaner.clean_test_case_fields.side_effect = Exception("清理失敗")
        mock_cleaner_class.return_value = mock_cleaner
        
        # 執行轉換流程
        result = main_conversion_flow(
            xml_file_path="/some/file.xml",
            wiki_token="docABC123456789",
            table_id="tblXYZ123456"
        )
        
        # 系統應該能夠恢復（跳過有問題的記錄）
        # 但因為沒有有效記錄，最終會失敗
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])