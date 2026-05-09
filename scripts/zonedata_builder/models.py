"""
models.py
数据模型定义
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Literal

from .enums import DataType, MetaType, AggrType, ZoneType


@dataclass
class FieldDef:
    """
    字段定义（来自 dsInfo.columns）
    """
    fdId: str
    name: str
    dsId: Optional[str] = None
    fdType: DataType = DataType.STRING
    metaType: MetaType = MetaType.DIM
    alias: Optional[str] = None
    granularity: Optional[str] = None
    parentFdName: Optional[str] = None
    isDsField: bool = True
    formula: Optional[str] = None
    isAggregated: bool = False
    calculationType: str = "normal"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fdId": self.fdId,
            "name": self.name,
            "dsId": self.dsId,
            "fdType": self.fdType.value,
            "metaType": self.metaType.value,
            "alias": self.alias,
            "granularity": self.granularity,
            "parentFdName": self.parentFdName,
            "isDsField": self.isDsField,
            "formula": self.formula,
            "isAggregated": self.isAggregated,
            "calculationType": self.calculationType
        }


@dataclass
class ZoneInfo:
    """
    Zone 配置信息（复刻 313759.Tw）
    """
    zoneId: ZoneType
    needAggregation: bool = False
    minCount: int = 0
    maxCount: int = 1
    setting: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "zoneId": self.zoneId.value,
            "needAggregation": self.needAggregation,
            "minCount": self.minCount,
            "maxCount": self.maxCount,
            "setting": self.setting
        }


@dataclass
class DynamicZoneMapping:
    """
    动态区域映射（复刻 794146）
    """
    dzId: str
    zoneId: ZoneType
    defaultValue: List[str] = field(default_factory=list)
    multiSelect: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "dzId": self.dzId,
            "zoneId": self.zoneId.value,
            "defaultValue": self.defaultValue,
            "multiSelect": self.multiSelect
        }


@dataclass
class DsInfo:
    """
    数据源信息
    """
    config: Dict[str, Any]
    cdId: Optional[str] = None
    
    def get_fields(self) -> List[FieldDef]:
        """解析字段列表，兼容 fields / columns 两种 key"""
        raw_fields = self.config.get("fields") or self.config.get("columns") or []
        ds_id = self.config.get("dsId")
        return [
            FieldDef(
                fdId=f["fdId"],
                name=f["name"],
                dsId=f.get("dsId", ds_id),
                fdType=DataType(f.get("fdType", "STRING")),
                metaType=MetaType(f.get("metaType", "DIM")),
                alias=f.get("alias"),
                granularity=f.get("granularity"),
                parentFdName=f.get("parentFdName"),
                isDsField=f.get("isDsField", True),
                formula=f.get("formula"),
                isAggregated=f.get("isAggregated", False),
                calculationType=f.get("calculationType", "normal")
            )
            for f in raw_fields
        ]


@dataclass
class FieldAssignment:
    """
    字段分配指令（核心输入格式）
    
    这是您需要提供的字段分配配置
    """
    fdId: str
    zoneId: ZoneType
    position: Optional[int] = None
    
    # 字段覆盖属性
    alias: Optional[str] = None
    aggrType: Optional[AggrType] = None
    granularity: Optional[str] = None
    dzId: Optional[str] = None
    
    # 筛选器专用
    filterValue: Optional[List[Any]] = None
    filterType: Optional[str] = None
    
    # 排序专用
    ordering: Optional[str] = None  # "asc" / "DESC"，大小写不敏感
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fdId": self.fdId,
            "zoneId": self.zoneId.value,
            "position": self.position,
            "alias": self.alias,
            "aggrType": self.aggrType.value if self.aggrType else None,
            "granularity": self.granularity,
            "dzId": self.dzId,
            "filterValue": self.filterValue,
            "filterType": self.filterType,
            "ordering": self.ordering
        }
