"""
CLI 介面模組

提供友善的互動式命令列介面，包括：
- 主選單顯示和選項處理
- 檔案路徑輸入和驗證
- Lark 設定資訊輸入
- 進度顯示和結果展示
"""

import os
import re
import logging
from typing import Dict, Optional, List


class ValidationError(Exception):
    """輸入驗證錯誤"""
    pass


class InteractiveCLI:
    """互動式 CLI 介面"""
    
    def __init__(self):
        """初始化 CLI 介面"""
        self.logger = logging.getLogger(f"{__name__}.InteractiveCLI")
        
        # 檔案大小限制 (100MB)
        self.max_file_size = 100 * 1024 * 1024
        
        # 驗證正則表達式（根據 Lark 實際格式設定）
        self._wiki_token_pattern = re.compile(r'^[a-zA-Z0-9]{20,30}$')
        self._table_id_pattern = re.compile(r'^tbl[a-zA-Z0-9]{10,20}$')
        
        self.logger.debug("InteractiveCLI 初始化完成")
    
    def show_main_menu(self) -> str:
        """
        顯示主選單並取得使用者選擇
        
        Returns:
            使用者選擇的選項 ("convert", "test", "quit")
        """
        while True:
            print("\n" + "="*50)
            print("       TestRail 到 Lark 轉換器")
            print("="*50)
            print("1. 開始轉換")
            print("2. 測試連接")
            print("3. 退出程式")
            print("-"*50)
            
            try:
                choice = input("請選擇操作 (1-3): ").strip()
                
                if choice == "1":
                    return "convert"
                elif choice == "2":
                    return "test"
                elif choice == "3":
                    return "quit"
                else:
                    print(f"❌ 無效的選項: {choice}")
                    print("請輸入 1、2 或 3")
                    
            except KeyboardInterrupt:
                print("\n👋 程式已退出")
                return "quit"
            except Exception as e:
                print(f"❌ 輸入錯誤: {e}")
                continue
    
    def get_file_path_input(self) -> str:
        """
        取得 XML 檔案路徑輸入並驗證
        
        Returns:
            驗證過的檔案絕對路徑
            
        Raises:
            ValidationError: 當檔案驗證失敗時
        """
        print("\n📁 請輸入 TestRail XML 檔案路徑:")
        
        while True:
            try:
                file_path = input("檔案路徑: ").strip()
                
                if not file_path:
                    print("❌ 檔案路徑不能為空")
                    continue
                
                # 檢查檔案是否存在
                if not os.path.exists(file_path):
                    print(f"❌ 檔案不存在: {file_path}")
                    continue
                
                # 檢查檔案副檔名
                if not file_path.lower().endswith('.xml'):
                    print("❌ 必須是 .xml 檔案")
                    continue
                
                # 檢查檔案大小
                file_size = os.path.getsize(file_path)
                if file_size > self.max_file_size:
                    size_mb = file_size / (1024 * 1024)
                    print(f"❌ 檔案過大: {size_mb:.1f}MB (最大限制: 100MB)")
                    continue
                
                # 轉換為絕對路徑
                abs_path = os.path.abspath(file_path)
                print(f"✅ 檔案驗證成功: {abs_path}")
                
                self.logger.info(f"選擇的檔案: {abs_path} ({file_size/1024:.1f}KB)")
                return abs_path
                
            except KeyboardInterrupt:
                print("\n👋 已取消檔案選擇")
                raise ValidationError("使用者取消操作")
            except OSError as e:
                print(f"❌ 檔案存取錯誤: {e}")
                continue
            except Exception as e:
                print(f"❌ 檔案驗證錯誤: {e}")
                continue
    
    def get_multi_file_input(self) -> List[str]:
        """
        取得多個 XML 檔案路徑輸入並驗證
        
        Returns:
            驗證過的檔案絕對路徑列表
            
        Raises:
            ValidationError: 當檔案驗證失敗時
        """
        print("\n📁 請輸入 TestRail XML 檔案路徑:")
        print("   💡 提示: 每行輸入一個檔案路徑，輸入空行結束，或輸入 'q' 取消")
        
        file_paths = []
        
        while True:
            try:
                if len(file_paths) == 0:
                    prompt = "檔案路徑 #1: "
                else:
                    prompt = f"檔案路徑 #{len(file_paths)+1} (空行結束): "
                
                file_path = input(prompt).strip()
                
                # 空行表示結束輸入
                if not file_path:
                    if len(file_paths) == 0:
                        print("❌ 至少需要輸入一個檔案路徑")
                        continue
                    else:
                        break
                
                # 'q' 表示取消
                if file_path.lower() == 'q':
                    print("👋 已取消檔案選擇")
                    raise ValidationError("使用者取消操作")
                
                # 驗證檔案
                if not os.path.exists(file_path):
                    print(f"❌ 檔案不存在: {file_path}")
                    continue
                
                if not file_path.lower().endswith('.xml'):
                    print("❌ 必須是 .xml 檔案")
                    continue
                
                # 檢查檔案大小
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size > self.max_file_size:
                        print(f"❌ 檔案太大: {file_size/1024/1024:.1f}MB (最大限制: {self.max_file_size/1024/1024}MB)")
                        continue
                except OSError as e:
                    print(f"❌ 無法讀取檔案: {e}")
                    continue
                
                # 取得絕對路徑
                abs_path = os.path.abspath(file_path)
                
                # 檢查是否重複
                if abs_path in file_paths:
                    print(f"❌ 檔案已添加: {abs_path}")
                    continue
                
                file_paths.append(abs_path)
                print(f"✅ 檔案驗證成功: {abs_path} ({file_size/1024:.1f}KB)")
                
                self.logger.info(f"添加檔案: {abs_path} ({file_size/1024:.1f}KB)")
                
            except KeyboardInterrupt:
                print("\n👋 已取消檔案選擇")
                raise ValidationError("使用者取消操作")
            except OSError as e:
                print(f"❌ 檔案存取錯誤: {e}")
                continue
            except Exception as e:
                print(f"❌ 檔案驗證錯誤: {e}")
                continue
        
        self.logger.info(f"總共選擇 {len(file_paths)} 個檔案")
        return file_paths
    
    def get_file_mode_choice(self) -> str:
        """
        讓使用者選擇單檔案還是多檔案模式
        
        Returns:
            'single' 或 'multiple'
        """
        print("\n📂 請選擇檔案處理模式:")
        print("1. 單檔案模式")
        print("2. 多檔案模式")
        
        while True:
            try:
                choice = input("請選擇 (1-2): ").strip()
                
                if choice == "1":
                    return "single"
                elif choice == "2":
                    return "multiple"
                else:
                    print("❌ 請輸入 1 或 2")
                    continue
                    
            except KeyboardInterrupt:
                print("\n👋 已取消選擇")
                raise ValidationError("使用者取消操作")
    
    def get_lark_config_input(self) -> Dict[str, str]:
        """
        取得 Lark 設定資訊
        
        Returns:
            包含 wiki_token 和 table_id 的字典
        """
        print("\n🔧 請輸入 Lark 設定資訊:")
        
        # 取得 Wiki Token
        wiki_token = self._get_wiki_token_input()
        
        # 取得 Table ID
        table_id = self._get_table_id_input()
        
        config = {
            "wiki_token": wiki_token,
            "table_id": table_id
        }
        
        print("✅ Lark 設定資訊輸入完成")
        self.logger.info("Lark 設定資訊已收集")
        
        return config
    
    def _get_wiki_token_input(self) -> str:
        """取得 Wiki Token 輸入"""
        while True:
            try:
                wiki_token = input("Wiki Token: ").strip()
                
                if not wiki_token:
                    print("❌ Wiki Token 不能為空")
                    continue
                
                if not self._validate_wiki_token(wiki_token):
                    print("❌ Wiki Token 格式錯誤")
                    print("   格式應為: doc + 24位以上英數字符")
                    print("   範例: doccnG7ZuSaeQhN9BItJnSobGUd")
                    continue
                
                return wiki_token
                
            except KeyboardInterrupt:
                print("\n👋 已取消設定輸入")
                raise ValidationError("使用者取消操作")
    
    def _get_table_id_input(self) -> str:
        """取得 Table ID 輸入"""
        while True:
            try:
                table_id = input("Table ID: ").strip()
                
                if not table_id:
                    print("❌ Table ID 不能為空")
                    continue
                
                if not self._validate_table_id(table_id):
                    print("❌ Table ID 格式錯誤")
                    print("   格式應為: tbl + 13位以上英數字符")
                    print("   範例: tblmVw4gSqKaBGdB")
                    continue
                
                return table_id
                
            except KeyboardInterrupt:
                print("\n👋 已取消設定輸入")
                raise ValidationError("使用者取消操作")
    
    def _validate_wiki_token(self, token: str) -> bool:
        """
        驗證 Wiki Token 格式
        
        Args:
            token: Wiki Token 字串
            
        Returns:
            是否為有效格式
        """
        if not token:
            return False
        
        # 檢查是否符合 Lark Wiki Token 格式
        return bool(self._wiki_token_pattern.match(token))
    
    def _validate_table_id(self, table_id: str) -> bool:
        """
        驗證 Table ID 格式
        
        Args:
            table_id: Table ID 字串
            
        Returns:
            是否為有效格式
        """
        if not table_id:
            return False
        
        # 檢查是否符合 Lark Table ID 格式
        return bool(self._table_id_pattern.match(table_id))
    
    def show_progress(self, current: int, total: int) -> None:
        """
        顯示處理進度
        
        Args:
            current: 目前處理數量
            total: 總數量
        """
        if total == 0:
            percentage = 0
        else:
            percentage = min(100, int((current / total) * 100))
        
        # 創建進度條
        bar_length = 30
        filled_length = int(bar_length * percentage // 100)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        # 顯示進度資訊
        print(f"\r📈 處理進度: [{bar}] {current}/{total} ({percentage}%)", end="", flush=True)
        
        # 如果完成，換行
        if current >= total:
            print()
    
    def show_results(self, success_count: int, error_count: int) -> None:
        """
        顯示處理結果
        
        Args:
            success_count: 成功處理的數量
            error_count: 錯誤的數量
        """
        total_count = success_count + error_count
        
        if total_count == 0:
            success_rate = 0
        else:
            success_rate = int((success_count / total_count) * 100)
        
        print("\n" + "="*50)
        print("             處理完成")
        print("="*50)
        print(f"✅ 成功: {success_count}")
        print(f"❌ 錯誤: {error_count}")
        print(f"📊 成功率: {success_rate}%")
        
        if success_count == total_count and total_count > 0:
            print("🎉 所有資料都已成功處理！")
        elif success_count > 0:
            print("⚠️  部分資料處理成功")
        else:
            print("❌ 沒有資料被成功處理")
        
        print("-"*50)
        
        self.logger.info(f"處理結果: 成功 {success_count}, 錯誤 {error_count}, 成功率 {success_rate}%")