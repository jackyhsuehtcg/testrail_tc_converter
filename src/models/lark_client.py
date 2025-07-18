"""
Lark 多維表格客戶端
純粹的 Lark API 操作模組，不包含業務邏輯
"""

import logging
import requests
import threading
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta


class LarkAuthManager:
    """Lark 認證管理器"""
    
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
                
                self.logger.info("Access Token 獲取成功")
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
    """Lark 表格管理器"""
    
    def __init__(self, auth_manager: LarkAuthManager):
        self.auth_manager = auth_manager
        
        # 快取
        self._obj_tokens = {}
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
            
            self.logger.info(f"Obj Token 獲取成功")
            return obj_token
            
        except Exception as e:
            self.logger.error(f"Wiki Token 解析異常: {e}")
            return None
    
    def get_table_fields(self, obj_token: str, table_id: str) -> List[Dict[str, Any]]:
        """獲取表格欄位資訊"""
        try:
            token = self.auth_manager.get_tenant_access_token()
            if not token:
                return []
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            url = f"{self.base_url}/bitable/v1/apps/{obj_token}/tables/{table_id}/fields"
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code != 200:
                self.logger.error(f"獲取表格欄位失敗，HTTP {response.status_code}")
                return []
            
            result = response.json()
            if result.get('code') != 0:
                self.logger.error(f"獲取表格欄位失敗: {result.get('msg')}")
                return []
            
            fields = result.get('data', {}).get('items', [])
            self.logger.info(f"獲取表格欄位成功: {len(fields)} 個")
            return fields
            
        except Exception as e:
            self.logger.error(f"獲取表格欄位異常: {e}")
            return []
    
    def get_field_names(self, obj_token: str, table_id: str) -> List[str]:
        """獲取表格欄位名稱列表"""
        fields = self.get_table_fields(obj_token, table_id)
        return [field.get('field_name', '') for field in fields if field.get('field_name')]


