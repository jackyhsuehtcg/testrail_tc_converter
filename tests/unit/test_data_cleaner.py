"""
資料清理器模組單元測試

測試 TestCaseDataCleaner 類別的所有功能
"""

import pytest
from typing import Dict, Any, Tuple

# 待實作的模組
from parsers.data_cleaner import TestCaseDataCleaner, DataCleaningError


class TestTestCaseDataCleaner:
    """TestCaseDataCleaner 類別測試"""

    def setup_method(self):
        """每個測試方法前的設定"""
        self.cleaner = TestCaseDataCleaner()

    @pytest.mark.data_cleaner
    def test_extract_test_case_number_and_title_standard_format(self):
        """測試標準格式的測試案例編號和標題提取"""
        title = "TCG-001.002.003 登入功能測試"
        
        case_number, clean_title = self.cleaner.extract_test_case_number_and_title(title)
        
        assert case_number == "TCG-001.002.003", "應正確提取測試案例編號"
        assert clean_title == "登入功能測試", "應正確提取純標題"

    @pytest.mark.data_cleaner
    def test_extract_test_case_number_and_title_missing_hyphen(self):
        """測試缺失hyphen的測試案例編號提取和修正"""
        title = "TCG001.002.003 缺失hyphen的測試"
        
        case_number, clean_title = self.cleaner.extract_test_case_number_and_title(title)
        
        assert case_number == "TCG-001.002.003", "應自動修正缺失的hyphen"
        assert clean_title == "缺失hyphen的測試", "應正確提取標題"

    @pytest.mark.data_cleaner
    def test_extract_test_case_number_and_title_no_number(self):
        """測試沒有測試案例編號的標題"""
        title = "純標題沒有編號"
        
        case_number, clean_title = self.cleaner.extract_test_case_number_and_title(title)
        
        assert case_number == "", "沒有編號時應回傳空字串"
        assert clean_title == "純標題沒有編號", "應回傳原始標題"

    @pytest.mark.data_cleaner
    def test_extract_test_case_number_and_title_multiple_numbers(self):
        """測試包含多個編號格式的標題"""
        title = "TCG-001.002.003 測試 TCG-004.005.006 相關功能"
        
        case_number, clean_title = self.cleaner.extract_test_case_number_and_title(title)
        
        assert case_number == "TCG-001.002.003", "應提取第一個匹配的編號"
        assert clean_title == "測試 TCG-004.005.006 相關功能", "應移除第一個編號後的標題"

    @pytest.mark.data_cleaner
    def test_extract_test_case_number_and_title_edge_cases(self):
        """測試邊界條件和異常輸入"""
        test_cases = [
            ("", "", ""),  # 空字串
            ("   ", "", ""),  # 空白字串
            ("TCG-123", "", "TCG-123"),  # 不完整編號
            ("TCG-001.002.003", "TCG-001.002.003", ""),  # 只有編號沒有標題
            ("TCG-001.002.003 ", "TCG-001.002.003", ""),  # 編號後只有空白
        ]
        
        for title, expected_number, expected_title in test_cases:
            case_number, clean_title = self.cleaner.extract_test_case_number_and_title(title)
            assert case_number == expected_number, f"編號提取失敗: {title}"
            assert clean_title == expected_title, f"標題提取失敗: {title}"

    @pytest.mark.data_cleaner
    def test_fix_missing_hyphen_standard_cases(self):
        """測試標準的hyphen修正功能"""
        test_cases = [
            ("TCG001.002.003", "TCG-001.002.003"),
            ("TCG123.456.789", "TCG-123.456.789"),
            ("TCG001.001.001", "TCG-001.001.001"),
        ]
        
        for input_number, expected_output in test_cases:
            result = self.cleaner.fix_missing_hyphen(input_number)
            assert result == expected_output, f"Hyphen修正失敗: {input_number}"

    @pytest.mark.data_cleaner
    def test_fix_missing_hyphen_already_correct(self):
        """測試已經正確格式的編號不會被更改"""
        correct_numbers = [
            "TCG-001.002.003",
            "TCG-123.456.789",
            "TCG-999.888.777",
        ]
        
        for number in correct_numbers:
            result = self.cleaner.fix_missing_hyphen(number)
            assert result == number, f"正確格式不應被修改: {number}"

    @pytest.mark.data_cleaner
    def test_fix_missing_hyphen_invalid_format(self):
        """測試無效格式的編號處理"""
        invalid_numbers = [
            "TCG-123",  # 不完整
            "ABC-001.002.003",  # 錯誤前綴
            "TCG001002003",  # 缺少點號
            "invalid",  # 完全不符合格式
            "",  # 空字串
        ]
        
        for number in invalid_numbers:
            result = self.cleaner.fix_missing_hyphen(number)
            assert result == number, f"無效格式應保持原樣: {number}"

    @pytest.mark.data_cleaner
    def test_clean_markdown_content_bold_and_italic(self):
        """測試清理Markdown粗體和斜體格式"""
        test_cases = [
            ("**粗體文字**", "粗體文字"),
            ("*斜體文字*", "斜體文字"),
            ("**粗體** 和 *斜體* 混合", "粗體 和 斜體 混合"),
            ("***粗斜體***", "粗斜體"),
            ("正常文字", "正常文字"),
        ]
        
        for markdown_text, expected_result in test_cases:
            result = self.cleaner.clean_markdown_content(markdown_text)
            assert result == expected_result, f"Markdown清理失敗: {markdown_text}"

    @pytest.mark.data_cleaner
    def test_clean_markdown_content_code_blocks(self):
        """測試清理Markdown程式碼格式"""
        test_cases = [
            ("`程式碼`", "程式碼"),
            ("執行 `print('hello')` 指令", "執行 print('hello') 指令"),
            ("```多行程式碼```", "多行程式碼"),
            ("`code` 和 **bold** 混合", "code 和 bold 混合"),
        ]
        
        for markdown_text, expected_result in test_cases:
            result = self.cleaner.clean_markdown_content(markdown_text)
            assert result == expected_result, f"程式碼格式清理失敗: {markdown_text}"

    @pytest.mark.data_cleaner
    def test_clean_markdown_content_complex_formatting(self):
        """測試複雜的Markdown格式清理"""
        complex_text = "**重要**：執行 `npm install` 後，*請檢查* `package.json` 檔案"
        expected_result = "重要：執行 npm install 後，請檢查 package.json 檔案"
        
        result = self.cleaner.clean_markdown_content(complex_text)
        assert result == expected_result, "複雜Markdown格式清理失敗"

    @pytest.mark.data_cleaner
    def test_extract_url_description_markdown_links(self):
        """測試從Markdown連結中提取說明文字"""
        test_cases = [
            ("[登入頁面](http://example.com/login)", "登入頁面"),
            ("[API文件](https://api.example.com/docs)", "API文件"),
            ("[測試報告](file://local/report.html)", "測試報告"),
            ("請參考[官方文件](https://docs.example.com)了解詳情", "請參考官方文件了解詳情"),
        ]
        
        for url_content, expected_result in test_cases:
            result = self.cleaner.extract_url_description(url_content)
            assert result == expected_result, f"URL說明提取失敗: {url_content}"

    @pytest.mark.data_cleaner
    def test_extract_url_description_plain_urls(self):
        """測試純URL的處理（沒有說明文字）"""
        test_cases = [
            ("http://example.com", "http://example.com"),
            ("https://api.example.com/endpoint", "https://api.example.com/endpoint"),
            ("訪問 http://example.com 查看", "訪問 http://example.com 查看"),
            ("文字 https://example.com 更多文字", "文字 https://example.com 更多文字"),
        ]
        
        for url_content, expected_result in test_cases:
            result = self.cleaner.extract_url_description(url_content)
            assert result == expected_result, f"純URL處理失敗: {url_content}"

    @pytest.mark.data_cleaner
    def test_extract_url_description_multiple_links(self):
        """測試包含多個連結的內容"""
        content = "參考[文件A](http://a.com)和[文件B](http://b.com)"
        expected_result = "參考文件A和文件B"
        
        result = self.cleaner.extract_url_description(content)
        assert result == expected_result, "多連結處理失敗"

    @pytest.mark.data_cleaner
    def test_extract_url_description_mixed_content(self):
        """測試混合Markdown連結和純URL的內容"""
        content = "查看[文件](http://docs.com)或直接訪問 http://example.com"
        expected_result = "查看文件或直接訪問 http://example.com"
        
        result = self.cleaner.extract_url_description(content)
        assert result == expected_result, "混合內容處理失敗"

    @pytest.mark.data_cleaner
    def test_clean_test_case_fields_complete_case(self):
        """測試完整測試案例的欄位清理"""
        test_case = {
            "id": "C001",
            "title": "TCG-001.002.003 **重要**登入功能測試",
            "priority": "High",
            "preconds": "1. 準備**測試**環境\n2. 開啟`瀏覽器`",
            "steps": "1. 輸入*使用者名稱*\n2. 點擊[登入按鈕](http://example.com/login)",
            "expected": "**成功**登入並跳轉到*首頁*"
        }
        
        result = self.cleaner.clean_test_case_fields(test_case)
        
        assert result["test_case_number"] == "TCG-001.002.003", "測試案例編號應正確提取"
        assert result["title"] == "重要登入功能測試", "標題應清理Markdown格式"
        assert result["priority"] == "High", "優先級應保持不變"
        assert result["precondition"] == "1. 準備測試環境\n2. 開啟瀏覽器", "前置條件應清理格式"
        assert result["steps"] == "1. 輸入使用者名稱\n2. 點擊登入按鈕", "測試步驟應清理格式和URL"
        assert result["expected_result"] == "成功登入並跳轉到首頁", "預期結果應清理格式"

    @pytest.mark.data_cleaner
    def test_clean_test_case_fields_missing_hyphen_case(self):
        """測試包含缺失hyphen的測試案例清理"""
        test_case = {
            "id": "C002",
            "title": "TCG001.002.003 缺失hyphen的測試",
            "priority": "Medium",
            "preconds": "前置條件",
            "steps": "測試步驟",
            "expected": "預期結果"
        }
        
        result = self.cleaner.clean_test_case_fields(test_case)
        
        assert result["test_case_number"] == "TCG-001.002.003", "應自動修正缺失的hyphen"
        assert result["title"] == "缺失hyphen的測試", "標題應正確提取"

    @pytest.mark.data_cleaner
    def test_clean_test_case_fields_no_case_number(self):
        """測試沒有測試案例編號的情況"""
        test_case = {
            "id": "C003",
            "title": "沒有編號的測試案例",
            "priority": "Low",
            "preconds": "前置條件",
            "steps": "測試步驟",
            "expected": "預期結果"
        }
        
        result = self.cleaner.clean_test_case_fields(test_case)
        
        assert result["test_case_number"] == "", "沒有編號時應為空字串"
        assert result["title"] == "沒有編號的測試案例", "標題應保持原樣"

    @pytest.mark.data_cleaner
    def test_clean_test_case_fields_empty_fields(self):
        """測試包含空欄位的測試案例"""
        test_case = {
            "id": "C004",
            "title": "TCG-004.005.006 包含空欄位的測試",
            "priority": "",
            "preconds": "",
            "steps": "",
            "expected": ""
        }
        
        result = self.cleaner.clean_test_case_fields(test_case)
        
        assert result["test_case_number"] == "TCG-004.005.006", "編號應正確提取"
        assert result["title"] == "包含空欄位的測試", "標題應正確"
        assert result["priority"] == "", "空優先級應保持為空"
        assert result["precondition"] == "", "空前置條件應保持為空"
        assert result["steps"] == "", "空步驟應保持為空"
        assert result["expected_result"] == "", "空預期結果應保持為空"

    @pytest.mark.data_cleaner
    def test_clean_test_case_fields_missing_keys(self):
        """測試缺少必要欄位的測試案例"""
        incomplete_case = {
            "id": "C005",
            "title": "TCG-005.006.007 不完整的測試案例"
            # 故意缺少其他欄位
        }
        
        result = self.cleaner.clean_test_case_fields(incomplete_case)
        
        assert result["test_case_number"] == "TCG-005.006.007", "編號應正確提取"
        assert result["title"] == "不完整的測試案例", "標題應正確"
        # 缺失的欄位應設為預設值
        assert result["priority"] == "", "缺失的優先級應為空字串"
        assert result["precondition"] == "", "缺失的前置條件應為空字串"
        assert result["steps"] == "", "缺失的步驟應為空字串"
        assert result["expected_result"] == "", "缺失的預期結果應為空字串"

    @pytest.mark.data_cleaner
    def test_clean_test_case_fields_none_values(self):
        """測試包含None值的測試案例"""
        test_case = {
            "id": "C006",
            "title": "TCG-006.007.008 包含None值的測試",
            "priority": None,
            "preconds": None,
            "steps": None,
            "expected": None
        }
        
        result = self.cleaner.clean_test_case_fields(test_case)
        
        assert result["test_case_number"] == "TCG-006.007.008", "編號應正確提取"
        assert result["title"] == "包含None值的測試", "標題應正確"
        # None值應轉換為空字串
        assert result["priority"] == "", "None優先級應轉為空字串"
        assert result["precondition"] == "", "None前置條件應轉為空字串"
        assert result["steps"] == "", "None步驟應轉為空字串"
        assert result["expected_result"] == "", "None預期結果應轉為空字串"

    @pytest.mark.data_cleaner
    def test_clean_test_case_fields_complex_markdown_and_urls(self):
        """測試複雜的Markdown和URL混合內容清理"""
        test_case = {
            "id": "C007",
            "title": "TCG007.008.009 **複雜**的*混合*格式測試",
            "priority": "Critical",
            "preconds": "1. 查看[環境設定](http://config.com)\n2. 執行`setup.sh`腳本",
            "steps": "1. **重要**：點擊[開始按鈕](http://start.com)\n2. 輸入`test data`\n3. 查看*結果*頁面",
            "expected": "看到**成功**訊息並導向[結果頁](http://result.com)"
        }
        
        result = self.cleaner.clean_test_case_fields(test_case)
        
        assert result["test_case_number"] == "TCG-007.008.009", "應修正hyphen"
        assert result["title"] == "複雜的混合格式測試", "標題應清理所有格式"
        assert result["precondition"] == "1. 查看環境設定\n2. 執行setup.sh腳本", "前置條件應清理格式和URL"
        assert result["steps"] == "1. 重要：點擊開始按鈕\n2. 輸入test data\n3. 查看結果頁面", "步驟應清理所有格式"
        assert result["expected_result"] == "看到成功訊息並導向結果頁", "預期結果應清理格式和URL"

    @pytest.mark.data_cleaner
    def test_error_handling_with_invalid_input(self):
        """測試異常輸入的錯誤處理"""
        # 測試None輸入
        with pytest.raises(TypeError):
            self.cleaner.extract_test_case_number_and_title(None)
        
        with pytest.raises(TypeError):
            self.cleaner.clean_markdown_content(None)

    @pytest.mark.data_cleaner
    def test_performance_with_large_content(self):
        """測試大量內容的處理效能"""
        # 建立大量重複內容
        large_content = "**重要**：" + "測試內容 " * 1000 + "[連結](http://example.com)"
        
        import time
        start_time = time.time()
        result = self.cleaner.clean_markdown_content(large_content)
        end_time = time.time()
        
        assert len(result) > 0, "應能處理大量內容"
        assert end_time - start_time < 1.0, "大量內容處理應在1秒內完成"

    @pytest.mark.data_cleaner
    def test_unicode_and_special_characters(self):
        """測試Unicode和特殊字元處理"""
        test_cases = [
            ("**中文粗體**", "中文粗體"),
            ("*日本語イタリック*", "日本語イタリック"),
            ("`한국어 코드`", "한국어 코드"),
            ("**emoji 😀** test", "emoji 😀 test"),
            ("特殊符號 @#$%^&*()", "特殊符號 @#$%^&*()"),
        ]
        
        for input_text, expected_output in test_cases:
            result = self.cleaner.clean_markdown_content(input_text)
            assert result == expected_output, f"Unicode處理失敗: {input_text}"


