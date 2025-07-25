"""
Lark 客戶端模組

提供穩定的 Lark API 客戶端，基於 jira_sync_v3 的成功實作
專注於批次資料寫入功能，優化為 TestRail 轉換器專用版本
"""

import logging
import time
import requests
import threading
from typing import Dict, List, Tuple, Any, Optional
from requests.exceptions import RequestException, Timeout
from datetime import datetime, timedelta


class LarkAPIError(Exception):
    """Lark API 呼叫錯誤"""
    pass


class LarkAuthManager:
    """Lark 認證管理器 - 基於 jira_sync_v3 實作"""
    
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        
        # Token 快取
        self._tenant_access_token = None
        self._token_expire_time = None
        self._token_lock = threading.Lock()
        
        # 設定日誌
        self.logger = logging.getLogger(f"{__name__}.LarkAuthManager")
        
        # API 配置
        self.auth_url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
        self.timeout = 30
    
    def get_tenant_access_token(self, force_refresh: bool = False) -> Optional[str]:
        """獲取 Tenant Access Token"""
        with self._token_lock:
            # 檢查是否需要刷新
            if (not force_refresh and 
                self._tenant_access_token and 
                self._token_expire_time and 
                datetime.now() < self._token_expire_time):
                return self._tenant_access_token
            
            # 獲取新 Token
            try:
                response = requests.post(
                    self.auth_url,
                    json={
                        "app_id": self.app_id,
                        "app_secret": self.app_secret
                    },
                    timeout=self.timeout
                )
                
                if response.status_code != 200:
                    self.logger.error(f"Token 獲取失敗，HTTP {response.status_code}")
                    return None
                
                result = response.json()
                
                if result.get('code') != 0:
                    self.logger.error(f"Token 獲取失敗: {result.get('msg')}")
                    return None
                
                # 快取 Token
                self._tenant_access_token = result['tenant_access_token']
                expire_seconds = result.get('expire', 7200)
                self._token_expire_time = datetime.now() + timedelta(seconds=expire_seconds - 300)
                
                return self._tenant_access_token
                
            except Exception as e:
                self.logger.error(f"Token 獲取異常: {e}")
                return None
    
    def is_token_valid(self) -> bool:
        """檢查 Token 是否有效"""
        return (self._tenant_access_token is not None and 
                self._token_expire_time is not None and 
                datetime.now() < self._token_expire_time)


class LarkTableManager:
    """Lark 表格管理器 - 基於 jira_sync_v3 實作"""
    
    def __init__(self, auth_manager: LarkAuthManager):
        self.auth_manager = auth_manager
        
        # 快取
        self._obj_tokens = {}     # wiki_token -> obj_token
        self._cache_lock = threading.Lock()
        
        # 設定日誌
        self.logger = logging.getLogger(f"{__name__}.LarkTableManager")
        
        # API 配置
        self.base_url = "https://open.larksuite.com/open-apis"
        self.timeout = 30
    
    def get_obj_token(self, wiki_token: str) -> Optional[str]:
        """從 Wiki Token 獲取 Obj Token"""
        with self._cache_lock:
            if wiki_token in self._obj_tokens:
                return self._obj_tokens[wiki_token]
        
        try:
            token = self.auth_manager.get_tenant_access_token()
            if not token:
                return None
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            url = f"{self.base_url}/wiki/v2/spaces/get_node?token={wiki_token}"
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code != 200:
                self.logger.error(f"Wiki Token 解析失敗，HTTP {response.status_code}")
                return None
            
            result = response.json()
            if result.get('code') != 0:
                self.logger.error(f"Wiki Token 解析失敗: {result.get('msg')}")
                return None
            
            obj_token = result['data']['node']['obj_token']
            
            # 快取結果
            with self._cache_lock:
                self._obj_tokens[wiki_token] = obj_token
            
            return obj_token
            
        except Exception as e:
            self.logger.error(f"Wiki Token 解析異常: {e}")
            return None