class LarkRecordManager:
    """Lark 記錄管理器"""
    
    def __init__(self, auth_manager: LarkAuthManager):
        self.auth_manager = auth_manager
        
        # 設定日誌
        self.logger = logging.getLogger(f"{__name__}.LarkRecordManager")
        
        # API 配置
        self.base_url = "https://open.larksuite.com/open-apis"
        self.timeout = 60
    
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
                self.logger.error(f"API 請求失敗: {result.get('msg')}")
                return None
            
            return result.get('data', {})
            
        except Exception as e:
            self.logger.error(f"API 請求異常: {e}")
            return None
    
    def get_all_records(self, obj_token: str, table_id: str) -> List[Dict]:
        """獲取表格所有記錄"""
        url = f"{self.base_url}/bitable/v1/apps/{obj_token}/tables/{table_id}/records"
        
        all_records = []
        page_token = None
        
        while True:
            params = {'page_size': 500}
            if page_token:
                params['page_token'] = page_token
            
            result = self._make_request('GET', url, params=params)
            if not result:
                break
            
            records = result.get('items', [])
            all_records.extend(records)
            
            # 檢查是否還有更多記錄
            page_token = result.get('page_token')
            if not page_token or not result.get('has_more', False):
                break
        
        self.logger.info(f"獲取記錄完成，共 {len(all_records)} 筆")
        return all_records
    
    def create_record(self, obj_token: str, table_id: str, fields: Dict) -> Optional[str]:
        """創建單筆記錄"""
        url = f"{self.base_url}/bitable/v1/apps/{obj_token}/tables/{table_id}/records"
        
        data = {'fields': fields}
        result = self._make_request('POST', url, json=data)
        
        if result:
            record = result.get('record', {})
            record_id = record.get('record_id')
            if record_id:
                self.logger.info(f"創建記錄成功: {record_id}")
            return record_id
        return None
    
    def update_record(self, obj_token: str, table_id: str, record_id: str, fields: Dict) -> bool:
        """更新單筆記錄"""
        url = f"{self.base_url}/bitable/v1/apps/{obj_token}/tables/{table_id}/records/{record_id}"
        
        data = {'fields': fields}
        result = self._make_request('PUT', url, json=data)
        
        if result:
            self.logger.info(f"更新記錄成功: {record_id}")
            return True
        return False
    
    def delete_record(self, obj_token: str, table_id: str, record_id: str) -> bool:
        """刪除單筆記錄"""
        url = f"{self.base_url}/bitable/v1/apps/{obj_token}/tables/{table_id}/records/{record_id}"
        
        result = self._make_request('DELETE', url)
        
        if result:
            self.logger.info(f"刪除記錄成功: {record_id}")
            return True
        return False
    
    def batch_create_records(self, obj_token: str, table_id: str, 
                           records_data: List[Dict]) -> Tuple[bool, List[str], List[str]]:
        """批次創建記錄"""
        if not records_data:
            return True, [], []
        
        max_batch_size = 20
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
                
                # 添加重試機制處理 SSL 錯誤
                max_retries = 3
                response = None
                for retry in range(max_retries):
                    try:
                        response = requests.post(url, json=data, headers=headers, timeout=self.timeout)
                        break
                    except requests.exceptions.SSLError as e:
                        if retry == max_retries - 1:
                            error_msg = f"SSL 錯誤，重試 {max_retries} 次後仍失敗: {e}"
                            error_messages.append(error_msg)
                            response = None
                            break
                        else:
                            self.logger.warning(f"SSL 錯誤，重試 {retry + 1}/{max_retries}: {e}")
                            continue
                    except Exception as e:
                        error_msg = f"請求異常: {e}"
                        error_messages.append(error_msg)
                        response = None
                        break
                
                if response is None:
                    continue
                
                if response.status_code != 200:
                    error_msg = f"批次創建失敗，HTTP {response.status_code}: {response.text}"
                    error_messages.append(error_msg)
                    continue
                
                result = response.json()
                if result.get('code') != 0:
                    error_msg = f"批次創建失敗: {result.get('msg')}"
                    error_messages.append(error_msg)
                    continue
                
                # 提取成功創建的記錄 ID
                data_section = result.get('data', {})
                records = data_section.get('records', [])
                batch_ids = [record.get('record_id') for record in records if record.get('record_id')]
                success_ids.extend(batch_ids)
                
                self.logger.info(f"批次創建成功: {len(batch_ids)} 筆記錄")
                
            except Exception as e:
                error_messages.append(f"批次創建異常: {e}")
        
        overall_success = len(error_messages) == 0
        self.logger.info(f"批次創建完成，成功: {len(success_ids)}, 失敗: {len(error_messages)}")
        
        return overall_success, success_ids, error_messages
    
    def batch_update_records(self, obj_token: str, table_id: str, 
                           updates: List[Tuple[str, Dict]]) -> bool:
        """批次更新記錄"""
        if not updates:
            return True
        
        max_batch_size = 20
        
        # 分批處理
        for i in range(0, len(updates), max_batch_size):
            batch = updates[i:i + max_batch_size]
            
            try:
                token = self.auth_manager.get_tenant_access_token()
                if not token:
                    self.logger.error("無法獲取 Access Token")
                    return False
                
                headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    'records': [
                        {
                            'record_id': record_id,
                            'fields': fields
                        }
                        for record_id, fields in batch
                    ]
                }
                
                url = f"{self.base_url}/bitable/v1/apps/{obj_token}/tables/{table_id}/records/batch_update"
                response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
                
                if response.status_code != 200:
                    self.logger.error(f"批次更新失敗，HTTP {response.status_code}: {response.text}")
                    return False
                
                result = response.json()
                if result.get('code') != 0:
                    self.logger.error(f"批次更新失敗: {result.get('msg')}")
                    return False
                
                self.logger.info(f"批次更新成功: {len(batch)} 筆記錄")
                
            except Exception as e:
                self.logger.error(f"批次更新異常: {e}")
                return False
        
        self.logger.info(f"批次更新完成，總計: {len(updates)} 筆記錄")
        return True
    
    def batch_delete_records(self, obj_token: str, table_id: str, 
                           record_ids: List[str]) -> bool:
        """批次刪除記錄"""
        if not record_ids:
            return True
        
        max_batch_size = 20
        
        # 分批處理
        for i in range(0, len(record_ids), max_batch_size):
            batch_ids = record_ids[i:i + max_batch_size]
            
            try:
                token = self.auth_manager.get_tenant_access_token()
                if not token:
                    self.logger.error("無法獲取 Access Token")
                    return False
                
                headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
                
                data = {'records': batch_ids}
                
                url = f"{self.base_url}/bitable/v1/apps/{obj_token}/tables/{table_id}/records/batch_delete"
                response = requests.post(url, json=data, headers=headers, timeout=self.timeout)
                
                if response.status_code != 200:
                    self.logger.error(f"批次刪除失敗，HTTP {response.status_code}: {response.text}")
                    return False
                
                result = response.json()
                if result.get('code') != 0:
                    self.logger.error(f"批次刪除失敗: {result.get('msg')}")
                    return False
                
                self.logger.info(f"批次刪除成功: {len(batch_ids)} 筆記錄")
                
            except Exception as e:
                self.logger.error(f"批次刪除異常: {e}")
                return False
        
        self.logger.info(f"批次刪除完成，總計: {len(record_ids)} 筆記錄")
        return True