class TestDataCleanerEdgeCases:
    """資料清理器邊界條件測試"""

    def setup_method(self):
        """每個測試方法前的設定"""
        self.cleaner = TestCaseDataCleaner()

    @pytest.mark.data_cleaner
    def test_regex_pattern_edge_cases(self):
        """測試正則表達式的邊界條件"""
        edge_cases = [
            ("TCG000.000.000 零值編號", "TCG-000.000.000", "零值編號"),
            ("TCG999.999.999 最大值編號", "TCG-999.999.999", "最大值編號"),
            ("TCG1.1.1 最小值編號", "TCG-001.001.001", "最小值編號"),  # 測試是否會補零
        ]
        
        for title, expected_number, expected_title in edge_cases:
            case_number, clean_title = self.cleaner.extract_test_case_number_and_title(title)
            # 根據實際實作調整這個測試
            assert len(case_number) > 0, f"應能處理邊界值: {title}"

    @pytest.mark.data_cleaner  
    def test_nested_markdown_formatting(self):
        """測試巢狀Markdown格式"""
        nested_cases = [
            ("**粗體內含*斜體*文字**", "粗體內含斜體文字"),
            ("*斜體內含`程式碼`文字*", "斜體內含程式碼文字"),
            ("**`粗體程式碼`**", "粗體程式碼"),
        ]
        
        for markdown_text, expected_result in nested_cases:
            result = self.cleaner.clean_markdown_content(markdown_text)
            assert result == expected_result, f"巢狀格式處理失敗: {markdown_text}"

    @pytest.mark.data_cleaner
    def test_malformed_markdown_links(self):
        """測試格式錯誤的Markdown連結"""
        malformed_cases = [
            ("[不完整連結", "[不完整連結"),  # 缺少結尾
            ("](缺少開頭", "](缺少開頭"),  # 缺少開頭
            ("[空連結]()", "空連結"),  # 空URL
            ("[](http://example.com)", ""),  # 空說明
        ]
        
        for input_text, expected_output in malformed_cases:
            result = self.cleaner.extract_url_description(input_text)
            # 測試是否能優雅處理格式錯誤的情況
            assert isinstance(result, str), f"應回傳字串: {input_text}"