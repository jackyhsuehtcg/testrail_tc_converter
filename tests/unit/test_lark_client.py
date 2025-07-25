"""
Lark 客戶端單元測試

測試 SimpleLarkClient 類別的所有功能
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import RequestException, HTTPError, Timeout

from lark.client import SimpleLarkClient, LarkAPIError


class TestSimpleLarkClient:
    """SimpleLarkClient 單元測試"""

    def setup_method(self):
        """每個測試方法前的設定"""
        self.app_id = "test_app_id"
        self.app_secret = "test_app_secret"
        self.wiki_token = "test_wiki_token"
        self.table_id = "test_table_id"

    def test_init_success(self):
        """測試成功初始化"""
        client = SimpleLarkClient(self.app_id, self.app_secret)
        
        assert client.app_id == self.app_id
        assert client.app_secret == self.app_secret
        assert client._tenant_access_token is None
        assert client.wiki_token is None
        assert client.table_id is None
        assert client.rate_limit_remaining > 0

    def test_init_with_empty_params(self):
        """測試空參數初始化"""
        with pytest.raises(ValueError, match="App ID 不能為空"):
            SimpleLarkClient("", self.app_secret)
        
        with pytest.raises(ValueError, match="App Secret 不能為空"):
            SimpleLarkClient(self.app_id, "")

    def test_init_with_none_params(self):
        """測試 None 參數初始化"""
        with pytest.raises(ValueError, match="App ID 不能為空"):
            SimpleLarkClient(None, self.app_secret)
        
        with pytest.raises(ValueError, match="App Secret 不能為空"):
            SimpleLarkClient(self.app_id, None)

    @patch('lark.client.requests.post')
    def test_get_access_token_success(self, mock_post):
        """測試成功獲取 access token"""
        # 模擬成功回應
        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 0,
            "msg": "success",
            "tenant_access_token": "test_access_token",
            "expire": 7200
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = SimpleLarkClient(self.app_id, self.app_secret)
        token = client._get_access_token()

        assert token == "test_access_token"
        assert client._tenant_access_token == "test_access_token"
        
        # 驗證請求參數
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "auth/v3/tenant_access_token/internal" in call_args[0][0]
        assert call_args[1]["json"]["app_id"] == self.app_id
        assert call_args[1]["json"]["app_secret"] == self.app_secret

    @patch('lark.client.requests.post')
    def test_get_access_token_api_error(self, mock_post):
        """測試 API 回傳錯誤"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 99991663,
            "msg": "app not found"
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = SimpleLarkClient(self.app_id, self.app_secret)
        
        with pytest.raises(LarkAPIError, match="Lark API 認證失敗"):
            client._get_access_token()

    @patch('lark.client.requests.post')
    def test_get_access_token_network_error(self, mock_post):
        """測試網路錯誤"""
        mock_post.side_effect = RequestException("網路連接失敗")

        client = SimpleLarkClient(self.app_id, self.app_secret)
        
        with pytest.raises(LarkAPIError, match="網路請求失敗"):
            client._get_access_token()

    @patch('lark.client.requests.post')
    def test_get_access_token_timeout(self, mock_post):
        """測試請求超時"""
        mock_post.side_effect = Timeout("請求超時")

        client = SimpleLarkClient(self.app_id, self.app_secret)
        
        with pytest.raises(LarkAPIError, match="請求超時"):
            client._get_access_token()

    @patch('lark.client.SimpleLarkClient._get_obj_token')
    def test_set_table_info_success(self, mock_get_obj_token):
        """測試成功設定資料表資訊"""
        mock_get_obj_token.return_value = "test_obj_token"
        
        client = SimpleLarkClient(self.app_id, self.app_secret)
        
        result = client.set_table_info(self.wiki_token, self.table_id)
        
        assert result is True
        assert client.wiki_token == self.wiki_token
        assert client.table_id == self.table_id
        assert client._obj_token == "test_obj_token"

    def test_set_table_info_empty_params(self):
        """測試空參數設定"""
        client = SimpleLarkClient(self.app_id, self.app_secret)
        
        with pytest.raises(ValueError, match="Wiki Token 不能為空"):
            client.set_table_info("", self.table_id)
        
        with pytest.raises(ValueError, match="Table ID 不能為空"):
            client.set_table_info(self.wiki_token, "")

    def test_set_table_info_none_params(self):
        """測試 None 參數設定"""
        client = SimpleLarkClient(self.app_id, self.app_secret)
        
        with pytest.raises(ValueError, match="Wiki Token 不能為空"):
            client.set_table_info(None, self.table_id)
        
        with pytest.raises(ValueError, match="Table ID 不能為空"):
            client.set_table_info(self.wiki_token, None)

    @patch('lark.client.SimpleLarkClient._get_obj_token')
    @patch('lark.client.SimpleLarkClient._get_access_token')
    @patch('lark.client.requests.get')
    def test_test_connection_success(self, mock_get, mock_get_token, mock_get_obj_token):
        """測試成功連接測試"""
        # 模擬成功獲取 token 和 obj_token
        mock_get_token.return_value = "test_access_token"
        mock_get_obj_token.return_value = "test_obj_token"
        
        # 模擬成功的連接測試回應
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "msg": "success"
        }
        mock_get.return_value = mock_response

        client = SimpleLarkClient(self.app_id, self.app_secret)
        client.set_table_info(self.wiki_token, self.table_id)
        
        result = client.test_connection()
        
        assert result is True
        mock_get_token.assert_called()

    @patch('lark.client.SimpleLarkClient._get_access_token')
    def test_test_connection_no_table_info(self, mock_get_token):
        """測試未設定資料表資訊的連接測試"""
        mock_get_token.return_value = "test_access_token"
        
        client = SimpleLarkClient(self.app_id, self.app_secret)
        
        with pytest.raises(ValueError, match="請先設定資料表資訊"):
            client.test_connection()

    @patch('lark.client.SimpleLarkClient._get_obj_token')
    @patch('lark.client.SimpleLarkClient._get_access_token')
    @patch('lark.client.requests.get')
    def test_test_connection_api_error(self, mock_get, mock_get_token, mock_get_obj_token):
        """測試連接失敗"""
        mock_get_token.return_value = "test_access_token"
        mock_get_obj_token.return_value = "test_obj_token"
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 1254005,
            "msg": "invalid token"
        }
        mock_get.return_value = mock_response

        client = SimpleLarkClient(self.app_id, self.app_secret)
        client.set_table_info(self.wiki_token, self.table_id)
        
        result = client.test_connection()
        assert result is False

    @patch('lark.client.SimpleLarkClient._get_obj_token')
    @patch('lark.client.SimpleLarkClient._get_access_token')
    @patch('lark.client.requests.post')
    def test_batch_create_records_success(self, mock_post, mock_get_token, mock_get_obj_token):
        """測試成功批次建立記錄"""
        mock_get_token.return_value = "test_access_token"
        mock_get_obj_token.return_value = "test_obj_token"
        
        # 模擬成功的建立記錄回應
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "msg": "success",
            "data": {
                "records": [
                    {"record_id": "rec001"},
                    {"record_id": "rec002"}
                ]
            }
        }
        mock_post.return_value = mock_response

        client = SimpleLarkClient(self.app_id, self.app_secret)
        client.set_table_info(self.wiki_token, self.table_id)
        
        test_records = [
            {
                "test_case_number": "TCG-001.002.003",
                "title": "測試案例1",
                "priority": "High",
                "precondition": "前置條件",
                "steps": "測試步驟",
                "expected_result": "預期結果"
            },
            {
                "test_case_number": "TCG-004.005.006",
                "title": "測試案例2",
                "priority": "Medium",
                "precondition": "前置條件2",
                "steps": "測試步驟2",
                "expected_result": "預期結果2"
            }
        ]
        
        success, record_ids = client.batch_create_records(test_records)
        
        assert success is True
        assert record_ids == ["rec001", "rec002"]
        mock_get_token.assert_called_once()

    def test_batch_create_records_no_table_info(self):
        """測試未設定資料表資訊的批次建立"""
        client = SimpleLarkClient(self.app_id, self.app_secret)
        
        with pytest.raises(ValueError, match="請先設定資料表資訊"):
            client.batch_create_records([])

    def test_batch_create_records_empty_records(self):
        """測試空記錄列表"""
        client = SimpleLarkClient(self.app_id, self.app_secret)
        client.set_table_info(self.wiki_token, self.table_id)
        
        with pytest.raises(ValueError, match="記錄列表不能為空"):
            client.batch_create_records([])

    def test_batch_create_records_invalid_record(self):
        """測試無效記錄格式"""
        client = SimpleLarkClient(self.app_id, self.app_secret)
        client.set_table_info(self.wiki_token, self.table_id)
        
        invalid_records = [
            {
                "test_case_number": "",  # 空編號
                "title": "測試案例1",
                "priority": "High"
            }
        ]
        
        with pytest.raises(ValueError, match="記錄缺少必要欄位"):
            client.batch_create_records(invalid_records)

    @patch('lark.client.SimpleLarkClient._get_access_token')
    @patch('lark.client.requests.post')
    def test_batch_create_records_large_batch(self, mock_post, mock_get_token):
        """測試大批次記錄（超過500筆的分批處理）"""
        mock_get_token.return_value = "test_access_token"
        
        # 模擬兩次成功的建立記錄回應
        mock_response1 = Mock()
        mock_response1.json.return_value = {
            "code": 0,
            "msg": "success",
            "data": {
                "records": [{"record_id": f"rec{i:03d}"} for i in range(500)]
            }
        }
        mock_response1.raise_for_status.return_value = None
        
        mock_response2 = Mock()
        mock_response2.json.return_value = {
            "code": 0,
            "msg": "success",
            "data": {
                "records": [{"record_id": f"rec{i:03d}"} for i in range(500, 600)]
            }
        }
        mock_response2.raise_for_status.return_value = None
        
        mock_post.side_effect = [mock_response1, mock_response2]

        client = SimpleLarkClient(self.app_id, self.app_secret)
        client.set_table_info(self.wiki_token, self.table_id)
        
        # 建立600筆測試記錄
        test_records = []
        for i in range(600):
            test_records.append({
                "test_case_number": f"TCG-{i:03d}.001.001",
                "title": f"測試案例{i}",
                "priority": "Medium",
                "precondition": f"前置條件{i}",
                "steps": f"測試步驟{i}",
                "expected_result": f"預期結果{i}"
            })
        
        success, record_ids = client.batch_create_records(test_records)
        
        assert success is True
        assert len(record_ids) == 600
        assert mock_post.call_count == 2  # 分成兩次批次請求

    @patch('lark.client.SimpleLarkClient._get_access_token')
    @patch('lark.client.requests.post')
    def test_batch_create_records_api_error(self, mock_post, mock_get_token):
        """測試批次建立記錄 API 錯誤"""
        mock_get_token.return_value = "test_access_token"
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 1254004,
            "msg": "permission denied"
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = SimpleLarkClient(self.app_id, self.app_secret)
        client.set_table_info(self.wiki_token, self.table_id)
        
        test_records = [
            {
                "test_case_number": "TCG-001.002.003",
                "title": "測試案例1",
                "priority": "High",
                "precondition": "前置條件",
                "steps": "測試步驟",
                "expected_result": "預期結果"
            }
        ]
        
        with pytest.raises(LarkAPIError, match="批次建立記錄失敗"):
            client.batch_create_records(test_records)

    def test_validate_record_format_valid(self):
        """測試有效記錄格式驗證"""
        client = SimpleLarkClient(self.app_id, self.app_secret)
        
        valid_record = {
            "test_case_number": "TCG-001.002.003",
            "title": "測試案例",
            "priority": "High",
            "precondition": "前置條件",
            "steps": "測試步驟",
            "expected_result": "預期結果"
        }
        
        # 不應該拋出異常
        result = client._validate_record_format(valid_record)
        assert result is True

    def test_validate_record_format_missing_fields(self):
        """測試缺少必要欄位的記錄"""
        client = SimpleLarkClient(self.app_id, self.app_secret)
        
        # 缺少 title
        invalid_record = {
            "test_case_number": "TCG-001.002.003",
            "priority": "High",
            "precondition": "前置條件",
            "steps": "測試步驟",
            "expected_result": "預期結果"
        }
        
        result = client._validate_record_format(invalid_record)
        assert result is False

    def test_validate_record_format_empty_required_fields(self):
        """測試必要欄位為空的記錄"""
        client = SimpleLarkClient(self.app_id, self.app_secret)
        
        # title 為空
        invalid_record = {
            "test_case_number": "TCG-001.002.003",
            "title": "",
            "priority": "High",
            "precondition": "前置條件",
            "steps": "測試步驟",
            "expected_result": "預期結果"
        }
        
        result = client._validate_record_format(invalid_record)
        assert result is False

    def test_rate_limit_handling(self):
        """測試 Rate Limit 處理"""
        client = SimpleLarkClient(self.app_id, self.app_secret)
        
        # 初始狀態
        assert client.rate_limit_remaining > 0
        
        # 模擬消耗 Rate Limit
        client._consume_rate_limit(10)
        assert client.rate_limit_remaining == client.rate_limit_max - 10
        
        # 模擬重置 Rate Limit
        client._reset_rate_limit()
        assert client.rate_limit_remaining == client.rate_limit_max

    @patch('lark.client.time.sleep')
    def test_rate_limit_wait(self, mock_sleep):
        """測試 Rate Limit 等待機制"""
        client = SimpleLarkClient(self.app_id, self.app_secret)
        
        # 消耗所有 Rate Limit
        client.rate_limit_remaining = 0
        
        # 應該會等待
        client._wait_for_rate_limit()
        mock_sleep.assert_called_once()
        
        # Rate Limit 應該被重置
        assert client.rate_limit_remaining == client.rate_limit_max


class TestLarkAPIError:
    """LarkAPIError 異常測試"""

    def test_lark_api_error_creation(self):
        """測試 LarkAPIError 建立"""
        error_msg = "測試錯誤訊息"
        error = LarkAPIError(error_msg)
        
        assert str(error) == error_msg
        assert isinstance(error, Exception)

    def test_lark_api_error_with_details(self):
        """測試帶詳細資訊的 LarkAPIError"""
        error_msg = "API 呼叫失敗"
        error_code = 1254005
        error = LarkAPIError(f"{error_msg} (錯誤碼: {error_code})")
        
        assert "API 呼叫失敗" in str(error)
        assert "1254005" in str(error)