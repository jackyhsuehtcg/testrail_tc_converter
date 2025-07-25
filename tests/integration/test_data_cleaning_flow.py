"""
資料清理器整合測試

測試完整的XML解析 -> 資料清理流程
"""

import pytest
from pathlib import Path

from parsers.xml_parser import TestRailXMLParser
from parsers.data_cleaner import TestCaseDataCleaner


class TestDataCleaningIntegration:
    """資料清理整合測試"""

    def setup_method(self):
        """每個測試方法前的設定"""
        self.xml_parser = TestRailXMLParser()
        self.data_cleaner = TestCaseDataCleaner()

    @pytest.mark.integration
    def test_complete_data_cleaning_flow(self, test_data_path):
        """測試完整的XML解析到資料清理流程"""
        # 1. 解析XML檔案
        xml_file = test_data_path / "xml" / "sample_basic.xml"
        raw_test_cases = self.xml_parser.parse_xml_file(str(xml_file))
        
        assert len(raw_test_cases) > 0, "應解析出測試案例"
        
        # 2. 清理每個測試案例
        cleaned_cases = []
        for raw_case in raw_test_cases:
            cleaned_case = self.data_cleaner.clean_test_case_fields(raw_case)
            cleaned_cases.append(cleaned_case)
        
        assert len(cleaned_cases) == len(raw_test_cases), "清理後案例數量應相同"
        
        # 3. 驗證清理結果
        for cleaned_case in cleaned_cases:
            # 檢查必要欄位存在
            required_fields = ["test_case_number", "title", "priority", 
                             "precondition", "steps", "expected_result"]
            for field in required_fields:
                assert field in cleaned_case, f"清理後應包含欄位: {field}"
            
            # 檢查資料類型
            assert isinstance(cleaned_case["test_case_number"], str), "編號應為字串"
            assert isinstance(cleaned_case["title"], str), "標題應為字串"
            assert isinstance(cleaned_case["priority"], str), "優先級應為字串"
            assert isinstance(cleaned_case["precondition"], str), "前置條件應為字串"
            assert isinstance(cleaned_case["steps"], str), "步驟應為字串"
            assert isinstance(cleaned_case["expected_result"], str), "預期結果應為字串"

    @pytest.mark.integration
    def test_markdown_content_cleaning_integration(self, file_test_helper):
        """測試包含Markdown格式的XML解析和清理"""
        # 建立包含Markdown格式的測試XML
        markdown_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<suite>
    <sections>
        <section>
            <cases>
                <case>
                    <id>C001</id>
                    <title>TCG001.002.003 **重要**的*登入*測試</title>
                    <priority>High</priority>
                    <custom>
                        <preconds>1. 開啟`瀏覽器`
