"""
簡化的 Lark 客戶端單元測試

測試核心功能是否正常運作
"""

import pytest
from unittest.mock import Mock, patch

from lark.client import SimpleLarkClient, LarkAPIError


class TestSimpleLarkClientCore:
    """SimpleLarkClient 核心功能測試"""

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

    def test_init_invalid_params(self):
        """測試無效參數初始化"""
        with pytest.raises(ValueError, match="App ID 不能為空"):
            SimpleLarkClient("", self.app_secret)
        
        with pytest.raises(ValueError, match="App Secret 不能為空"):
            SimpleLarkClient(self.app_id, "")

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
    def test_get_access_token_error(self, mock_post):
        """測試獲取 token 失敗"""
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

    @patch('lark.client.SimpleLarkClient._get_obj_token')
    def test_set_table_info_success(self, mock_get_obj_token):
        """測試成功設定資料表資訊"""
        mock_get_obj_token.return_value = "test_obj_token"
        
        client = SimpleLarkClient(self.app_id, self.app_secret)
        result = client.set_table_info(self.wiki_token, self.table_id)
        
        assert result is True
        assert client.wiki_token == self.wiki_token
        assert client.table_id == self.table_id

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

    def test_test_connection_no_table_info(self):
        """測試未設定資料表資訊的連接測試"""
        client = SimpleLarkClient(self.app_id, self.app_secret)
        
        with pytest.raises(ValueError, match="請先設定資料表資訊"):
            client.test_connection()

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

    def test_validate_record_format_invalid(self):
        """測試無效記錄格式"""
        client = SimpleLarkClient(self.app_id, self.app_secret)
        
        # 缺少必要欄位
        invalid_record = {
            "test_case_number": "TCG-001.002.003",
            "priority": "High"
        }
        
        result = client._validate_record_format(invalid_record)
        assert result is False

    def test_rate_limit_handling(self):
        """測試 Rate Limit 處理"""
        client = SimpleLarkClient(self.app_id, self.app_secret)
        
        # 初始狀態
        assert client.rate_limit_remaining > 0
        
        # 消耗 Rate Limit
        client._consume_rate_limit(10)
        assert client.rate_limit_remaining == client.rate_limit_max - 10
        
        # 重置 Rate Limit
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