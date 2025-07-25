"""
完整的 Lark 客戶端單元測試

包含所有方法的測試以達到足夠的覆蓋率
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import RequestException, Timeout

from lark.client import SimpleLarkClient, LarkAPIError


class TestSimpleLarkClientComplete:
    """SimpleLarkClient 完整測試"""

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

    def test_init_invalid_params(self):
        """測試無效參數初始化"""
        with pytest.raises(ValueError, match="App ID 不能為空"):
            SimpleLarkClient("", self.app_secret)
        
        with pytest.raises(ValueError, match="App Secret 不能為空"):
            SimpleLarkClient(self.app_id, "")
        
        with pytest.raises(ValueError, match="App ID 不能為空"):
            SimpleLarkClient(None, self.app_secret)

    @patch('lark.client.requests.post')
    def test_get_access_token_success(self, mock_post):
        """測試成功獲取 access token"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "tenant_access_token": "test_token",
            "expire": 7200
        }
        mock_post.return_value = mock_response

        client = SimpleLarkClient(self.app_id, self.app_secret)
        token = client._get_access_token()

        assert token == "test_token"
        assert client._tenant_access_token == "test_token"

    @patch('lark.client.requests.post')
    def test_get_access_token_cached(self, mock_post):
        """測試快取的 access token"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "tenant_access_token": "test_token",
            "expire": 7200
        }
        mock_post.return_value = mock_response

        client = SimpleLarkClient(self.app_id, self.app_secret)
        
        # 第一次獲取
        token1 = client._get_access_token()
        # 第二次獲取（應該使用快取）
        token2 = client._get_access_token()

        assert token1 == token2
        assert mock_post.call_count == 1  # 只調用一次

    @patch('lark.client.requests.post')
    def test_get_access_token_force_refresh(self, mock_post):
        """測試強制刷新 access token"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "tenant_access_token": "test_token",
            "expire": 7200
        }
        mock_post.return_value = mock_response

        client = SimpleLarkClient(self.app_id, self.app_secret)
        
        # 第一次獲取
        token1 = client._get_access_token()
        # 強制刷新
        token2 = client._get_access_token(force_refresh=True)

        assert token1 == token2
        assert mock_post.call_count == 2  # 調用兩次

    @patch('lark.client.requests.post')
    def test_get_access_token_http_error(self, mock_post):
        """測試 HTTP 錯誤"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response
        
        client = SimpleLarkClient(self.app_id, self.app_secret)
        
        with pytest.raises(LarkAPIError, match="Token 獲取失敗"):
            client._get_access_token()

    @patch('lark.client.requests.post')
    def test_get_access_token_api_error(self, mock_post):
        """測試 API 錯誤"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 99991663,
            "msg": "app not found"
        }
        mock_post.return_value = mock_response

        client = SimpleLarkClient(self.app_id, self.app_secret)
        
        with pytest.raises(LarkAPIError, match="Lark API 認證失敗"):
            client._get_access_token()

    @patch('lark.client.requests.post')
    def test_get_access_token_timeout(self, mock_post):
        """測試請求超時"""
        mock_post.side_effect = Timeout("請求超時")

        client = SimpleLarkClient(self.app_id, self.app_secret)
        
        with pytest.raises(LarkAPIError, match="請求超時"):
            client._get_access_token()

    @patch('lark.client.requests.post')
    def test_get_access_token_network_error(self, mock_post):
        """測試網路錯誤"""
        mock_post.side_effect = RequestException("網路連接失敗")

        client = SimpleLarkClient(self.app_id, self.app_secret)
        
        with pytest.raises(LarkAPIError, match="網路請求失敗"):
            client._get_access_token()

    @patch('lark.client.SimpleLarkClient._get_access_token')
    @patch('lark.client.requests.get')
    def test_get_obj_token_success(self, mock_get, mock_get_token):
        """測試成功獲取 Obj Token"""
        mock_get_token.return_value = "test_access_token"
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "data": {
                "node": {
                    "obj_token": "test_obj_token"
                }
            }
        }
        mock_get.return_value = mock_response

        client = SimpleLarkClient(self.app_id, self.app_secret)
        obj_token = client._get_obj_token(self.wiki_token)

        assert obj_token == "test_obj_token"
        assert self.wiki_token in client._obj_token_cache

    @patch('lark.client.SimpleLarkClient._get_access_token')
    @patch('lark.client.requests.get')
    def test_get_obj_token_cached(self, mock_get, mock_get_token):
        """測試快取的 Obj Token"""
        client = SimpleLarkClient(self.app_id, self.app_secret)
        client._obj_token_cache[self.wiki_token] = "cached_obj_token"
        
        obj_token = client._get_obj_token(self.wiki_token)
        
        assert obj_token == "cached_obj_token"
        assert mock_get.call_count == 0  # 不應該發送請求

    @patch('lark.client.SimpleLarkClient._get_access_token')
    @patch('lark.client.requests.get')
    def test_get_obj_token_http_error(self, mock_get, mock_get_token):
        """測試獲取 Obj Token HTTP 錯誤"""
        mock_get_token.return_value = "test_access_token"
        
        mock_response = Mock()
        mock_response.status_code = 400
        mock_get.return_value = mock_response

        client = SimpleLarkClient(self.app_id, self.app_secret)
        obj_token = client._get_obj_token(self.wiki_token)

        assert obj_token is None

    @patch('lark.client.SimpleLarkClient._get_access_token')
    @patch('lark.client.requests.get')
    def test_get_obj_token_api_error(self, mock_get, mock_get_token):
        """測試獲取 Obj Token API 錯誤"""
        mock_get_token.return_value = "test_access_token"
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 1254005,
            "msg": "invalid token"
        }
        mock_get.return_value = mock_response

        client = SimpleLarkClient(self.app_id, self.app_secret)
        obj_token = client._get_obj_token(self.wiki_token)

        assert obj_token is None

    @patch('lark.client.SimpleLarkClient._get_access_token')
    @patch('lark.client.requests.get')
    def test_get_obj_token_exception(self, mock_get, mock_get_token):
        """測試獲取 Obj Token 異常"""
        mock_get_token.side_effect = Exception("測試異常")

        client = SimpleLarkClient(self.app_id, self.app_secret)
        obj_token = client._get_obj_token(self.wiki_token)

        assert obj_token is None

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

    @patch('lark.client.SimpleLarkClient._get_obj_token')
    def test_set_table_info_failure(self, mock_get_obj_token):
        """測試設定資料表資訊失敗"""
        mock_get_obj_token.return_value = None
        
        client = SimpleLarkClient(self.app_id, self.app_secret)
        result = client.set_table_info(self.wiki_token, self.table_id)
        
        assert result is False

    def test_set_table_info_invalid_params(self):
        """測試無效參數設定"""
        client = SimpleLarkClient(self.app_id, self.app_secret)
        
        with pytest.raises(ValueError, match="Wiki Token 不能為空"):
            client.set_table_info("", self.table_id)
        
        with pytest.raises(ValueError, match="Table ID 不能為空"):
            client.set_table_info(self.wiki_token, "")

    @patch('lark.client.SimpleLarkClient._get_obj_token')
    @patch('lark.client.SimpleLarkClient._get_access_token')
    @patch('lark.client.requests.get')
    def test_test_connection_success(self, mock_get, mock_get_token, mock_get_obj_token):
        """測試成功連接"""
        mock_get_token.return_value = "test_access_token"
        mock_get_obj_token.return_value = "test_obj_token"
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 0}
        mock_get.return_value = mock_response

        client = SimpleLarkClient(self.app_id, self.app_secret)
        client.set_table_info(self.wiki_token, self.table_id)
        
        result = client.test_connection()
        assert result is True

    @patch('lark.client.SimpleLarkClient._get_obj_token')
    @patch('lark.client.SimpleLarkClient._get_access_token')
    @patch('lark.client.requests.get')
    def test_test_connection_without_obj_token(self, mock_get, mock_get_token, mock_get_obj_token):
        """測試沒有 Obj Token 的連接"""
        mock_get_token.return_value = "test_access_token"
        mock_get_obj_token.return_value = "test_obj_token"  # 用於重新獲取
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 0}
        mock_get.return_value = mock_response

        client = SimpleLarkClient(self.app_id, self.app_secret)
        client.wiki_token = self.wiki_token
        client.table_id = self.table_id
        client._obj_token = None  # 清空 obj_token
        
        result = client.test_connection()
        assert result is True

    @patch('lark.client.SimpleLarkClient._get_access_token')
    def test_test_connection_no_token(self, mock_get_token):
        """測試無法獲取 Token 的連接"""
        mock_get_token.return_value = None
        
        client = SimpleLarkClient(self.app_id, self.app_secret)
        client.wiki_token = self.wiki_token
        client.table_id = self.table_id
        
        result = client.test_connection()
        assert result is False

    @patch('lark.client.SimpleLarkClient._get_obj_token')
    @patch('lark.client.SimpleLarkClient._get_access_token')
    def test_test_connection_no_obj_token(self, mock_get_token, mock_get_obj_token):
        """測試無法獲取 Obj Token 的連接"""
        mock_get_token.return_value = "test_access_token"
        mock_get_obj_token.return_value = None
        
        client = SimpleLarkClient(self.app_id, self.app_secret)
        client.wiki_token = self.wiki_token
        client.table_id = self.table_id
        client._obj_token = None
        
        result = client.test_connection()
        assert result is False

    def test_test_connection_no_table_info(self):
        """測試未設定資料表資訊的連接測試"""
        client = SimpleLarkClient(self.app_id, self.app_secret)
        
        with pytest.raises(ValueError, match="請先設定資料表資訊"):
            client.test_connection()

    @patch('lark.client.SimpleLarkClient._get_obj_token')
    @patch('lark.client.SimpleLarkClient._get_access_token')
    @patch('lark.client.requests.get')
    def test_test_connection_api_error(self, mock_get, mock_get_token, mock_get_obj_token):
        """測試連接 API 錯誤"""
        mock_get_token.return_value = "test_access_token"
        mock_get_obj_token.return_value = "test_obj_token"
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 1254005, "msg": "invalid token"}
        mock_get.return_value = mock_response

        client = SimpleLarkClient(self.app_id, self.app_secret)
        client.set_table_info(self.wiki_token, self.table_id)
        
        result = client.test_connection()
        assert result is False

    @patch('lark.client.SimpleLarkClient._get_obj_token')
    @patch('lark.client.SimpleLarkClient._get_access_token')
    @patch('lark.client.requests.get')
    def test_test_connection_http_error(self, mock_get, mock_get_token, mock_get_obj_token):
        """測試連接 HTTP 錯誤"""
        mock_get_token.return_value = "test_access_token"
        mock_get_obj_token.return_value = "test_obj_token"
        
        mock_response = Mock()
        mock_response.status_code = 400
        mock_get.return_value = mock_response

        client = SimpleLarkClient(self.app_id, self.app_secret)
        client.set_table_info(self.wiki_token, self.table_id)
        
        result = client.test_connection()
        assert result is False

    @patch('lark.client.SimpleLarkClient._get_obj_token')
    @patch('lark.client.SimpleLarkClient._get_access_token')
    @patch('lark.client.requests.get')
    def test_test_connection_exception(self, mock_get, mock_get_token, mock_get_obj_token):
        """測試連接異常"""
        mock_get_token.return_value = "test_access_token"
        mock_get_obj_token.return_value = "test_obj_token"
        mock_get.side_effect = Exception("測試異常")

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

    def test_batch_create_records_no_table_info(self):
        """測試未設定資料表資訊的批次建立"""
        client = SimpleLarkClient(self.app_id, self.app_secret)
        
        with pytest.raises(ValueError, match="請先設定資料表資訊"):
            client.batch_create_records([])

    def test_batch_create_records_empty_records(self):
        """測試空記錄列表"""
        client = SimpleLarkClient(self.app_id, self.app_secret)
        client.wiki_token = self.wiki_token
        client.table_id = self.table_id
        
        with pytest.raises(ValueError, match="記錄列表不能為空"):
            client.batch_create_records([])

    @patch('lark.client.SimpleLarkClient._get_obj_token')
    def test_batch_create_records_no_obj_token(self, mock_get_obj_token):
        """測試無法獲取 Obj Token"""
        mock_get_obj_token.return_value = None
        
        client = SimpleLarkClient(self.app_id, self.app_secret)
        client.wiki_token = self.wiki_token
        client.table_id = self.table_id
        
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
        
        with pytest.raises(LarkAPIError, match="無法獲取 Obj Token"):
            client.batch_create_records(test_records)

    def test_batch_create_records_invalid_record(self):
        """測試無效記錄格式"""
        client = SimpleLarkClient(self.app_id, self.app_secret)
        client.wiki_token = self.wiki_token
        client.table_id = self.table_id
        client._obj_token = "test_obj_token"
        
        invalid_records = [
            {
                "test_case_number": "",  # 空編號
                "title": "測試案例1",
                "priority": "High"
            }
        ]
        
        with pytest.raises(ValueError, match="記錄 1 缺少必要欄位或格式錯誤"):
            client.batch_create_records(invalid_records)

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
        
        result = client._validate_record_format(valid_record)
        assert result is True

    def test_validate_record_format_missing_field(self):
        """測試缺少必要欄位"""
        client = SimpleLarkClient(self.app_id, self.app_secret)
        
        invalid_record = {
            "test_case_number": "TCG-001.002.003",
            "priority": "High"
            # 缺少其他必要欄位
        }
        
        result = client._validate_record_format(invalid_record)
        assert result is False

    def test_validate_record_format_empty_critical_field(self):
        """測試關鍵欄位為空"""
        client = SimpleLarkClient(self.app_id, self.app_secret)
        
        invalid_record = {
            "test_case_number": "",  # 空的關鍵欄位
            "title": "測試案例",
            "priority": "High",
            "precondition": "前置條件",
            "steps": "測試步驟",
            "expected_result": "預期結果"
        }
        
        result = client._validate_record_format(invalid_record)
        assert result is False

    @patch('lark.client.time.sleep')
    def test_wait_for_rate_limit(self, mock_sleep):
        """測試 Rate Limit 等待"""
        client = SimpleLarkClient(self.app_id, self.app_secret)
        
        # 設定 Rate Limit 已用完
        client.rate_limit_remaining = 0
        
        client._wait_for_rate_limit()
        
        # 應該會等待並重置
        mock_sleep.assert_called_once()
        assert client.rate_limit_remaining == client.rate_limit_max

    def test_consume_rate_limit(self):
        """測試消耗 Rate Limit"""
        client = SimpleLarkClient(self.app_id, self.app_secret)
        original_remaining = client.rate_limit_remaining
        
        client._consume_rate_limit(5)
        
        assert client.rate_limit_remaining == original_remaining - 5

    def test_reset_rate_limit(self):
        """測試重置 Rate Limit"""
        client = SimpleLarkClient(self.app_id, self.app_secret)
        
        # 消耗一些額度
        client.rate_limit_remaining = 50
        
        # 重置
        client._reset_rate_limit()
        
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