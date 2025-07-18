"""
TestRail 資料模型定義
支援階層式 section 和 sub-section 結構
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class Priority(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class CaseType(Enum):
    ACCEPTANCE = "Acceptance"
    ACCESSIBILITY = "Accessibility"
    AUTOMATED = "Automated"
    COMPATIBILITY = "Compatibility"
    DESTRUCTIVE = "Destructive"
    FUNCTIONAL = "Functional"
    OTHER = "Other"
    PERFORMANCE = "Performance"
    REGRESSION = "Regression"
    SECURITY = "Security"
    SMOKE_SANITY = "Smoke & Sanity"
    USABILITY = "Usability"


@dataclass
class TestCase:
    """單一測試案例"""
    id: str
    title: str
    template: str
    type: CaseType
    priority: Priority
    estimate: Optional[str] = None
    references: Optional[str] = None
    
    # 自定義欄位
    preconds: Optional[str] = None  # 前置條件
    steps: Optional[str] = None     # 測試步驟
    expected: Optional[str] = None   # 預期結果
    
    # 其他自定義欄位
    custom_fields: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Section:
    """測試區段 - 支援巢狀結構"""
    name: str
    description: Optional[str] = None
    
    # 階層結構
    subsections: List['Section'] = field(default_factory=list)
    test_cases: List[TestCase] = field(default_factory=list)
    
    # 樹狀結構輔助資訊
    level: int = 0  # 階層深度
    parent: Optional['Section'] = None
    
    def add_subsection(self, subsection: 'Section') -> None:
        """新增子區段"""
        subsection.parent = self
        subsection.level = self.level + 1
        self.subsections.append(subsection)
    
    def add_test_case(self, test_case: TestCase) -> None:
        """新增測試案例"""
        self.test_cases.append(test_case)
    
    def get_total_cases_count(self) -> int:
        """取得此區段及所有子區段的測試案例總數"""
        total = len(self.test_cases)
        for subsection in self.subsections:
            total += subsection.get_total_cases_count()
        return total
    
    def get_all_cases(self) -> List[TestCase]:
        """取得此區段及所有子區段的所有測試案例"""
        all_cases = self.test_cases.copy()
        for subsection in self.subsections:
            all_cases.extend(subsection.get_all_cases())
        return all_cases
    
    def get_path(self) -> List[str]:
        """取得從根節點到此節點的路徑"""
        if self.parent is None:
            return [self.name]
        return self.parent.get_path() + [self.name]


@dataclass
class TestSuite:
    """測試套件 - 根節點"""
    id: str
    name: str
    description: Optional[str] = None
    
    # 根層級的 sections
    sections: List[Section] = field(default_factory=list)
    
    def add_section(self, section: Section) -> None:
        """新增根層級區段"""
        section.level = 1
        self.sections.append(section)
    
    def get_total_cases_count(self) -> int:
        """取得整個套件的測試案例總數"""
        total = 0
        for section in self.sections:
            total += section.get_total_cases_count()
        return total
    
    def get_all_cases(self) -> List[TestCase]:
        """取得整個套件的所有測試案例"""
        all_cases = []
        for section in self.sections:
            all_cases.extend(section.get_all_cases())
        return all_cases
    
    def get_tree_structure(self) -> Dict[str, Any]:
        """取得樹狀結構表示"""
        def section_to_tree(section: Section) -> Dict[str, Any]:
            return {
                'name': section.name,
                'description': section.description,
                'level': section.level,
                'test_cases_count': len(section.test_cases),
                'total_cases_count': section.get_total_cases_count(),
                'subsections': [section_to_tree(sub) for sub in section.subsections],
                'test_cases': [
                    {
                        'id': case.id,
                        'title': case.title,
                        'type': case.type.value,
                        'priority': case.priority.value
                    } for case in section.test_cases
                ]
            }
        
        return {
            'suite': {
                'id': self.id,
                'name': self.name,
                'description': self.description,
                'total_cases_count': self.get_total_cases_count(),
                'sections': [section_to_tree(section) for section in self.sections]
            }
        }