"""
CLI 介面整合測試

測試 CLI 介面與其他模組的整合，包括：
- 完整的使用者互動流程
- CLI 與檔案處理的整合
- CLI 與 Lark 設定的整合
- 端到端的轉換流程模擬
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, mock_open
from io import StringIO

# 加入 src 目錄到 Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from cli.interface import InteractiveCLI, ValidationError


class TestCLIIntegration:
    """CLI 介面整合測試"""
    
    def setup_method(self):
        """每個測試方法前的設定"""
        self.cli = InteractiveCLI()
        
        # 測試檔案路徑
        self.test_xml_path = os.path.join(
            os.path.dirname(__file__), '..', 'fixtures', 'xml', 'sample_basic.xml'
        )
    
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_complete_conversion_workflow_simulation(self, mock_stdout, mock_input):
        """測試完整的轉換工作流程模擬"""
        # 模擬使用者選擇轉換選項
        mock_input.side_effect = [
            '1',  # 選擇轉換
        ]
        
        # 測試主選單
        choice = self.cli.show_main_menu()
        assert choice == "convert"
        
        # 驗證選單顯示
        output = mock_stdout.getvalue()
        assert "TestRail 到 Lark 轉換器" in output
        assert "1. 開始轉換" in output
    
    @patch('builtins.input')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('sys.stdout', new_callable=StringIO)
    def test_file_input_integration_workflow(self, mock_stdout, mock_getsize, mock_exists, mock_input):
        """測試檔案輸入整合工作流程"""
        # 模擬使用者輸入檔案路徑的完整流程
        mock_input.side_effect = [
            "/invalid/path.txt",       # 無效副檔名
            "/nonexistent/file.xml",   # 檔案不存在
            "/path/to/large.xml",      # 檔案過大
            "/path/to/valid.xml"       # 有效檔案
        ]
        
        # 模擬檔案系統狀態
        mock_exists.side_effect = [
            True,   # 第一個檔案存在但副檔名錯誤
            False,  # 第二個檔案不存在
            True,   # 第三個檔案存在但過大
            True    # 第四個檔案有效
        ]
        
        mock_getsize.side_effect = [
            200 * 1024 * 1024,        # 第三個檔案過大（前兩個檔案不會調用 getsize）
            1024                      # 第四個檔案正常
        ]
        
        result = self.cli.get_file_path_input()
        
        # 檢查最終結果
        assert result == "/path/to/valid.xml"
        
        # 檢查錯誤訊息
        output = mock_stdout.getvalue()
        assert "必須是 .xml 檔案" in output
        assert "檔案不存在" in output
        assert "檔案過大" in output
        assert "檔案驗證成功" in output
    
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_lark_config_integration_workflow(self, mock_stdout, mock_input):
        """測試 Lark 設定整合工作流程"""
        # 模擬使用者輸入 Lark 設定的完整流程
        mock_input.side_effect = [
            "",                             # 空 Wiki Token
            "invalid_wiki_token",           # 無效 Wiki Token
            "doccnG7ZuSaeQhN9BItJnSobGUd",  # 有效 Wiki Token
            "",                             # 空 Table ID
            "invalid_table_id",             # 無效 Table ID
            "tblmVw4gSqKaBGdB"              # 有效 Table ID
        ]
        
        result = self.cli.get_lark_config_input()
        
        # 檢查最終結果
        expected = {
            "wiki_token": "doccnG7ZuSaeQhN9BItJnSobGUd",
            "table_id": "tblmVw4gSqKaBGdB"
        }
        assert result == expected
        
        # 檢查輸出訊息
        output = mock_stdout.getvalue()
        assert "請輸入 Lark 設定資訊" in output
        assert "Wiki Token 不能為空" in output
        assert "Wiki Token 格式錯誤" in output
        assert "Table ID 不能為空" in output
        assert "Table ID 格式錯誤" in output
        assert "Lark 設定資訊輸入完成" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_progress_tracking_integration(self, mock_stdout):
        """測試進度追蹤整合"""
        total_items = 100
        
        # 模擬處理進度
        progress_points = [0, 25, 50, 75, 100]
        
        for current in progress_points:
            # 清除之前的輸出
            mock_stdout.seek(0)
            mock_stdout.truncate(0)
            
            self.cli.show_progress(current, total_items)
            output = mock_stdout.getvalue()
            
            # 檢查進度顯示
            expected_percent = int((current / total_items) * 100) if total_items > 0 else 0
            assert f"{current}/{total_items}" in output
            assert f"({expected_percent}%)" in output
            
            # 檢查進度條存在
            assert "█" in output or "░" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_results_display_integration(self, mock_stdout):
        """測試結果顯示整合"""
        # 測試不同的結果場景
        test_scenarios = [
            (100, 0, "所有資料都已成功處理"),      # 完全成功
            (80, 20, "部分資料處理成功"),          # 部分成功
            (0, 100, "沒有資料被成功處理")         # 完全失敗
        ]
        
        for success, error, expected_message in test_scenarios:
            # 清除之前的輸出
            mock_stdout.seek(0)
            mock_stdout.truncate(0)
            
            self.cli.show_results(success, error)
            output = mock_stdout.getvalue()
            
            # 檢查結果顯示
            assert "處理完成" in output
            assert f"成功: {success}" in output
            assert f"錯誤: {error}" in output
            
            total = success + error
            if total > 0:
                success_rate = int((success / total) * 100)
                assert f"成功率: {success_rate}%" in output
            
            assert expected_message in output
    
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_user_cancellation_handling(self, mock_stdout, mock_input):
        """測試使用者取消操作的處理"""
        # 模擬使用者按 Ctrl+C 取消操作
        mock_input.side_effect = KeyboardInterrupt()
        
        # 測試檔案路徑輸入取消
        with pytest.raises(ValidationError) as exc_info:
            self.cli.get_file_path_input()
        
        assert "使用者取消操作" in str(exc_info.value)
        
        # 檢查輸出訊息
        output = mock_stdout.getvalue()
        assert "已取消檔案選擇" in output
    
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)  
    def test_lark_config_cancellation_handling(self, mock_stdout, mock_input):
        """測試 Lark 設定輸入取消處理"""
        # 模擬使用者在 Wiki Token 輸入時取消
        mock_input.side_effect = KeyboardInterrupt()
        
        with pytest.raises(ValidationError) as exc_info:
            self.cli.get_lark_config_input()
        
        assert "使用者取消操作" in str(exc_info.value)
        
        # 檢查輸出訊息
        output = mock_stdout.getvalue()
        assert "已取消設定輸入" in output
    
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_menu_navigation_flow(self, mock_stdout, mock_input):
        """測試選單導航流程"""
        # 測試各種選單選項的流程
        menu_choices = [
            ('1', 'convert'),
            ('2', 'test'), 
            ('3', 'quit')
        ]
        
        for choice_input, expected_result in menu_choices:
            # 清除之前的輸出
            mock_stdout.seek(0)
            mock_stdout.truncate(0)
            
            mock_input.return_value = choice_input
            result = self.cli.show_main_menu()
            
            assert result == expected_result
            
            # 檢查選單顯示
            output = mock_stdout.getvalue()
            assert "TestRail 到 Lark 轉換器" in output
            assert "1. 開始轉換" in output
            assert "2. 測試連接" in output
            assert "3. 退出程式" in output
    
    def test_token_validation_with_real_format_examples(self):
        """測試使用真實格式範例的 Token 驗證"""
        # 真實的 Lark Token 格式範例
        valid_wiki_tokens = [
            "doccnG7ZuSaeQhN9BItJnSobGUd",
            "docAbCdEfGhIjKlMnOpQrStUvWxYz",
            "doc1234567890abcdefghijklmnop"
        ]
        
        valid_table_ids = [
            "tblmVw4gSqKaBGdB",
            "tblAbCdEfGhIjKlMn",
            "tbl1234567890abcd"
        ]
        
        # 測試有效的 Token
        for token in valid_wiki_tokens:
            assert self.cli._validate_wiki_token(token), f"Should validate: {token}"
        
        for table_id in valid_table_ids:
            assert self.cli._validate_table_id(table_id), f"Should validate: {table_id}"
        
        # 測試無效的 Token
        invalid_tokens = [
            "doc123",                    # 太短
            "abc" + "a" * 24,           # 不以 doc 開頭
            "doc" + "a" * 50,           # 太長
            "doc_invalid_char_here"      # 包含無效字符
        ]
        
        for token in invalid_tokens:
            assert not self.cli._validate_wiki_token(token), f"Should not validate: {token}"
    
    @patch('os.path.exists')
    @patch('os.path.getsize')
    def test_file_validation_edge_cases(self, mock_getsize, mock_exists):
        """測試檔案驗證的邊界情況"""
        mock_exists.return_value = True
        
        # 測試檔案大小邊界
        edge_sizes = [
            (100 * 1024 * 1024 - 1, True),   # 剛好小於限制
            (100 * 1024 * 1024, True),       # 剛好等於限制
            (100 * 1024 * 1024 + 1, False),  # 剛好超過限制
        ]
        
        for file_size, should_pass in edge_sizes:
            mock_getsize.return_value = file_size
            
            with patch('builtins.input', return_value="test.xml"):
                with patch('sys.stdout', new_callable=StringIO):
                    if should_pass:
                        result = self.cli.get_file_path_input()
                        assert result is not None
                    else:
                        # 模擬使用者重新輸入有效檔案
                        with patch('builtins.input', side_effect=["test.xml", "valid.xml"]):
                            with patch('os.path.getsize', side_effect=[file_size, 1024]):
                                result = self.cli.get_file_path_input()
                                assert result is not None
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_progress_bar_mathematical_accuracy(self, mock_stdout):
        """測試進度條的數學準確性"""
        test_cases = [
            (0, 100, 0),      # 0%
            (1, 100, 1),      # 1%
            (33, 100, 33),    # 33%
            (50, 100, 50),    # 50%
            (99, 100, 99),    # 99%
            (100, 100, 100),  # 100%
            (150, 100, 100),  # 超過 100%（應該顯示為 100%）
        ]
        
        for current, total, expected_percent in test_cases:
            # 清除輸出
            mock_stdout.seek(0)
            mock_stdout.truncate(0)
            
            self.cli.show_progress(current, total)
            output = mock_stdout.getvalue()
            
            # 檢查百分比計算準確性
            assert f"({min(expected_percent, 100)}%)" in output
            assert f"{current}/{total}" in output
    
    def test_cli_error_recovery_mechanisms(self):
        """測試 CLI 的錯誤恢復機制"""
        # 測試驗證函數的魯棒性
        edge_inputs = [None, "", " ", "\t", "\n", "   \t\n   "]
        
        for invalid_input in edge_inputs:
            # Wiki Token 驗證應該優雅地處理所有無效輸入
            assert not self.cli._validate_wiki_token(invalid_input)
            assert not self.cli._validate_table_id(invalid_input)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])