class LarkRecordManager:
    """Lark 記錄管理器 - 基於 jira_sync_v3 實作"""
    
    def __init__(self, auth_manager: LarkAuthManager):
        self.auth_manager = auth_manager
        
        # 設定日誌
        self.logger = logging.getLogger(f"{__name__}.LarkRecordManager")
        
        # API 配置
        self.base_url = "https://open.larksuite.com/open-apis"
        self.timeout = 60
        self.max_page_size = 500
    
    def _make_request(self, method: str, url: str, **kwargs) -> Optional[Dict]:
        """統一的 HTTP 請求方法"""
        try:
            token = self.auth_manager.get_tenant_access_token()
            if not token:
                self.logger.error("無法獲取 Access Token")
                return None
            
            headers = kwargs.pop('headers', {})
            headers.update({
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            })
            
            response = requests.request(
                method, url, 
                headers=headers, 
                timeout=self.timeout,
                **kwargs
            )
            
            if response.status_code != 200:
                self.logger.error(f"API 請求失敗，HTTP {response.status_code}: {response.text}")
                return None
            
            result = response.json()
            
            if result.get('code') != 0:
                error_msg = result.get('msg', 'Unknown error')
                self.logger.error(f"API 請求失敗: {error_msg}")
                return None
            
            return result.get('data', {})
            
        except Exception as e:
            self.logger.error(f"API 請求異常: {e}")
            return None
    
    def batch_create_records(self, obj_token: str, table_id: str, 
                           records_data: List[Dict]) -> Tuple[bool, List[str], List[str]]:
        """批次創建記錄"""
        if not records_data:
            return True, [], []
        
        max_batch_size = 500
        success_ids = []
        error_messages = []
        
        # 分批處理
        for i in range(0, len(records_data), max_batch_size):
            batch_data = records_data[i:i + max_batch_size]
            
            try:
                token = self.auth_manager.get_tenant_access_token()
                if not token:
                    error_messages.append("無法獲取 Access Token")
                    continue
                
                headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
                
                # 準備批次數據
                records = [{'fields': fields} for fields in batch_data]
                data = {'records': records}
                
                url = f"{self.base_url}/bitable/v1/apps/{obj_token}/tables/{table_id}/records/batch_create"
                response = requests.post(url, json=data, headers=headers, timeout=self.timeout)
                
                if response.status_code != 200:
                    error_msg = f"批次創建失敗，HTTP {response.status_code}: {response.text}"
                    error_messages.append(error_msg)
                    continue
                
                result = response.json()
                if result.get('code') != 0:
                    error_msg = f"批次創建失敗: {result.get('msg')}"
                    error_messages.append(error_msg)
                    self.logger.error(f"批次創建失敗詳細資訊 - 錯誤碼: {result.get('code')}, 錯誤訊息: {result.get('msg')}")
                    continue
                
                # 提取成功創建的記錄 ID
                data_section = result.get('data', {})
                records = data_section.get('records', [])
                batch_ids = [record.get('record_id') for record in records if record.get('record_id')]
                success_ids.extend(batch_ids)
                
            except Exception as e:
                error_messages.append(f"批次創建異常: {e}")
        
        overall_success = len(error_messages) == 0
        self.logger.info(f"批次創建完成，成功: {len(success_ids)}, 失敗: {len(error_messages)}")
        
        return overall_success, success_ids, error_messages


