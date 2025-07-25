"""
Lark 客戶端整合測試

測試 SimpleLarkClient 與其他模組的整合
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from parsers.xml_parser import TestRailXMLParser
from parsers.data_cleaner import TestCaseDataCleaner
from lark.client import SimpleLarkClient, LarkAPIError


class TestLarkIntegration:
    """Lark 客戶端整合測試"""

    def setup_method(self):
        """每個測試方法前的設定"""
        self.app_id = "test_app_id"
        self.app_secret = "test_app_secret"
        self.wiki_token = "test_wiki_token"
        self.table_id = "test_table_id"

    @pytest.mark.integration
    @patch('lark.client.SimpleLarkClient._get_obj_token')
    @patch('lark.client.SimpleLarkClient._get_access_token')
    @patch('lark.client.requests.post')
    def test_complete_xml_to_lark_flow(self, mock_post, mock_get_token, mock_get_obj_token, 
                                     test_data_path, file_test_helper):
        """測試完整的 XML 解析到 Lark 建立流程"""
        # 1. 模擬 Lark API 回應
        mock_get_token.return_value = "test_access_token"
        mock_get_obj_token.return_value = "test_obj_token"
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "data": {
                "records": [
                    {"record_id": "rec001"},
                    {"record_id": "rec002"}
                ]
            }
        }
        mock_post.return_value = mock_response

        # 2. 建立測試 XML 內容
        test_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<suite>
    <sections>
        <section>
            <cases>
                <case>
                    <id>C001</id>
                    <title>TCG001.002.003 **重要**測試案例</title>
                    <priority>High</priority>
                    <custom>
                        <preconds>**重要**前置條件</preconds>
                        <steps>1. 執行*測試*步驟
2. 檢查[結果](http://example.com)</steps>
                        <expected>看到**成功**結果</expected>
                    </custom>
                </case>
                <case>
                    <id>C002</id>
                    <title>TCG004.005.006 另一個測試案例</title>
                    <priority>Medium</priority>
                    <custom>
                        <preconds>另一個前置條件</preconds>
                        <steps>另一個測試步驟</steps>
                        <expected>另一個預期結果</expected>
                    </custom>
                </case>
            </cases>
        </section>
    </sections>
</suite>'''
        
        # 3. 建立臨時 XML 檔案
        temp_file = file_test_helper.create_temp_file(test_xml, "integration_test.xml")
        
        # 4. 初始化所有組件
        xml_parser = TestRailXMLParser()
        data_cleaner = TestCaseDataCleaner()
        lark_client = SimpleLarkClient(self.app_id, self.app_secret)
        lark_client.set_table_info(self.wiki_token, self.table_id)
        
        # 5. 執行完整流程
        # 步驟 1: XML 解析
        raw_cases = xml_parser.parse_xml_file(str(temp_file))
        
        # 步驟 2: 資料清理
        cleaned_cases = []
        for raw_case in raw_cases:
            cleaned_case = data_cleaner.clean_test_case_fields(raw_case)
            cleaned_cases.append(cleaned_case)
        
        # 步驟 3: 寫入 Lark
        success, record_ids = lark_client.batch_create_records(cleaned_cases)
        
        # 6. 驗證結果
        assert len(raw_cases) == 2, "應解析出兩個測試案例"
        assert len(cleaned_cases) == 2, "應清理兩個測試案例"
        assert success is True, "Lark 寫入應成功"
        assert record_ids == ["rec001", "rec002"], "應回傳正確的記錄 ID"
        
        # 驗證資料清理效果
        assert cleaned_cases[0]["test_case_number"] == "TCG-001.002.003"
        assert cleaned_cases[0]["title"] == "重要測試案例"  # Markdown 已清理
        assert cleaned_cases[0]["precondition"] == "重要前置條件"  # Markdown 已清理
        assert "執行測試步驟" in cleaned_cases[0]["steps"]  # Markdown 已清理
        assert "檢查結果" in cleaned_cases[0]["steps"]  # URL 文字已提取
        
        # 驗證 Lark API 調用
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        
        # 檢查轉換為 Lark 格式
        assert "records" in payload
        assert len(payload["records"]) == 2
        
        # 檢查第一筆記錄的欄位格式
        first_record = payload["records"][0]
        assert "fields" in first_record
        fields = first_record["fields"]
        assert "測試案例編號" in fields
        assert "標題" in fields
        assert "優先級" in fields
        assert "前置條件" in fields
        assert "測試步驟" in fields
        assert "預期結果" in fields

    @pytest.mark.integration
    def test_lark_client_with_real_xml_data(self, test_data_path):
        """測試 Lark 客戶端與真實 XML 資料的整合"""
        xml_file = test_data_path / "xml" / "sample_basic.xml"
        
        # 初始化組件
        xml_parser = TestRailXMLParser()
        data_cleaner = TestCaseDataCleaner()
        lark_client = SimpleLarkClient(self.app_id, self.app_secret)
        
        # 解析和清理資料
        raw_cases = xml_parser.parse_xml_file(str(xml_file))
        cleaned_cases = []
        
        for raw_case in raw_cases:
            cleaned_case = data_cleaner.clean_test_case_fields(raw_case)
            cleaned_cases.append(cleaned_case)
        
        # 驗證資料格式符合 Lark 要求
        for case in cleaned_cases:
            assert lark_client._validate_record_format(case), "清理後的資料應符合 Lark 格式要求"

    @pytest.mark.integration
    @patch('lark.client.SimpleLarkClient._get_obj_token')
    def test_lark_client_error_handling_integration(self, mock_get_obj_token, file_test_helper):
        """測試整合流程中的錯誤處理"""
        # 模擬無法獲取 Obj Token
        mock_get_obj_token.return_value = None
        
        # 建立簡單的測試 XML
        test_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<suite>
    <sections>
        <section>
            <cases>
                <case>
                    <id>C001</id>
                    <title>TCG-001.002.003 測試案例</title>
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
        
        temp_file = file_test_helper.create_temp_file(test_xml, "error_test.xml")
        
        # 執行解析和清理
        xml_parser = TestRailXMLParser()
        data_cleaner = TestCaseDataCleaner()
        
        raw_cases = xml_parser.parse_xml_file(str(temp_file))
        cleaned_cases = []
        for raw_case in raw_cases:
            cleaned_case = data_cleaner.clean_test_case_fields(raw_case)
            cleaned_cases.append(cleaned_case)
        
        # 嘗試寫入 Lark（應該失敗）
        lark_client = SimpleLarkClient(self.app_id, self.app_secret)
        
        # 設定資料表資訊應該失敗
        result = lark_client.set_table_info(self.wiki_token, self.table_id)
        assert result is False, "設定資料表資訊應該失敗"
        
        # 批次建立記錄應該拋出異常
        with pytest.raises(LarkAPIError, match="無法獲取 Obj Token"):
            lark_client.batch_create_records(cleaned_cases)

    @pytest.mark.integration
    @patch('lark.client.SimpleLarkClient._get_obj_token')
    @patch('lark.client.SimpleLarkClient._get_access_token')
    @patch('lark.client.requests.get')
    def test_lark_connection_test_integration(self, mock_get, mock_get_token, mock_get_obj_token, 
                                            test_data_path):
        """測試 Lark 連接測試與其他模組的整合"""
        # 模擬成功的連接測試
        mock_get_token.return_value = "test_access_token"
        mock_get_obj_token.return_value = "test_obj_token"
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 0}
        mock_get.return_value = mock_response
        
        # 初始化 Lark 客戶端
        lark_client = SimpleLarkClient(self.app_id, self.app_secret)
        lark_client.set_table_info(self.wiki_token, self.table_id)
        
        # 測試連接
        connection_result = lark_client.test_connection()
        assert connection_result is True, "連接測試應該成功"
        
        # 使用真實資料測試驗證功能
        xml_file = test_data_path / "xml" / "sample_basic.xml"
        xml_parser = TestRailXMLParser()
        data_cleaner = TestCaseDataCleaner()
        
        raw_cases = xml_parser.parse_xml_file(str(xml_file))
        cleaned_cases = []
        
        for raw_case in raw_cases:
            cleaned_case = data_cleaner.clean_test_case_fields(raw_case)
            # 驗證每個清理後的案例都符合 Lark 格式
            assert lark_client._validate_record_format(cleaned_case)
            cleaned_cases.append(cleaned_case)
        
        # 確認有處理到資料
        assert len(cleaned_cases) > 0, "應該有清理後的測試案例"

    @pytest.mark.integration
    def test_data_format_consistency(self, test_data_path):
        """測試資料格式一致性（XML -> 清理 -> Lark）"""
        xml_file = test_data_path / "xml" / "sample_basic.xml"
        
        # 初始化組件
        xml_parser = TestRailXMLParser()
        data_cleaner = TestCaseDataCleaner()
        lark_client = SimpleLarkClient(self.app_id, self.app_secret)
        
        # 獲取統計資訊
        parser_stats = xml_parser.get_parser_stats()
        cleaner_stats = data_cleaner.get_cleaner_stats()
        
        # 驗證統計資訊格式
        assert "parser_type" in parser_stats
        assert "supported_formats" in parser_stats
        assert "cleaner_type" in cleaner_stats
        assert "supported_formats" in cleaner_stats
        
        # 解析和清理資料
        raw_cases = xml_parser.parse_xml_file(str(xml_file))
        cleaned_cases = []
        
        for raw_case in raw_cases:
            # 驗證原始資料格式
            assert "id" in raw_case
            assert "title" in raw_case
            assert "priority" in raw_case
            
            # 清理資料
            cleaned_case = data_cleaner.clean_test_case_fields(raw_case)
            
            # 驗證清理後的資料格式
            assert "test_case_number" in cleaned_case
            assert "title" in cleaned_case
            assert "priority" in cleaned_case
            assert "precondition" in cleaned_case
            assert "steps" in cleaned_case
            assert "expected_result" in cleaned_case
            
            # 驗證符合 Lark 格式要求
            assert lark_client._validate_record_format(cleaned_case)
            
            cleaned_cases.append(cleaned_case)
        
        # 確認資料處理的完整性
        assert len(raw_cases) == len(cleaned_cases), "資料處理前後數量應一致"