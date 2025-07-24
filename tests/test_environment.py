"""
測試環境驗證測試

驗證測試框架和測試輔助工具是否正常運作
"""

import pytest
import json
from pathlib import Path


class TestEnvironmentSetup:
    """測試環境設定驗證"""

    def test_pytest_configuration(self):
        """測試 pytest 設定是否正確"""
        # 檢查 pytest.ini 是否存在並包含必要設定
        pytest_ini = Path(__file__).parent.parent / "pytest.ini"
        assert pytest_ini.exists(), "pytest.ini 檔案不存在"
        
        content = pytest_ini.read_text(encoding="utf-8")
        assert "testpaths = tests" in content, "pytest 設定缺少 testpaths"
        assert "--color=yes" in content, "pytest 設定缺少顏色輸出"

    def test_fixtures_directory_structure(self, test_data_path):
        """測試 fixtures 目錄結構是否完整"""
        xml_dir = test_data_path / "xml"
        lark_responses_dir = test_data_path / "lark_responses"
        expected_outputs_dir = test_data_path / "expected_outputs"
        
        assert xml_dir.exists(), "XML fixtures 目錄不存在"
        assert lark_responses_dir.exists(), "Lark responses fixtures 目錄不存在"
        assert expected_outputs_dir.exists(), "Expected outputs fixtures 目錄不存在"

    def test_xml_fixtures_availability(self, test_data_path):
        """測試 XML 測試檔案是否可用"""
        xml_dir = test_data_path / "xml"
        
        # 檢查必要的測試檔案
        required_files = [
            "TP-3153 Associated Users Phase 2.xml",
            "sample_basic.xml",
            "malformed.xml",
            "empty.xml",
            "edge_cases.xml"
        ]
        
        for filename in required_files:
            file_path = xml_dir / filename
            assert file_path.exists(), f"測試檔案 {filename} 不存在"
            assert file_path.stat().st_size > 0, f"測試檔案 {filename} 為空"

    def test_lark_response_fixtures(self, test_data_path):
        """測試 Lark API 回應測試資料是否正確"""
        lark_dir = test_data_path / "lark_responses"
        
        # 檢查認證成功回應
        auth_success = lark_dir / "auth_success.json"
        assert auth_success.exists(), "認證成功回應檔案不存在"
        
        with open(auth_success, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data["code"] == 0, "認證成功回應格式錯誤"
        assert "tenant_access_token" in data, "認證成功回應缺少 token"

    def test_expected_output_fixtures(self, test_data_path):
        """測試預期輸出測試資料是否正確"""
        expected_dir = test_data_path / "expected_outputs"
        
        # 檢查清理後測試案例資料
        cleaned_cases = expected_dir / "cleaned_test_cases.json"
        assert cleaned_cases.exists(), "預期輸出檔案不存在"
        
        with open(cleaned_cases, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert isinstance(data, list), "預期輸出格式應為列表"
        assert len(data) > 0, "預期輸出不能為空"
        
        # 檢查第一筆資料格式
        first_case = data[0]
        required_fields = [
            "test_case_number", "title", "priority", 
            "precondition", "steps", "expected_result"
        ]
        
        for field in required_fields:
            assert field in first_case, f"預期輸出缺少必要欄位: {field}"


class TestHelpersUsage:
    """測試輔助工具使用驗證"""

    def test_xml_helper_usage(self, xml_test_helper):
        """測試 XML 輔助工具是否正常運作"""
        # 測試載入 XML fixture
        xml_root = xml_test_helper.load_xml_fixture("sample_basic.xml")
        assert xml_root.tag == "suite", "XML 根元素標籤錯誤"
        
        # 測試建立 XML 元素
        test_elem = xml_test_helper.create_test_xml_element("test", "內容", id="123")
        assert test_elem.tag == "test", "建立的 XML 元素標籤錯誤"
        assert test_elem.text == "內容", "建立的 XML 元素內容錯誤"
        assert test_elem.attrib["id"] == "123", "建立的 XML 元素屬性錯誤"

    def test_lark_helper_usage(self, lark_test_helper):
        """測試 Lark 輔助工具是否正常運作"""
        # 測試載入 Lark 回應資料
        response_data = lark_test_helper.load_lark_response("auth_success.json")
        assert response_data["code"] == 0, "載入的 Lark 回應資料錯誤"
        
        # 測試建立模擬回應
        mock_response = lark_test_helper.create_mock_response(200, {"test": "data"})
        assert mock_response.status_code == 200, "模擬回應狀態碼錯誤"
        assert mock_response.json()["test"] == "data", "模擬回應內容錯誤"

    def test_file_helper_usage(self, file_test_helper):
        """測試檔案輔助工具是否正常運作"""
        # 測試載入預期輸出
        expected_data = file_test_helper.load_expected_output("cleaned_test_cases.json")
        assert isinstance(expected_data, list), "載入的預期輸出格式錯誤"
        
        # 測試建立臨時檔案
        test_content = "測試內容"
        temp_file = file_test_helper.create_temp_file(test_content, "test.txt")
        
        assert temp_file.exists(), "臨時檔案建立失敗"
        assert temp_file.read_text(encoding='utf-8') == test_content, "臨時檔案內容錯誤"

    def test_data_helper_usage(self, data_test_helper):
        """測試資料輔助工具是否正常運作"""
        # 測試建立範例測試案例
        test_case = data_test_helper.create_sample_test_case(
            title="自訂測試案例",
            priority="High"
        )
        
        assert test_case["title"] == "自訂測試案例", "範例測試案例標題錯誤"
        assert test_case["priority"] == "High", "範例測試案例優先級錯誤"
        assert "test_case_number" in test_case, "範例測試案例缺少編號欄位"
        
        # 測試資料比較功能
        expected = {"field1": "value1", "field2": "value2"}
        actual = {"field1": "value1", "field2": "value2", "field3": "value3"}
        
        assert data_test_helper.compare_test_case_data(actual, expected), "資料比較功能錯誤"

    def test_fixtures_integration(self, xml_test_helper, lark_test_helper, 
                                 file_test_helper, data_test_helper):
        """測試輔助工具整合使用"""
        # 載入真實的測試 XML
        xml_root = xml_test_helper.load_xml_fixture("sample_basic.xml")
        
        # 載入對應的預期輸出
        expected_output = file_test_helper.load_expected_output("cleaned_test_cases.json")
        
        # 載入 Lark API 回應資料
        lark_response = lark_test_helper.load_lark_response("batch_create_success.json")
        
        # 驗證資料格式一致性
        assert xml_root is not None, "XML 載入失敗"
        assert len(expected_output) > 0, "預期輸出為空"
        assert lark_response["code"] == 0, "Lark 回應格式錯誤"
        
        # 檢查資料結構相容性
        first_expected = expected_output[0]
        first_lark_record = lark_response["data"]["records"][0]["fields"]
        
        # 主要欄位應該匹配
        for field in ["test_case_number", "title", "priority"]:
            assert field in first_expected, f"預期輸出缺少欄位: {field}"
            assert field in first_lark_record, f"Lark 回應缺少欄位: {field}"


class TestEnvironmentVariables:
    """測試環境變數設定"""

    def test_required_env_vars_set(self):
        """測試必要的環境變數是否已設定"""
        import os
        
        # 檢查測試用環境變數（由 conftest.py 設定）
        assert os.getenv("LARK_APP_ID") == "test_app_id", "測試用 LARK_APP_ID 未正確設定"
        assert os.getenv("LARK_APP_SECRET") == "test_app_secret", "測試用 LARK_APP_SECRET 未正確設定"
        assert os.getenv("LOG_LEVEL") == "DEBUG", "測試用 LOG_LEVEL 未正確設定"

    def test_python_path_configuration(self):
        """測試 Python 路徑設定是否正確"""
        import sys
        from pathlib import Path
        
        project_root = Path(__file__).parent.parent
        src_path = str(project_root / "src")
        
        assert src_path in sys.path, "src 目錄未加入 Python 路徑"