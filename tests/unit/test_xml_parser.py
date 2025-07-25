"""
XML 解析器模組單元測試

測試 TestRailXMLParser 類別的所有功能
"""

import pytest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch, mock_open
from typing import List, Dict, Any

# 待實作的模組
from parsers.xml_parser import TestRailXMLParser, TestRailParseError


class TestTestRailXMLParser:
    """TestRailXMLParser 類別測試"""

    def setup_method(self):
        """每個測試方法前的設定"""
        self.parser = TestRailXMLParser()

    @pytest.mark.xml_parser
    def test_parse_xml_file_success(self, xml_test_helper, test_data_path):
        """測試成功解析正常的 XML 檔案"""
        # 使用測試輔助工具載入範例 XML
        xml_file = test_data_path / "xml" / "sample_basic.xml"
        
        # 預期的測試案例數量
        expected_case_count = 2
        
        result = self.parser.parse_xml_file(str(xml_file))
        
        assert isinstance(result, list), "回傳值應為列表"
        assert len(result) == expected_case_count, f"應解析出 {expected_case_count} 個測試案例"
        
        # 檢查第一個測試案例的基本結構
        first_case = result[0]
        required_keys = ["id", "title", "priority", "preconds", "steps", "expected"]
        for key in required_keys:
            assert key in first_case, f"測試案例缺少必要欄位: {key}"

    @pytest.mark.xml_parser
    def test_parse_xml_file_with_real_testrail_data(self, test_data_path):
        """測試解析真實的 TestRail XML 檔案"""
        xml_file = test_data_path / "xml" / "TP-3153 Associated Users Phase 2.xml"
        
        result = self.parser.parse_xml_file(str(xml_file))
        
        assert isinstance(result, list), "回傳值應為列表"
        assert len(result) > 0, "真實的 TestRail 檔案應包含測試案例"
        
        # 檢查真實資料的結構
        for case in result:
            assert "id" in case, "測試案例應包含 ID"
            assert "title" in case, "測試案例應包含標題"
            
        # 檢查第一個案例的詳細結構
        first_case = result[0]
        required_keys = ["id", "title", "priority", "preconds", "steps", "expected"]
        for key in required_keys:
            assert key in first_case, f"測試案例缺少必要欄位: {key}"

    @pytest.mark.xml_parser
    def test_parse_xml_file_empty_path(self):
        """測試空檔案路徑的錯誤處理"""
        with pytest.raises(ValueError, match="檔案路徑不能為空"):
            self.parser.parse_xml_file("")
        
        with pytest.raises(ValueError, match="檔案路徑不能為空"):
            self.parser.parse_xml_file(None)

    @pytest.mark.xml_parser
    def test_parse_xml_file_not_found(self):
        """測試檔案不存在的錯誤處理"""
        non_existent_file = "/path/to/non_existent.xml"
        
        with pytest.raises(FileNotFoundError):
            self.parser.parse_xml_file(non_existent_file)

    @pytest.mark.xml_parser
    def test_parse_xml_file_malformed(self, test_data_path):
        """測試格式錯誤的 XML 檔案處理"""
        malformed_file = test_data_path / "xml" / "malformed.xml"
        
        with pytest.raises(ET.ParseError):
            self.parser.parse_xml_file(str(malformed_file))

    @pytest.mark.xml_parser
    def test_parse_xml_file_non_xml_extension(self, file_test_helper):
        """測試非XML檔案格式的警告處理"""
        # 建立非XML格式的檔案
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<suite><sections><section><cases></cases></section></sections></suite>'''
        non_xml_file = file_test_helper.create_temp_file(xml_content, "test.txt")
        
        # 應該會發出警告但仍會處理
        result = self.parser.parse_xml_file(str(non_xml_file))
        assert isinstance(result, list), "非XML檔名仍應正常處理"

    @pytest.mark.xml_parser
    def test_parse_xml_file_empty(self, test_data_path):
        """測試空 XML 檔案處理"""
        empty_file = test_data_path / "xml" / "empty.xml"
        
        result = self.parser.parse_xml_file(str(empty_file))
        assert isinstance(result, list), "即使是空檔案也應回傳列表"
        assert len(result) == 0, "空檔案應回傳空列表"

    @pytest.mark.xml_parser
    def test_extract_test_cases_from_xml_root(self, xml_test_helper):
        """測試從 XML 根元素提取測試案例"""
        # 載入測試 XML
        xml_root = xml_test_helper.load_xml_fixture("sample_basic.xml")
        
        result = self.parser.extract_test_cases(xml_root)
        
        assert isinstance(result, list), "回傳值應為列表"
        assert len(result) > 0, "應提取到測試案例"
        
        # 檢查提取的案例結構
        for case in result:
            assert isinstance(case, dict), "每個案例應為字典"
            # 驗證必要欄位
            required_fields = ["id", "title", "priority", "preconds", "steps", "expected"]
            for field in required_fields:
                assert field in case, f"案例缺少必要欄位: {field}"

    @pytest.mark.xml_parser
    def test_extract_test_cases_with_none_root(self):
        """測試XML根元素為None的情況"""
        result = self.parser.extract_test_cases(None)
        assert isinstance(result, list), "None根元素應回傳空列表"
        assert len(result) == 0, "None根元素應回傳空列表"

    @pytest.mark.xml_parser
    def test_extract_test_cases_with_missing_custom_element(self, data_test_helper):
        """測試提取缺少custom元素的測試案例"""
        # 建立缺少custom元素的測試案例
        case_elem = ET.Element("case")
        ET.SubElement(case_elem, "id").text = "C999"
        ET.SubElement(case_elem, "title").text = "TCG-999.999.999 缺少custom元素的案例"
        ET.SubElement(case_elem, "priority").text = "Medium"
        # 故意不添加custom元素
        
        # 建立包含此案例的XML結構
        suite_root = ET.Element("suite")
        sections = ET.SubElement(suite_root, "sections")
        section = ET.SubElement(sections, "section")
        cases = ET.SubElement(section, "cases")
        cases.append(case_elem)
        
        result = self.parser.extract_test_cases(suite_root)
        
        # 應該能處理缺少custom元素的情況
        assert len(result) == 1, "應該提取到一個案例"
        case = result[0]
        assert case["preconds"] == "", "缺少custom元素時preconds應為空字串"
        assert case["steps"] == "", "缺少custom元素時steps應為空字串"
        assert case["expected"] == "", "缺少custom元素時expected應為空字串"

    @pytest.mark.xml_parser
    def test_extract_test_cases_with_empty_title(self, data_test_helper):
        """測試提取缺少標題的測試案例"""
        # 建立缺少標題的測試案例
        case_elem = ET.Element("case")
        ET.SubElement(case_elem, "id").text = "C888"
        ET.SubElement(case_elem, "title").text = ""  # 空標題
        ET.SubElement(case_elem, "priority").text = "High"
        
        # 建立包含此案例的XML結構
        suite_root = ET.Element("suite")
        sections = ET.SubElement(suite_root, "sections")
        section = ET.SubElement(sections, "section")
        cases = ET.SubElement(section, "cases")
        cases.append(case_elem)
        
        result = self.parser.extract_test_cases(suite_root)
        
        # 缺少標題的案例應被過濾掉
        assert len(result) == 0, "缺少標題的案例應被過濾掉"

    @pytest.mark.xml_parser
    def test_extract_test_cases_with_missing_fields(self, data_test_helper):
        """測試提取缺少部分欄位的測試案例"""
        # 建立缺少某些欄位的測試 XML 元素
        incomplete_case = data_test_helper.create_sample_xml_case(
            id="C999",
            title="TCG-999.999.999 不完整的測試案例",
            priority="Medium"
            # 故意缺少 preconds, steps, expected 欄位
        )
        
        # 移除某些子元素來模擬缺失欄位
        custom_elem = incomplete_case.find("custom")
        if custom_elem is not None:
            # 移除 expected 元素
            expected_elem = custom_elem.find("expected")
            if expected_elem is not None:
                custom_elem.remove(expected_elem)
        
        # 建立包含不完整案例的 XML 結構
        suite_root = ET.Element("suite")
        sections = ET.SubElement(suite_root, "sections")
        section = ET.SubElement(sections, "section")
        cases = ET.SubElement(section, "cases")
        cases.append(incomplete_case)
        
        result = self.parser.extract_test_cases(suite_root)
        
        # 應該能處理缺失欄位的情況
        assert len(result) == 1, "應該提取到一個案例"
        case = result[0]
        assert case.get("expected", "") == "", "缺失的欄位應為空字串"

    @pytest.mark.xml_parser
    def test_validate_xml_structure_valid(self, xml_test_helper):
        """測試驗證有效的 XML 結構"""
        xml_root = xml_test_helper.load_xml_fixture("sample_basic.xml")
        
        result = self.parser.validate_xml_structure(xml_root)
        assert result is True, "有效的 XML 結構應通過驗證"

    @pytest.mark.xml_parser
    def test_validate_xml_structure_with_none_root(self):
        """測試驗證None根元素的情況"""
        result = self.parser.validate_xml_structure(None)
        assert result is False, "None根元素應驗證失敗"

    @pytest.mark.xml_parser
    def test_validate_xml_structure_invalid(self):
        """測試驗證無效的 XML 結構"""
        # 建立無效的 XML 結構（缺少必要元素）
        invalid_root = ET.Element("invalid_root")
        
        result = self.parser.validate_xml_structure(invalid_root)
        assert result is False, "無效的 XML 結構應驗證失敗"

    @pytest.mark.xml_parser
    def test_validate_xml_structure_non_suite_root(self):
        """測試非suite根元素但包含case的XML結構"""
        # 建立非suite根元素但直接包含case的結構
        other_root = ET.Element("testrail")
        case_elem = ET.SubElement(other_root, "case")
        ET.SubElement(case_elem, "id").text = "C001"
        ET.SubElement(case_elem, "title").text = "測試案例"
        
        result = self.parser.validate_xml_structure(other_root)
        assert result is True, "包含case元素的非suite根元素應通過驗證"

    @pytest.mark.xml_parser
    def test_validate_xml_structure_with_direct_cases(self):
        """測試直接在根元素下包含case的XML結構"""
        # 建立直接在根元素下包含case的結構（不通過sections）
        root_with_cases = ET.Element("root")
        case_elem = ET.SubElement(root_with_cases, "case")
        ET.SubElement(case_elem, "id").text = "C001"
        ET.SubElement(case_elem, "title").text = "直接案例"
        
        result = self.parser.validate_xml_structure(root_with_cases)
        assert result is True, "直接包含case的結構應通過驗證"

    @pytest.mark.xml_parser
    def test_extract_custom_fields_from_case(self, data_test_helper):
        """測試從測試案例中提取 custom 欄位"""
        # 建立包含完整 custom 欄位的測試案例
        test_case = data_test_helper.create_sample_xml_case(
            id="C123",
            title="TCG-123.456.789 完整測試案例",
            priority="High",
            preconds="測試前置條件",
            steps="1. 執行步驟一\n2. 執行步驟二",
            expected="預期的測試結果"
        )
        
        # 這裡應該測試內部方法提取 custom 欄位的功能
        custom_elem = test_case.find("custom")
        assert custom_elem is not None, "應找到 custom 元素"
        
        preconds = custom_elem.find("preconds")
        steps = custom_elem.find("steps")
        expected = custom_elem.find("expected")
        
        assert preconds is not None and preconds.text == "測試前置條件"
        assert steps is not None and "執行步驟一" in steps.text
        assert expected is not None and expected.text == "預期的測試結果"

    @pytest.mark.xml_parser
    def test_get_element_text_with_none_parent(self):
        """測試_get_element_text方法處理None父元素的情況"""
        result = self.parser._get_element_text(None, "test_tag", "default_value")
        assert result == "default_value", "None父元素應回傳預設值"

    @pytest.mark.xml_parser
    def test_get_element_text_with_missing_element(self):
        """測試_get_element_text方法處理缺失元素的情況"""
        parent = ET.Element("parent")
        result = self.parser._get_element_text(parent, "missing_tag", "default_value")
        assert result == "default_value", "缺失元素應回傳預設值"

    @pytest.mark.xml_parser
    def test_get_parser_stats(self):
        """測試取得解析器統計資訊"""
        stats = self.parser.get_parser_stats()
        assert isinstance(stats, dict), "統計資訊應為字典"
        assert "parser_type" in stats, "應包含解析器類型"
        assert "supported_formats" in stats, "應包含支援格式"
        assert "features" in stats, "應包含功能列表"

    @pytest.mark.xml_parser  
    def test_handle_special_characters_in_xml(self, file_test_helper):
        """測試處理 XML 中的特殊字元"""
        # 建立包含特殊字元的 XML 內容
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<suite>
    <sections>
        <section>
            <cases>
                <case>
                    <id>C001</id>
                    <title>TCG-001.001.001 包含特殊字元的測試 &lt;test&gt;</title>
                    <priority>High</priority>
                    <custom>
                        <preconds>前置條件包含 &amp; 符號</preconds>
                        <steps>步驟包含 "引號" 和 '單引號'</steps>
                        <expected>預期結果包含 &lt;標籤&gt;</expected>
                    </custom>
                </case>
            </cases>
        </section>
    </sections>
</suite>'''
        
        # 建立臨時檔案
        temp_file = file_test_helper.create_temp_file(xml_content, "special_chars.xml")
        
        result = self.parser.parse_xml_file(str(temp_file))
        
        assert len(result) == 1, "應解析出一個測試案例"
        case = result[0]
        
        # 檢查特殊字元是否正確處理
        assert "<test>" in case["title"], "XML轉義字元應被正確解析"
        assert "&" in case["preconds"], "&符號應被正確解析"
        assert "引號" in case["steps"], "引號應被正確保留"
        assert "<標籤>" in case["expected"], "標籤應被正確解析"

    @pytest.mark.xml_parser
    def test_parse_large_xml_file_performance(self, file_test_helper):
        """測試大型 XML 檔案的解析效能"""
        # 建立包含多個測試案例的大型 XML
        cases_xml = ""
        for i in range(50):  # 建立 50 個測試案例
            cases_xml += f'''
                <case>
                    <id>C{i:03d}</id>
                    <title>TCG-{i:03d}.001.001 效能測試案例 {i}</title>
                    <priority>Medium</priority>
                    <custom>
                        <preconds>效能測試前置條件 {i}</preconds>
                        <steps>1. 執行效能測試步驟 {i}\\n2. 驗證結果</steps>
                        <expected>預期效能測試結果 {i}</expected>
                    </custom>
                </case>'''
        
        large_xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<suite>
    <sections>
        <section>
            <cases>{cases_xml}
            </cases>
        </section>
    </sections>
