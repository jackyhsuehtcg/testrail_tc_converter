"""
主程式整合測試

測試 main.py 模組的各項功能，包括：
- 完整轉換流程
- 錯誤處理流程
- 命令列參數處理
- 各模組協調整合
"""

import pytest
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

# 加入 src 目錄到 Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from main import (
    main_conversion_flow,
    handle_conversion_request,
    handle_test_connection,
    parse_command_line_args,
    setup_application_logging,
    main
)


class TestMainConversionFlow:
    """主要轉換流程測試"""
    
    def setup_method(self):
        """每個測試方法前的設定"""
        self.mock_config = {
            "lark": {
                "app_id": "test_app_id",
                "app_secret": "test_app_secret"
            }
        }
        
        self.test_data = [
            {
                "test_case_number": "TCG-001.002.003",
                "title": "登入功能測試",
                "priority": "High",
                "precondition": "用戶已註冊",
                "steps": "1. 打開登入頁面\n2. 輸入憑證",
                "expected_result": "成功登入"
            }
        ]
    
    @patch('main.setup_application_logging')
    @patch('main.ConfigManager')
    @patch('main.TestRailXMLParser')
    @patch('main.TestCaseDataCleaner')
    @patch('main.LarkDataFormatter')
    @patch('main.SimpleLarkClient')
    def test_successful_conversion_flow(self, mock_client_class, mock_formatter_class, 
                                      mock_cleaner_class, mock_parser_class, 
                                      mock_config_class, mock_setup_logging):
        """測試成功的完整轉換流程"""
        # 設定 mocks
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        mock_config_manager = Mock()
        mock_config_manager.get_lark_config.return_value = self.mock_config["lark"]
        mock_config_class.return_value = mock_config_manager
        
        mock_parser = Mock()
        mock_parser.parse_xml_file.return_value = self.test_data
        mock_parser_class.return_value = mock_parser
        
        mock_cleaner = Mock()
        mock_cleaner.clean_test_case_fields.return_value = self.test_data[0]
        mock_cleaner_class.return_value = mock_cleaner
        
        mock_formatter = Mock()
        mock_formatter.batch_format_records.return_value = self.test_data
        mock_formatter_class.return_value = mock_formatter
        
        mock_client = Mock()
        mock_client.set_table_info.return_value = True
        mock_client.batch_create_records.return_value = (True, ["record_id_1"])
        mock_client_class.return_value = mock_client
        
        # 執行轉換流程
        with tempfile.NamedTemporaryFile(suffix='.xml', delete=False) as temp_file:
            temp_file.write(b'<test>content</test>')
            xml_path = temp_file.name
        
        try:
            result = main_conversion_flow(
                xml_file_path=xml_path,
                wiki_token="docABC123",
                table_id="tblXYZ789",
                config_path="test_config.yaml"
            )
            
            # 驗證結果
            assert result is True
            
            # 驗證各模組被正確調用
            mock_parser.parse_xml_file.assert_called_once_with(xml_path)
            mock_cleaner.clean_test_case_fields.assert_called()
            mock_formatter.batch_format_records.assert_called()
            mock_client.set_table_info.assert_called_once_with("docABC123", "tblXYZ789")
            mock_client.batch_create_records.assert_called_once()
            
        finally:
            os.unlink(xml_path)
    
    @patch('main.setup_application_logging')
    @patch('main.ConfigManager')
    @patch('main.TestRailXMLParser')
    def test_xml_parsing_failure(self, mock_parser_class, mock_config_class, mock_setup_logging):
        """測試 XML 解析失敗的處理"""
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        mock_config_manager = Mock()
        mock_config_manager.get_lark_config.return_value = self.mock_config["lark"]
        mock_config_class.return_value = mock_config_manager
        
        mock_parser = Mock()
        mock_parser.parse_xml_file.side_effect = Exception("XML 解析失敗")
        mock_parser_class.return_value = mock_parser
        
        # 執行轉換流程
        result = main_conversion_flow(
            xml_file_path="/nonexistent/file.xml",
            wiki_token="docABC123",
            table_id="tblXYZ789"
        )
        
        # 驗證結果
        assert result is False
        mock_logger.error.assert_called()
    
    @patch('main.setup_application_logging')
    @patch('main.ConfigManager')
    @patch('main.TestRailXMLParser')
    @patch('main.TestCaseDataCleaner')
    @patch('main.LarkDataFormatter')
    @patch('main.SimpleLarkClient')
    def test_lark_api_failure(self, mock_client_class, mock_formatter_class, 
                            mock_cleaner_class, mock_parser_class, 
                            mock_config_class, mock_setup_logging):
        """測試 Lark API 呼叫失敗的處理"""
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        mock_config_manager = Mock()
        mock_config_manager.get_lark_config.return_value = self.mock_config["lark"]
        mock_config_class.return_value = mock_config_manager
        
        mock_parser = Mock()
        mock_parser.parse_xml_file.return_value = self.test_data
        mock_parser_class.return_value = mock_parser
        
        mock_cleaner = Mock()
        mock_cleaner.clean_test_case_fields.return_value = self.test_data[0]
        mock_cleaner_class.return_value = mock_cleaner
        
        mock_formatter = Mock()
        mock_formatter.batch_format_records.return_value = self.test_data
        mock_formatter_class.return_value = mock_formatter
        
        mock_client = Mock()
        mock_client.set_table_info.return_value = True
        mock_client.batch_create_records.return_value = (False, [])
        mock_client_class.return_value = mock_client
        
        # 執行轉換流程
        with tempfile.NamedTemporaryFile(suffix='.xml', delete=False) as temp_file:
            temp_file.write(b'<test>content</test>')
            xml_path = temp_file.name
        
        try:
            result = main_conversion_flow(
                xml_file_path=xml_path,
                wiki_token="docABC123",
                table_id="tblXYZ789"
            )
            
            # 驗證結果
            assert result is False
            mock_logger.error.assert_called()
            
        finally:
            os.unlink(xml_path)
    
    @patch('main.setup_application_logging')
    @patch('main.ConfigManager')
    def test_config_loading_failure(self, mock_config_class, mock_setup_logging):
        """測試配置載入失敗的處理"""
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        mock_config_manager = Mock()
        mock_config_manager.load_config.side_effect = Exception("配置載入失敗")
        mock_config_class.return_value = mock_config_manager
        
        # 執行轉換流程
        result = main_conversion_flow(
            xml_file_path="/test/file.xml",
            wiki_token="docABC123",
            table_id="tblXYZ789",
            config_path="invalid_config.yaml"
        )
        
        # 驗證結果
        assert result is False
        mock_logger.error.assert_called()