2. 前往[登入頁面](http://example.com/login)</preconds>
                        <steps>1. 輸入**使用者名稱**
2. 輸入*密碼*
3. 點擊[登入按鈕](http://example.com/submit)</steps>
                        <expected>看到**成功**訊息並跳轉到[首頁](http://example.com/home)</expected>
                    </custom>
                </case>
            </cases>
        </section>
    </sections>
</suite>'''
        
        # 建立臨時XML檔案
        temp_file = file_test_helper.create_temp_file(markdown_xml, "markdown_test.xml")
        
        # 1. 解析XML
        raw_cases = self.xml_parser.parse_xml_file(str(temp_file))
        assert len(raw_cases) == 1, "應解析出一個測試案例"
        
        # 2. 清理資料
        cleaned_case = self.data_cleaner.clean_test_case_fields(raw_cases[0])
        
        # 3. 驗證清理結果
        assert cleaned_case["test_case_number"] == "TCG-001.002.003", "應修正hyphen"
        assert cleaned_case["title"] == "重要的登入測試", "標題應清理Markdown格式"
        assert cleaned_case["precondition"] == "1. 開啟瀏覽器\n2. 前往登入頁面", "前置條件應清理格式"
        assert cleaned_case["steps"] == "1. 輸入使用者名稱\n2. 輸入密碼\n3. 點擊登入按鈕", "步驟應清理格式"
        assert cleaned_case["expected_result"] == "看到成功訊息並跳轉到首頁", "預期結果應清理格式"

    @pytest.mark.integration
    def test_real_testrail_data_cleaning(self, test_data_path):
        """測試真實TestRail資料的解析和清理"""
        xml_file = test_data_path / "xml" / "TP-3153 Associated Users Phase 2.xml"
        
        # 1. 解析真實的TestRail XML
        raw_cases = self.xml_parser.parse_xml_file(str(xml_file))
        assert len(raw_cases) > 0, "真實資料應包含測試案例"
        
        # 2. 清理所有測試案例
        cleaned_cases = []
        for raw_case in raw_cases:
            try:
                cleaned_case = self.data_cleaner.clean_test_case_fields(raw_case)
                cleaned_cases.append(cleaned_case)
            except Exception as e:
                pytest.fail(f"清理真實資料失敗: {e}")
        
        assert len(cleaned_cases) > 0, "應成功清理真實資料"
        
        # 3. 驗證清理品質
        valid_cases = 0
        for cleaned_case in cleaned_cases:
            # 統計有效的測試案例（有編號和標題）
            if cleaned_case["test_case_number"] and cleaned_case["title"]:
                valid_cases += 1
                
                # 檢查編號格式是否正確
                case_number = cleaned_case["test_case_number"]
                if case_number:
                    assert case_number.startswith("TCG-"), f"編號格式錯誤: {case_number}"
                    assert "." in case_number, f"編號應包含點號: {case_number}"
        
        # 至少應該有一些有效的測試案例
        assert valid_cases > 0, "真實資料應包含有效的測試案例"

    @pytest.mark.integration
    def test_error_recovery_in_cleaning_flow(self, file_test_helper):
        """測試清理流程中的錯誤恢復"""
        # 建立包含問題資料的XML
        problematic_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<suite>
    <sections>
        <section>
            <cases>
                <case>
                    <id>C001</id>
                    <title>TCG-001.002.003 正常案例</title>
                    <priority>High</priority>
                    <custom>
                        <preconds>正常前置條件</preconds>
                        <steps>正常步驟</steps>
                        <expected>正常預期結果</expected>
                    </custom>
                </case>
                <case>
                    <id>C002</id>
                    <title>無編號的案例</title>
                    <priority>Medium</priority>
                    <custom>
                        <preconds></preconds>
                        <steps></steps>
                        <expected></expected>
                    </custom>
                </case>
                <case>
                    <id>C003</id>
                    <title></title>
                    <priority></priority>
                </case>
            </cases>
        </section>
    </sections>
</suite>'''
        
        temp_file = file_test_helper.create_temp_file(problematic_xml, "problematic_test.xml")
        
        # 1. 解析XML（應該能處理問題資料）
        raw_cases = self.xml_parser.parse_xml_file(str(temp_file))
        
        # 2. 嘗試清理所有案例（不應該因為單個案例問題而停止）
        cleaned_cases = []
        errors = []
        
        for raw_case in raw_cases:
            try:
                cleaned_case = self.data_cleaner.clean_test_case_fields(raw_case)
                cleaned_cases.append(cleaned_case)
            except Exception as e:
                errors.append(e)
        
        # 3. 驗證錯誤恢復
        assert len(cleaned_cases) > 0, "應該能處理部分案例"
        # 即使有問題案例，也不應該有錯誤（應該優雅處理）
        assert len(errors) == 0, "資料清理應該優雅處理問題資料"
        
        # 檢查清理結果
        normal_cases = [case for case in cleaned_cases if case["test_case_number"]]
        assert len(normal_cases) >= 1, "應該至少有一個正常案例"

    @pytest.mark.integration
    def test_performance_with_large_dataset(self, file_test_helper):
        """測試大量資料的處理效能"""
        # 建立大量測試案例的XML
        cases_xml = ""
        for i in range(100):  # 建立100個測試案例
            cases_xml += f'''
                <case>
                    <id>C{i:03d}</id>
                    <title>TCG{i:03d}.001.001 效能測試案例 {i}</title>
                    <priority>Medium</priority>
                    <custom>
                        <preconds>**重要**：效能測試前置條件 {i}</preconds>
                        <steps>1. 執行*步驟*一
2. 執行`命令` {i}
3. 查看[結果](http://result{i}.com)</steps>
                        <expected>看到**成功**訊息 {i}</expected>
                    </custom>
                </case>'''
        
        large_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<suite>
    <sections>
        <section>
            <cases>{cases_xml}
            </cases>
        </section>
    </sections>
</suite>'''
        
        temp_file = file_test_helper.create_temp_file(large_xml, "large_dataset.xml")
        
        import time
        
        # 1. 測試XML解析效能
        start_time = time.time()
        raw_cases = self.xml_parser.parse_xml_file(str(temp_file))
        parse_time = time.time() - start_time
        
        assert len(raw_cases) == 100, "應解析出100個測試案例"
        assert parse_time < 5.0, "XML解析應在5秒內完成"
        
        # 2. 測試資料清理效能
        start_time = time.time()
        cleaned_cases = []
        for raw_case in raw_cases:
            cleaned_case = self.data_cleaner.clean_test_case_fields(raw_case)
            cleaned_cases.append(cleaned_case)
        cleaning_time = time.time() - start_time
        
        assert len(cleaned_cases) == 100, "應清理100個測試案例"
        assert cleaning_time < 5.0, "資料清理應在5秒內完成"
        
        # 3. 驗證清理品質
        for i, cleaned_case in enumerate(cleaned_cases):
            assert cleaned_case["test_case_number"] == f"TCG-{i:03d}.001.001", f"編號應正確修正: {i}"
            assert "效能測試案例" in cleaned_case["title"], f"標題應正確: {i}"
            assert "重要：效能測試前置條件" in cleaned_case["precondition"], f"前置條件應清理格式: {i}"
            assert "執行步驟一" in cleaned_case["steps"], f"步驟應清理格式: {i}"
            assert "看到成功訊息" in cleaned_case["expected_result"], f"預期結果應清理格式: {i}"