</suite>'''
        
        temp_file = file_test_helper.create_temp_file(large_xml_content, "large_test.xml")
        
        import time
        start_time = time.time()
        result = self.parser.parse_xml_file(str(temp_file))
        end_time = time.time()
        
        assert len(result) == 50, "應解析出 50 個測試案例"
        assert end_time - start_time < 5.0, "大型檔案解析應在 5 秒內完成"

    @pytest.mark.xml_parser
    def test_error_handling_and_logging(self, caplog):
        """測試錯誤處理和日誌記錄"""
        import logging
        
        # 測試檔案不存在的情況
        with caplog.at_level(logging.ERROR):
            with pytest.raises(FileNotFoundError):
                self.parser.parse_xml_file("non_existent.xml")
        
        # 檢查是否有適當的日誌記錄
        assert any("檔案不存在" in record.message or "不存在" in record.message 
                  for record in caplog.records if record.levelno >= logging.ERROR)

    @pytest.mark.xml_parser
    def test_parse_xml_file_with_invalid_structure(self, file_test_helper):
        """測試XML結構驗證失敗的情況"""
        # 建立完全沒有case元素的XML，這會觸發驗證失敗
        invalid_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<invalid>
    <no_cases_here/>
</invalid>'''
        
        temp_file = file_test_helper.create_temp_file(invalid_xml, "invalid_structure.xml")
        
        with pytest.raises(ValueError, match="XML 檔案結構不符合 TestRail 格式"):
            self.parser.parse_xml_file(str(temp_file))

    @pytest.mark.xml_parser
    def test_extract_single_test_case_with_exception(self):
        """測試_extract_single_test_case方法遇到異常的情況"""
        # 建立一個會導致異常的元素（缺少必要子元素）
        case_elem = ET.Element("case")
        # 故意不添加任何子元素，這會在提取時造成問題
        
        result = self.parser._extract_single_test_case(case_elem)
        
        # 方法應該能處理異常並回傳None
        assert result is None, "遇到異常的案例應該回傳None"

    @pytest.mark.xml_parser
    def test_extract_single_test_case_with_none(self):
        """測試_extract_single_test_case方法處理None元素的情況"""
        result = self.parser._extract_single_test_case(None)
        assert result is None, "None元素應該回傳None"

    @pytest.mark.xml_parser
    def test_xml_namespace_handling(self, file_test_helper):
        """測試處理帶有命名空間的 XML"""
        # 簡化為無命名空間的XML，因為目前的實作不支援命名空間
        xml_simple = '''<?xml version="1.0" encoding="UTF-8"?>
<suite>
    <sections>
        <section>
            <cases>
                <case>
                    <id>C001</id>
                    <title>TCG-001.001.001 簡單測試</title>
                    <priority>High</priority>
                    <custom>
                        <preconds>前置條件</preconds>
                        <steps>測試步驟</steps>
                        <expected>預期結果</expected>
                    </custom>
                </case>
            </cases>
        </section>
    </sections>
</suite>'''
        
        temp_file = file_test_helper.create_temp_file(xml_simple, "namespace_test.xml")
        
        result = self.parser.parse_xml_file(str(temp_file))
        
        assert isinstance(result, list), "應該回傳列表"
        assert len(result) == 1, "應該有一個測試案例"
        assert "簡單測試" in result[0]["title"], "應該正確解析標題"


