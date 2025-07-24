"""
專案結構完整性測試

驗證專案目錄結構和基礎檔案是否正確建立
"""

import pytest
from pathlib import Path


class TestProjectStructure:
    """專案結構測試類別"""

    def test_project_directories_exist(self, project_root_path):
        """測試專案目錄是否存在"""
        required_dirs = [
            "src",
            "src/cli", 
            "src/parsers",
            "src/lark",
            "src/utils",
            "tests",
            "tests/unit",
            "tests/integration", 
            "tests/fixtures",
            "config",
            "logs",
            "temp",
            "test_output",
            "plan"
        ]
        
        for dir_name in required_dirs:
            dir_path = project_root_path / dir_name
            assert dir_path.exists(), f"目錄 {dir_name} 不存在"
            assert dir_path.is_dir(), f"{dir_name} 不是目錄"

    def test_init_files_exist(self, project_root_path):
        """測試 __init__.py 檔案是否存在"""
        init_files = [
            "src/__init__.py",
            "src/cli/__init__.py",
            "src/parsers/__init__.py", 
            "src/lark/__init__.py",
            "src/utils/__init__.py",
            "tests/__init__.py",
            "tests/unit/__init__.py",
            "tests/integration/__init__.py"
        ]
        
        for init_file in init_files:
            file_path = project_root_path / init_file
            assert file_path.exists(), f"初始化檔案 {init_file} 不存在"
            assert file_path.is_file(), f"{init_file} 不是檔案"

    def test_config_files_exist(self, project_root_path):
        """測試設定檔案是否存在"""
        config_files = [
            "requirements.txt",
            "config/config.yaml.example",
            "config/logging.yaml",
            "README.md",
            ".gitignore"
        ]
        
        for config_file in config_files:
            file_path = project_root_path / config_file
            assert file_path.exists(), f"設定檔案 {config_file} 不存在"
            assert file_path.is_file(), f"{config_file} 不是檔案"

    def test_gitignore_content(self, project_root_path):
        """測試 .gitignore 內容是否包含必要項目"""
        gitignore_path = project_root_path / ".gitignore"
        content = gitignore_path.read_text(encoding="utf-8")
        
        required_patterns = [
            "__pycache__/",
            "*.py[cod]",  # 修正為實際使用的模式
            "config/config.yaml",
            "logs/",
            "temp/",
            "test_output/",
            ".env"
        ]
        
        for pattern in required_patterns:
            assert pattern in content, f".gitignore 缺少必要的忽略模式: {pattern}"

    def test_requirements_content(self, project_root_path):
        """測試 requirements.txt 內容是否包含必要套件"""
        requirements_path = project_root_path / "requirements.txt"
        content = requirements_path.read_text(encoding="utf-8")
        
        required_packages = [
            "click>=8.0.0",
            "requests>=2.28.0", 
            "PyYAML>=6.0",
            "pytest>=7.0.0"
        ]
        
        for package in required_packages:
            assert package in content, f"requirements.txt 缺少必要套件: {package}"

    def test_src_init_content(self, project_root_path):
        """測試 src/__init__.py 包含版本資訊"""
        init_path = project_root_path / "src" / "__init__.py"
        content = init_path.read_text(encoding="utf-8")
        
        assert "__version__" in content, "src/__init__.py 缺少版本資訊"
        assert "__author__" in content, "src/__init__.py 缺少作者資訊"
        assert "__description__" in content, "src/__init__.py 缺少描述資訊"

    def test_git_initialization(self, project_root_path):
        """測試 Git 版本控制是否初始化"""
        git_path = project_root_path / ".git"
        assert git_path.exists(), "Git 版本控制尚未初始化"
        assert git_path.is_dir(), ".git 不是目錄"