class TestHandleConversionRequest:
    """轉換請求處理測試"""
    
    @patch('main.InteractiveCLI')
    @patch('main.main_conversion_flow')
    def test_successful_conversion_request(self, mock_conversion_flow, mock_cli_class):
        """測試成功的轉換請求處理"""
        mock_cli = Mock()
        mock_cli.get_file_path_input.return_value = "/test/file.xml"
        mock_cli.get_lark_config_input.return_value = {
            "wiki_token": "docABC123",
            "table_id": "tblXYZ789"
        }
        mock_cli_class.return_value = mock_cli
        
        mock_conversion_flow.return_value = True
        
        # 執行轉換請求處理
        result = handle_conversion_request()
        
        # 驗證結果
        assert result is True
        mock_cli.get_file_path_input.assert_called_once()
        mock_cli.get_lark_config_input.assert_called_once()
        mock_conversion_flow.assert_called_once()
        mock_cli.show_results.assert_called_once()
    
    @patch('main.InteractiveCLI')
    @patch('main.main_conversion_flow')
    def test_conversion_request_with_user_cancel(self, mock_conversion_flow, mock_cli_class):
        """測試用戶取消轉換請求的處理"""
        from cli.interface import ValidationError
        
        mock_cli = Mock()
        mock_cli.get_file_path_input.side_effect = ValidationError("用戶取消操作")
        mock_cli_class.return_value = mock_cli
        
        # 執行轉換請求處理
        result = handle_conversion_request()
        
        # 驗證結果
        assert result is False
        mock_cli.get_file_path_input.assert_called_once()
        mock_conversion_flow.assert_not_called()
    
    @patch('main.InteractiveCLI')
    @patch('main.main_conversion_flow')
    def test_conversion_request_with_processing_error(self, mock_conversion_flow, mock_cli_class):
        """測試轉換處理過程中發生錯誤"""
        mock_cli = Mock()
        mock_cli.get_file_path_input.return_value = "/test/file.xml"
        mock_cli.get_lark_config_input.return_value = {
            "wiki_token": "docABC123",
            "table_id": "tblXYZ789"
        }
        mock_cli_class.return_value = mock_cli
        
        mock_conversion_flow.side_effect = Exception("處理過程中發生錯誤")
        
        # 執行轉換請求處理
        result = handle_conversion_request()
        
        # 驗證結果
        assert result is False
        mock_cli.show_results.assert_called_with(0, 1)  # 0成功，1錯誤