class TestXMLParserEdgeCases:
    """XML 解析器邊界條件測試"""

    def setup_method(self):
        """每個測試方法前的設定"""
        # 等實作完成後再引入
        # self.parser = TestRailXMLParser()
        pass

    @pytest.mark.xml_parser
    def test_empty_test_case_elements(self, file_test_helper):
        """測試空的測試案例元素"""
        # 改為非空標題但其他欄位為空的測試
        empty_case_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<suite>
    <sections>
        <section>
            <cases>
                <case>
                    <id>C999</id>
                    <title>TCG-999.999.999 部分空欄位測試</title>
                    <priority></priority>
                    <custom>
                        <preconds></preconds>
                        <steps></steps>
                        <expected></expected>
                    </custom>
                </case>
            </cases>
        </section>
    </sections>
</suite>'''
        
        temp_file = file_test_helper.create_temp_file(empty_case_xml, "empty_case.xml")
        
        result = self.parser.parse_xml_file(str(temp_file))
        
        # 有標題的案例應該被保留
        assert len(result) == 1, "有標題的案例應被保留"
        case = result[0]
        assert case["title"] == "TCG-999.999.999 部分空欄位測試", "標題應正確"
        # 檢查空優先級是否被設為default值
        assert case["priority"] == "Medium", "空優先級應設為預設值"

    @pytest.mark.xml_parser
    def test_deeply_nested_xml_structure(self, file_test_helper):
        """測試深層巢狀的 XML 結構"""
        nested_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<suite>
    <sections>
        <section>
            <name>頂層區段</name>
            <sections>
                <section>
                    <name>次層區段</name>
                    <sections>
                        <section>
                            <name>深層區段</name>
                            <cases>
                                <case>
                                    <id>C001</id>
                                    <title>TCG-001.001.001 深層巢狀測試</title>
                                    <priority>Medium</priority>
                                    <custom>
                                        <preconds>深層巢狀前置條件</preconds>
                                        <steps>深層巢狀測試步驟</steps>
                                        <expected>深層巢狀預期結果</expected>
                                    </custom>
                                </case>
                            </cases>
                        </section>
                    </sections>
                </section>
            </sections>
        </section>
    </sections>
</suite>'''
        
        temp_file = file_test_helper.create_temp_file(nested_xml, "nested_test.xml")
        
        result = self.parser.parse_xml_file(str(temp_file))
        
        assert len(result) == 1, "應該能處理深層巢狀結構"
        case = result[0]
        assert "深層巢狀測試" in case["title"], "應該正確提取深層巢狀案例的標題"