class LarkClient:
    """Lark 多維表格客戶端"""
    
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        
        # 設定日誌
        self.logger = logging.getLogger(f"{__name__}.LarkClient")
        
        # 初始化管理器
        self.auth_manager = LarkAuthManager(app_id, app_secret)
        self.table_manager = LarkTableManager(self.auth_manager)
        self.record_manager = LarkRecordManager(self.auth_manager)
        
        self.logger.info("Lark 客戶端初始化完成")
    
    def test_connection(self) -> bool:
        """測試連接"""
        try:
            token = self.auth_manager.get_tenant_access_token()
            return token is not None
        except Exception as e:
            self.logger.error(f"連接測試失敗: {e}")
            return False
    
    def get_obj_token(self, wiki_token: str) -> Optional[str]:
        """獲取 Obj Token"""
        return self.table_manager.get_obj_token(wiki_token)
    
    def get_table_fields(self, obj_token: str, table_id: str) -> List[Dict[str, Any]]:
        """獲取表格欄位資訊"""
        return self.table_manager.get_table_fields(obj_token, table_id)
    
    def get_field_names(self, obj_token: str, table_id: str) -> List[str]:
        """獲取表格欄位名稱"""
        return self.table_manager.get_field_names(obj_token, table_id)
    
    def get_all_records(self, obj_token: str, table_id: str) -> List[Dict]:
        """獲取所有記錄"""
        return self.record_manager.get_all_records(obj_token, table_id)
    
    def create_record(self, obj_token: str, table_id: str, fields: Dict) -> Optional[str]:
        """創建記錄"""
        return self.record_manager.create_record(obj_token, table_id, fields)
    
    def update_record(self, obj_token: str, table_id: str, record_id: str, fields: Dict) -> bool:
        """更新記錄"""
        return self.record_manager.update_record(obj_token, table_id, record_id, fields)
    
    def delete_record(self, obj_token: str, table_id: str, record_id: str) -> bool:
        """刪除記錄"""
        return self.record_manager.delete_record(obj_token, table_id, record_id)
    
    def batch_create_records(self, obj_token: str, table_id: str, 
                           records_data: List[Dict]) -> Tuple[bool, List[str], List[str]]:
        """批次創建記錄"""
        return self.record_manager.batch_create_records(obj_token, table_id, records_data)
    
    def batch_update_records(self, obj_token: str, table_id: str, 
                           updates: List[Tuple[str, Dict]]) -> bool:
        """批次更新記錄"""
        return self.record_manager.batch_update_records(obj_token, table_id, updates)
    
    def batch_delete_records(self, obj_token: str, table_id: str, 
                           record_ids: List[str]) -> bool:
        """批次刪除記錄"""
        return self.record_manager.batch_delete_records(obj_token, table_id, record_ids)
    
    def get_status(self) -> Dict[str, Any]:
        """獲取客戶端狀態"""
        return {
            'connection_valid': self.auth_manager.is_token_valid(),
            'client_type': 'LarkClient',
            'app_id': self.app_id[:8] + '...' if len(self.app_id) > 8 else self.app_id
        }