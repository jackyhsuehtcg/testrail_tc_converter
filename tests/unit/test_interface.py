"""
CLI 介面模組測試

測試 InteractiveCLI 類別的各項功能，包括：
- 選單顯示功能
- 使用者輸入處理
- 檔案路徑驗證
- 進度顯示功能
- 結果展示功能
- Lark 設定輸入處理
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, mock_open
from io import StringIO

# 加入 src 目錄到 Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from cli.interface import InteractiveCLI, ValidationError


class TestInteractiveCLI:
    """InteractiveCLI 類別測試"""
    
    def setup_method(self):
        """每個測試方法前的設定"""
        self.cli = InteractiveCLI()
        
        # 創建測試用的臨時檔案路徑
        self.test_xml_path = os.path.join(
            os.path.dirname(__file__), '..', 'fixtures', 'xml', 'sample_basic.xml'
        )
    
    def test_init(self):
        """測試初始化"""
        cli = InteractiveCLI()
        assert cli is not None
        assert hasattr(cli, 'show_main_menu')
        assert hasattr(cli, 'get_file_path_input')
        assert hasattr(cli, 'get_lark_config_input')
        assert hasattr(cli, 'show_progress')
        assert hasattr(cli, 'show_results')
    
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_show_main_menu_convert_option(self, mock_stdout, mock_input):
        """測試主選單顯示和轉換選項選擇"""
        mock_input.return_value = '1'
        
        result = self.cli.show_main_menu()
        
        # 檢查回傳值
        assert result == "convert"
        
        # 檢查選單輸出
        output = mock_stdout.getvalue()
        assert "TestRail 到 Lark 轉換器" in output
        assert "1. 開始轉換" in output
        assert "2. 測試連接" in output
        assert "3. 退出程式" in output
    
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_show_main_menu_test_option(self, mock_stdout, mock_input):
        """測試主選單測試連接選項"""
        mock_input.return_value = '2'
        
        result = self.cli.show_main_menu()
        assert result == "test"
    
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_show_main_menu_quit_option(self, mock_stdout, mock_input):
        """測試主選單退出選項"""
        mock_input.return_value = '3'
        
        result = self.cli.show_main_menu()
        assert result == "quit"
    
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_show_main_menu_invalid_option(self, mock_stdout, mock_input):
        """測試主選單無效選項處理"""
        # 模擬使用者先輸入無效選項，再輸入有效選項
        mock_input.side_effect = ['4', 'invalid', '1']
        
        result = self.cli.show_main_menu()
        assert result == "convert"
        
        # 檢查錯誤訊息
        output = mock_stdout.getvalue()
        assert "無效的選項" in output
    
    @patch('builtins.input')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    def test_get_file_path_input_valid_file(self, mock_getsize, mock_exists, mock_input):
        """測試有效檔案路徑輸入"""
        test_path = "/path/to/test.xml"
        mock_input.return_value = test_path
        mock_exists.return_value = True
        mock_getsize.return_value = 1024 * 1024  # 1MB
        
        result = self.cli.get_file_path_input()
        assert result == test_path
    
    @patch('builtins.input')
    @patch('os.path.exists')
    @patch('sys.stdout', new_callable=StringIO)
    def test_get_file_path_input_file_not_exists(self, mock_stdout, mock_exists, mock_input):
        """測試檔案不存在的情況"""
        mock_input.side_effect = ["/non/existent/file.xml", self.test_xml_path]
        mock_exists.side_effect = [False, True]
        
        with patch('os.path.getsize', return_value=1024):
            result = self.cli.get_file_path_input()
        
        # 檢查錯誤訊息
        output = mock_stdout.getvalue()
        assert "檔案不存在" in output
    
    @patch('builtins.input')
    @patch('os.path.exists')
    @patch('sys.stdout', new_callable=StringIO)
    def test_get_file_path_input_invalid_extension(self, mock_stdout, mock_exists, mock_input):
        """測試無效檔案副檔名"""
        mock_input.side_effect = ["/path/to/test.txt", self.test_xml_path]
        mock_exists.side_effect = [True, True]
        
        with patch('os.path.getsize', return_value=1024):
            result = self.cli.get_file_path_input()
        
        # 檢查錯誤訊息
        output = mock_stdout.getvalue()
        assert "必須是 .xml 檔案" in output
    
    @patch('builtins.input')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('sys.stdout', new_callable=StringIO)
    def test_get_file_path_input_file_too_large(self, mock_stdout, mock_getsize, mock_exists, mock_input):
        """測試檔案過大的情況"""
        large_size = 200 * 1024 * 1024  # 200MB
        mock_input.side_effect = ["/path/to/large.xml", self.test_xml_path]
        mock_exists.return_value = True
        mock_getsize.side_effect = [large_size, 1024]
        
        result = self.cli.get_file_path_input()
        
        # 檢查錯誤訊息
        output = mock_stdout.getvalue()
        assert "檔案過大" in output
    
    @patch('builtins.input')
    def test_get_lark_config_input_valid(self, mock_input):
        """測試有效的 Lark 設定輸入"""
        mock_input.side_effect = [
            "doccnG7ZuSaeQhN9BItJnSobGUd",  # Wiki Token
            "tblmVw4gSqKaBGdB"             # Table ID
        ]
        
        result = self.cli.get_lark_config_input()
        
        expected = {
            "wiki_token": "doccnG7ZuSaeQhN9BItJnSobGUd",
            "table_id": "tblmVw4gSqKaBGdB"
        }
        assert result == expected
    
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_get_lark_config_input_invalid_wiki_token(self, mock_stdout, mock_input):
        """測試無效的 Wiki Token"""
        mock_input.side_effect = [
            "invalid_token",               # 無效的 Wiki Token
            "doccnG7ZuSaeQhN9BItJnSobGUd", # 有效的 Wiki Token
            "tblmVw4gSqKaBGdB"             # Table ID
        ]
        
        result = self.cli.get_lark_config_input()
        
        # 檢查錯誤訊息
        output = mock_stdout.getvalue()
        assert "Wiki Token 格式錯誤" in output
        
        # 檢查最終結果
        assert result["wiki_token"] == "doccnG7ZuSaeQhN9BItJnSobGUd"
    
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_get_lark_config_input_invalid_table_id(self, mock_stdout, mock_input):
        """測試無效的 Table ID"""
        mock_input.side_effect = [
            "doccnG7ZuSaeQhN9BItJnSobGUd", # Wiki Token
            "invalid_id",                  # 無效的 Table ID
            "tblmVw4gSqKaBGdB"             # 有效的 Table ID
        ]
        
        result = self.cli.get_lark_config_input()
        
        # 檢查錯誤訊息
        output = mock_stdout.getvalue()
        assert "Table ID 格式錯誤" in output
        
        # 檢查最終結果
        assert result["table_id"] == "tblmVw4gSqKaBGdB"
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_show_progress_initial(self, mock_stdout):
        """測試進度顯示 - 初始狀態"""
        self.cli.show_progress(0, 100)
        
        output = mock_stdout.getvalue()
        assert "處理進度" in output
        assert "0/100" in output
        assert "0%" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_show_progress_partial(self, mock_stdout):
        """測試進度顯示 - 部分完成"""
        self.cli.show_progress(50, 100)
        
        output = mock_stdout.getvalue()
        assert "50/100" in output
        assert "50%" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_show_progress_complete(self, mock_stdout):
        """測試進度顯示 - 完成狀態"""
        self.cli.show_progress(100, 100)
        
        output = mock_stdout.getvalue()
        assert "100/100" in output
        assert "100%" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_show_progress_edge_cases(self, mock_stdout):
        """測試進度顯示 - 邊界情況"""
        # 測試總數為 0 的情況
        self.cli.show_progress(0, 0)
        output = mock_stdout.getvalue()
        assert "0/0" in output
        
        # 清除輸出
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        
        # 測試當前數大於總數的情況
        self.cli.show_progress(150, 100)
        output = mock_stdout.getvalue()
        assert "150/100" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_show_results_success_only(self, mock_stdout):
        """測試結果顯示 - 只有成功"""
        self.cli.show_results(100, 0)
        
        output = mock_stdout.getvalue()
        assert "處理完成" in output
        assert "成功: 100" in output
        assert "錯誤: 0" in output
        assert "成功率: 100%" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_show_results_with_errors(self, mock_stdout):
        """測試結果顯示 - 有錯誤"""
        self.cli.show_results(80, 20)
        
        output = mock_stdout.getvalue()
        assert "成功: 80" in output
        assert "錯誤: 20" in output
        assert "成功率: 80%" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_show_results_all_errors(self, mock_stdout):
        """測試結果顯示 - 全部錯誤"""
        self.cli.show_results(0, 50)
        
        output = mock_stdout.getvalue()
        assert "成功: 0" in output
        assert "錯誤: 50" in output
        assert "成功率: 0%" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_show_results_no_data(self, mock_stdout):
        """測試結果顯示 - 無資料"""
        self.cli.show_results(0, 0)
        
        output = mock_stdout.getvalue()
        assert "成功: 0" in output
        assert "錯誤: 0" in output
    
    def test_validate_wiki_token_valid(self):
        """測試 Wiki Token 驗證 - 有效格式"""
        valid_tokens = [
            "doccnG7ZuSaeQhN9BItJnSobGUd",
            "docABCDEFGHIJKLMNOPQRSTUVWXYZ",
            "doc" + "a" * 24  # 27 字符總長度
        ]
        
        for token in valid_tokens:
            assert self.cli._validate_wiki_token(token), f"Token should be valid: {token}"
    
    def test_validate_wiki_token_invalid(self):
        """測試 Wiki Token 驗證 - 無效格式"""
        invalid_tokens = [
            "",                    # 空字串
            "doc",                 # 太短
            "abc123",              # 不以 doc 開頭
            "doc" + "a" * 50,      # 太長
            "doc_invalid_char",    # 包含無效字符
            "doc123456789012345678901234567890"  # 太長
        ]
        
        for token in invalid_tokens:
            assert not self.cli._validate_wiki_token(token), f"Token should be invalid: {token}"
    
    def test_validate_table_id_valid(self):
        """測試 Table ID 驗證 - 有效格式"""
        valid_ids = [
            "tblmVw4gSqKaBGdB",
            "tblABCDEFGHIJKLMN",
            "tbl" + "a" * 13  # 16 字符總長度
        ]
        
        for table_id in valid_ids:
            assert self.cli._validate_table_id(table_id), f"Table ID should be valid: {table_id}"
    
    def test_validate_table_id_invalid(self):
        """測試 Table ID 驗證 - 無效格式"""
        invalid_ids = [
            "",                  # 空字串
            "tbl",               # 太短
            "abc123",            # 不以 tbl 開頭
            "tbl" + "a" * 50,    # 太長
            "tbl_invalid_char",  # 包含無效字符
        ]
        
        for table_id in invalid_ids:
            assert not self.cli._validate_table_id(table_id), f"Table ID should be invalid: {table_id}"
    
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_input_validation_retry_mechanism(self, mock_stdout, mock_input):
        """測試輸入驗證的重試機制"""
        # 模擬使用者多次輸入錯誤，最後輸入正確
        mock_input.side_effect = [
            "",                              # 空 Wiki Token
            "invalid",                       # 無效 Wiki Token  
            "doccnG7ZuSaeQhN9BItJnSobGUd",   # 有效 Wiki Token
            "",                              # 空 Table ID
            "invalid",                       # 無效 Table ID
            "tblmVw4gSqKaBGdB"               # 有效 Table ID
        ]
        
        result = self.cli.get_lark_config_input()
        
        # 檢查最終結果正確
        assert result["wiki_token"] == "doccnG7ZuSaeQhN9BItJnSobGUd"
        assert result["table_id"] == "tblmVw4gSqKaBGdB"
        
        # 檢查錯誤訊息出現
        output = mock_stdout.getvalue()
        assert "Wiki Token 不能為空" in output
        assert "Wiki Token 格式錯誤" in output
        assert "Table ID 不能為空" in output
        assert "Table ID 格式錯誤" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_progress_bar_visual_representation(self, mock_stdout):
        """測試進度條的視覺表示"""
        # 測試不同進度的進度條顯示
        test_cases = [
            (0, 100, 0),      # 0%
            (25, 100, 25),    # 25%
            (50, 100, 50),    # 50%
            (75, 100, 75),    # 75%
            (100, 100, 100),  # 100%
        ]
        
        for current, total, expected_percent in test_cases:
            # 清除之前的輸出
            mock_stdout.truncate(0)
            mock_stdout.seek(0)
            
            self.cli.show_progress(current, total)
            output = mock_stdout.getvalue()
            
            # 檢查百分比顯示
            assert f"{expected_percent}%" in output
            
            # 檢查進度條符號
            if expected_percent > 0:
                assert "█" in output or "■" in output or "#" in output
    
    def test_error_handling_in_file_validation(self):
        """測試檔案驗證中的錯誤處理"""
        # 模擬第一次 OSError，第二次成功
        with patch('os.path.exists', side_effect=[OSError("Permission denied"), True]):
            with patch('builtins.input', side_effect=["/path/to/error.xml", self.test_xml_path]):
                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    with patch('os.path.getsize', return_value=1024):
                        result = self.cli.get_file_path_input()
                        
                        # 檢查錯誤處理
                        output = mock_stdout.getvalue()
                        assert "檔案存取錯誤" in output
                        
                        # 最終應該成功
                        assert result is not None


class TestValidationError:
    """ValidationError 異常測試"""
    
    def test_validation_error_creation(self):
        """測試 ValidationError 異常創建"""
        error_msg = "測試驗證錯誤"
        
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError(error_msg)
        
        assert str(exc_info.value) == error_msg
    
    def test_validation_error_inheritance(self):
        """測試 ValidationError 繼承關係"""
        error = ValidationError("測試錯誤")
        assert isinstance(error, Exception)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])