class SimpleLarkClient:
    """簡化的 Lark 客戶端，專注於批次資料操作 - 基於穩定的管理器架構"""
    
    def __init__(self, app_id: str, app_secret: str):
        """
        初始化 Lark 客戶端
        
        Args:
            app_id: Lark 應用程式 ID
            app_secret: Lark 應用程式密鑰
            
        Raises:
            ValueError: 當必要參數為空時
        """
        if not app_id:
            raise ValueError("App ID 不能為空")
        if not app_secret:
            raise ValueError("App Secret 不能為空")
        
        self.app_id = app_id
        self.app_secret = app_secret
        self.logger = logging.getLogger(f"{__name__}.SimpleLarkClient")
        
        # 初始化管理器
        self.auth_manager = LarkAuthManager(app_id, app_secret)
        self.table_manager = LarkTableManager(self.auth_manager)
        self.record_manager = LarkRecordManager(self.auth_manager)
        
        # 資料表資訊
        self.wiki_token = None
        self.table_id = None
        self._obj_token = None
        
        self.logger.debug("SimpleLarkClient 初始化完成")
    
    def _get_obj_token(self, wiki_token: str = None) -> Optional[str]:
        """獲取 Obj Token（內部方法）"""
        if wiki_token:
            return self.table_manager.get_obj_token(wiki_token)
        elif self._obj_token:
            return self._obj_token
        elif self.wiki_token:
            obj_token = self.table_manager.get_obj_token(self.wiki_token)
            if obj_token:
                self._obj_token = obj_token
            return obj_token
        else:
            self.logger.error("沒有可用的 Wiki Token")
            return None
    
    def set_table_info(self, wiki_token: str, table_id: str) -> bool:
        """
        設定目標資料表資訊
        
        Args:
            wiki_token: Lark Wiki Token
            table_id: 資料表 ID
            
        Returns:
            設定是否成功
            
        Raises:
            ValueError: 當參數為空時
        """
        if not wiki_token:
            raise ValueError("Wiki Token 不能為空")
        if not table_id:
            raise ValueError("Table ID 不能為空")
        
        self.wiki_token = wiki_token
        self.table_id = table_id
        
        # 立即解析並快取 Obj Token
        self._obj_token = self._get_obj_token(wiki_token)
        if self._obj_token:
            self.logger.debug(f"設定資料表資訊成功: table_id={table_id}")
            return True
        else:
            self.logger.error(f"設定資料表資訊失敗: 無法解析 Wiki Token")
            return False
    
    def test_connection(self) -> bool:
        """
        測試與 Lark API 的連接
        
        Returns:
            連接是否正常
            
        Raises:
            ValueError: 當未設定資料表資訊時
        """
        if not self.wiki_token or not self.table_id:
            raise ValueError("請先設定資料表資訊")
        
        self.logger.debug("正在測試 Lark API 連接")
        
        try:
            # 測試認證
            access_token = self.auth_manager.get_tenant_access_token()
            if not access_token:
                self.logger.error("無法獲取 access token")
                return False
            
            # 確保有 Obj Token
            if not self._obj_token:
                self._obj_token = self._get_obj_token(self.wiki_token)
                if not self._obj_token:
                    self.logger.error("無法解析 Wiki Token")
                    return False
            
            # 測試表格欄位存取（比測試表格資訊更可靠）
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            fields_url = f"https://open.larksuite.com/open-apis/bitable/v1/apps/{self._obj_token}/tables/{self.table_id}/fields"
            response = requests.get(fields_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    fields = result.get('data', {}).get('items', [])
                    self.logger.debug(f"Lark API 連接測試成功，找到 {len(fields)} 個欄位")
                    return True
                else:
                    self.logger.warning(f"Lark API 連接測試失敗: {result.get('msg', '未知錯誤')}")
                    return False
            else:
                self.logger.warning(f"Lark API 連接測試失敗，HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"連接測試失敗: {str(e)}")
            return False
    
    def batch_create_records(self, records: List[Dict]) -> Tuple[bool, List[str]]:
        """
        批次建立記錄到 Lark 資料表（使用穩定的 RecordManager）
        
        Args:
            records: 記錄資料列表，每筆記錄必須包含所有必要欄位
            
        Returns:
            (整體成功狀態, 成功建立的記錄 ID 列表)
            
        Raises:
            ValueError: 當參數無效時
            LarkAPIError: 當 API 呼叫失敗時
        """
        if not self.wiki_token or not self.table_id:
            raise ValueError("請先設定資料表資訊")
        
        if not records:
            raise ValueError("記錄列表不能為空")
        
        if not self._obj_token:
            self._obj_token = self._get_obj_token(self.wiki_token)
            if not self._obj_token:
                raise LarkAPIError("無法獲取 Obj Token")
        
        self.logger.debug(f"開始批次建立 {len(records)} 筆記錄")
        
        # 驗證記錄格式
        for i, record in enumerate(records):
            if not self._validate_record_format(record):
                raise ValueError(f"記錄 {i+1} 缺少必要欄位或格式錯誤")
        
        # 轉換記錄格式為 Lark API 要求的格式（使用英文欄位名）
        lark_records = []
        for record in records:
            lark_record = {
                "Test Case Number": record["test_case_number"],
                "Title": record["title"],
                "Priority": record["priority"],
                "Precondition": record["precondition"],
                "Steps": record["steps"],
                "Expected Result": record["expected_result"]
            }
            lark_records.append(lark_record)
        
        # 使用 RecordManager 進行批次創建
        try:
            success, success_ids, error_messages = self.record_manager.batch_create_records(
                self._obj_token, self.table_id, lark_records
            )
            
            if error_messages:
                error_summary = "; ".join(error_messages[:3])  # 只顯示前3個錯誤
                if len(error_messages) > 3:
                    error_summary += f" (還有 {len(error_messages) - 3} 個錯誤)"
                raise LarkAPIError(f"批次建立記錄失敗: {error_summary}")
            
            return success, success_ids
            
        except Exception as e:
            self.logger.error(f"批次建立記錄異常: {e}")
            raise LarkAPIError(f"批次建立記錄異常: {e}")
    
    def _validate_record_format(self, record: Dict) -> bool:
        """
        驗證記錄格式是否符合要求
        
        Args:
            record: 記錄資料
            
        Returns:
            格式是否有效
        """
        required_fields = [
            "test_case_number", "title", "priority", 
            "precondition", "steps", "expected_result"
        ]
        
        # 檢查必要欄位存在
        for field in required_fields:
            if field not in record:
                return False
        
        # 檢查關鍵欄位不為空
        critical_fields = ["test_case_number", "title", "steps", "expected_result"]
        for field in critical_fields:
            if not record[field] or not str(record[field]).strip():
                return False
        
        return True
    