class TestHandleTestConnection:
    """連接測試處理測試"""
    
    @patch('main.InteractiveCLI')
    @patch('main.ConfigManager')
    @patch('main.SimpleLarkClient')
    def test_successful_connection_test(self, mock_client_class, mock_config_class, mock_cli_class):
        """測試成功的連接測試"""
        mock_cli = Mock()
        mock_cli.get_lark_config_input.return_value = {
            "wiki_token": "docABC123",
            "table_id": "tblXYZ789"
        }
        mock_cli_class.return_value = mock_cli
        
        mock_config_manager = Mock()
        mock_config_manager.get_lark_config.return_value = {
            "app_id": "test_app_id",
            "app_secret": "test_app_secret"
        }
        mock_config_class.return_value = mock_config_manager
        
        mock_client = Mock()
        mock_client.set_table_info.return_value = True
        mock_client.test_connection.return_value = True
        mock_client_class.return_value = mock_client
        
        # 執行連接測試
        result = handle_test_connection()
        
        # 驗證結果
        assert result is True
        mock_cli.get_lark_config_input.assert_called_once()
        mock_client.set_table_info.assert_called_once_with("docABC123", "tblXYZ789")
        mock_client.test_connection.assert_called_once()
        mock_cli.show_results.assert_called_with(1, 0)  # 1成功，0錯誤
    
    @patch('main.InteractiveCLI')
    @patch('main.ConfigManager')
    @patch('main.SimpleLarkClient')
    def test_failed_connection_test(self, mock_client_class, mock_config_class, mock_cli_class):
        """測試失敗的連接測試"""
        mock_cli = Mock()
        mock_cli.get_lark_config_input.return_value = {
            "wiki_token": "docABC123",
            "table_id": "tblXYZ789"
        }
        mock_cli_class.return_value = mock_cli
        
        mock_config_manager = Mock()
        mock_config_manager.get_lark_config.return_value = {
            "app_id": "test_app_id",
            "app_secret": "test_app_secret"
        }
        mock_config_class.return_value = mock_config_manager
        
        mock_client = Mock()
        mock_client.set_table_info.return_value = True
        mock_client.test_connection.return_value = False
        mock_client_class.return_value = mock_client
        
        # 執行連接測試
        result = handle_test_connection()
        
        # 驗證結果
        assert result is False
        mock_cli.show_results.assert_called_with(0, 1)  # 0成功，1錯誤


class TestParseCommandLineArgs:
    """命令列參數解析測試"""
    
    def test_parse_no_arguments(self):
        """測試無參數的情況"""
        args = parse_command_line_args([])
        
        assert args.xml_file is None
        assert args.wiki_token is None
        assert args.table_id is None
        assert args.config is None
        assert args.mode == "interactive"
    
    def test_parse_conversion_arguments(self):
        """測試轉換模式的參數"""
        test_args = [
            "--xml-file", "/path/to/test.xml",
            "--wiki-token", "docABC123",
            "--table-id", "tblXYZ789",
            "--config", "/path/to/config.yaml"
        ]
        
        args = parse_command_line_args(test_args)
        
        assert args.xml_file == "/path/to/test.xml"
        assert args.wiki_token == "docABC123"
        assert args.table_id == "tblXYZ789"
        assert args.config == "/path/to/config.yaml"
        assert args.mode == "convert"
    
    def test_parse_test_mode_arguments(self):
        """測試連接測試模式的參數"""
        test_args = [
            "--mode", "test",
            "--wiki-token", "docABC123",
            "--table-id", "tblXYZ789"
        ]
        
        args = parse_command_line_args(test_args)
        
        assert args.wiki_token == "docABC123"
        assert args.table_id == "tblXYZ789"
        assert args.mode == "test"
    
    def test_parse_interactive_mode(self):
        """測試互動模式參數"""
        test_args = ["--mode", "interactive"]
        
        args = parse_command_line_args(test_args)
        
        assert args.mode == "interactive"


class TestSetupApplicationLogging:
    """應用程式日誌設定測試"""
    
    @patch('main.ConfigManager')
    @patch('main.setup_logger')
    def test_setup_logging_with_config(self, mock_setup_logger, mock_config_class):
        """測試使用配置檔案設定日誌"""
        mock_config_manager = Mock()
        mock_config_class.return_value = mock_config_manager
        
        mock_logger = Mock()
        mock_setup_logger.return_value = mock_logger
        
        # 執行日誌設定
        result = setup_application_logging("test_config.yaml")
        
        # 驗證結果
        assert result == mock_logger
        mock_config_manager.load_config.assert_called_once_with("test_config.yaml")
        mock_setup_logger.assert_called_once_with("main", config_path="test_config.yaml")
    
    @patch('main.ConfigManager')
    @patch('main.setup_logger')
    def test_setup_logging_without_config(self, mock_setup_logger, mock_config_class):
        """測試不使用配置檔案設定日誌"""
        mock_logger = Mock()
        mock_setup_logger.return_value = mock_logger
        
        # 執行日誌設定
        result = setup_application_logging()
        
        # 驗證結果
        assert result == mock_logger
        mock_config_class.assert_not_called()
        mock_setup_logger.assert_called_once_with("main", config_path=None)
    
    @patch('main.ConfigManager')
    @patch('main.setup_logger')
    def test_setup_logging_with_config_error(self, mock_setup_logger, mock_config_class):
        """測試配置載入錯誤時的日誌設定"""
        mock_config_manager = Mock()
        mock_config_manager.load_config.side_effect = Exception("配置載入失敗")
        mock_config_class.return_value = mock_config_manager
        
        mock_logger = Mock()
        mock_setup_logger.return_value = mock_logger
        
        # 執行日誌設定
        result = setup_application_logging("invalid_config.yaml")
        
        # 驗證結果
        assert result == mock_logger
        mock_setup_logger.assert_called_once_with("main", config_path=None)


