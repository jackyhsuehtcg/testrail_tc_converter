"""
pytest 全域設定檔

提供共用的測試設定和 fixture
"""

import pytest
import os
import sys
from pathlib import Path

# 將 src 目錄加入 Python 路徑
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# 匯入測試輔助工具
from tests.test_helpers import xml_helper, lark_helper, file_helper, data_helper


@pytest.fixture
def project_root_path():
    """提供專案根目錄路徑"""
    return project_root


@pytest.fixture
def test_data_path():
    """提供測試資料目錄路徑"""
    return project_root / "tests" / "fixtures"


@pytest.fixture
def temp_output_path():
    """提供測試輸出目錄路徑"""
    temp_path = project_root / "tests" / "temp"
    temp_path.mkdir(exist_ok=True)
    return temp_path


@pytest.fixture(autouse=True)
def setup_test_environment():
    """自動設定測試環境"""
    # 設定測試用環境變數
    os.environ.setdefault("LARK_APP_ID", "test_app_id")
    os.environ.setdefault("LARK_APP_SECRET", "test_app_secret")
    os.environ.setdefault("LOG_LEVEL", "DEBUG")
    
    yield
    
    # 清理測試環境（如有需要）
    pass


@pytest.fixture
def sample_xml_content():
    """提供範例 XML 內容"""
    return """<?xml version="1.0" encoding="UTF-8"?>
<test_cases>
    <test_case>
        <title>TCG-001.001.001 - 基本登入功能測試</title>
        <description>測試使用者登入功能</description>
    </test_case>
    <test_case>
        <title>TCG001.002.001 - 密碼重設功能測試</title>
        <description>測試使用者密碼重設功能</description>
    </test_case>
</test_cases>"""


@pytest.fixture
def sample_lark_response():
    """提供範例 Lark API 回應"""
    return lark_helper.load_lark_response("batch_create_success.json")


@pytest.fixture
def xml_test_helper():
    """提供 XML 測試輔助工具"""
    return xml_helper


@pytest.fixture
def lark_test_helper():
    """提供 Lark 測試輔助工具"""
    return lark_helper


@pytest.fixture
def file_test_helper():
    """提供檔案測試輔助工具"""
    return file_helper


@pytest.fixture
def data_test_helper():
    """提供資料測試輔助工具"""
    return data_helper


@pytest.fixture(autouse=True, scope="function")
def cleanup_temp_files_after_test():
    """測試完成後自動清理臨時檔案"""
    yield
    file_helper.cleanup_temp_files()