class TestMainFunction:
    """主函數測試"""
    
    @patch('main.handle_conversion_request')
    @patch('main.InteractiveCLI')
    @patch('main.setup_application_logging')
    def test_main_interactive_mode_convert(self, mock_setup_logging, mock_cli_class, mock_handle_conversion):
        """測試互動模式的轉換選擇"""
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        mock_cli = Mock()
        mock_cli.show_main_menu.return_value = "convert"
        mock_cli_class.return_value = mock_cli
        
        mock_handle_conversion.return_value = True
        
        # 執行主函數
        with patch('sys.argv', ['main.py']):
            result = main()
        
        # 驗證結果
        assert result == 0
        mock_cli.show_main_menu.assert_called_once()
        mock_handle_conversion.assert_called_once()
    
    @patch('main.handle_test_connection')
    @patch('main.InteractiveCLI')
    @patch('main.setup_application_logging')
    def test_main_interactive_mode_test(self, mock_setup_logging, mock_cli_class, mock_handle_test):
        """測試互動模式的連接測試選擇"""
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        mock_cli = Mock()
        mock_cli.show_main_menu.return_value = "test"
        mock_cli_class.return_value = mock_cli
        
        mock_handle_test.return_value = True
        
        # 執行主函數
        with patch('sys.argv', ['main.py']):
            result = main()
        
        # 驗證結果
        assert result == 0
        mock_cli.show_main_menu.assert_called_once()
        mock_handle_test.assert_called_once()
    
    @patch('main.InteractiveCLI')
    @patch('main.setup_application_logging')
    def test_main_interactive_mode_quit(self, mock_setup_logging, mock_cli_class):
        """測試互動模式的退出選擇"""
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        mock_cli = Mock()
        mock_cli.show_main_menu.return_value = "quit"
        mock_cli_class.return_value = mock_cli
        
        # 執行主函數
        with patch('sys.argv', ['main.py']):
            result = main()
        
        # 驗證結果
        assert result == 0
        mock_cli.show_main_menu.assert_called_once()
    
    @patch('main.main_conversion_flow')
    @patch('main.setup_application_logging')
    def test_main_convert_mode(self, mock_setup_logging, mock_conversion_flow):
        """測試命令列轉換模式"""
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        mock_conversion_flow.return_value = True
        
        test_args = [
            'main.py',
            '--xml-file', '/test/file.xml',
            '--wiki-token', 'docABC123',
            '--table-id', 'tblXYZ789'
        ]
        
        # 執行主函數
        with patch('sys.argv', test_args):
            result = main()
        
        # 驗證結果
        assert result == 0
        mock_conversion_flow.assert_called_once_with(
            xml_file_path='/test/file.xml',
            wiki_token='docABC123',
            table_id='tblXYZ789',
            config_path=None
        )
    
    @patch('main.handle_test_connection')
    @patch('main.setup_application_logging')
    def test_main_test_mode(self, mock_setup_logging, mock_handle_test):
        """測試命令列連接測試模式"""
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        mock_handle_test.return_value = True
        
        test_args = [
            'main.py',
            '--mode', 'test',
            '--wiki-token', 'docABC123',
            '--table-id', 'tblXYZ789'
        ]
        
        # 執行主函數
        with patch('sys.argv', test_args):
            result = main()
        
        # 驗證結果
        assert result == 0
        mock_handle_test.assert_called_once()
    
    @patch('main.setup_application_logging')
    def test_main_with_exception(self, mock_setup_logging):
        """測試主函數異常處理"""
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        # 模擬異常
        with patch('main.parse_command_line_args', side_effect=Exception("測試異常")):
            with patch('sys.argv', ['main.py']):
                result = main()
        
        # 驗證結果
        assert result == 1
        mock_logger.error.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])