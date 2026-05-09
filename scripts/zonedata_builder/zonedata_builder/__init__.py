"""
zonedata_builder
观远数据 BI 平台 ZoneData 生成器（Python 复刻版）

使用示例：
    from zonedata_builder import create_zone_data, FieldAssignment, ZoneType
    
    result = create_zone_data(
        zone_info=[...],
        ds_info={...},
        field_assignments=[...]
    )
"""

from typing import List, Dict, Any, Optional

from .enums import (
    DataType,
    DataTypeGroup,
    MetaType,
    AggrType,
    ZoneType,
    ZoneSpecialType,
    ChartType
)

from .models import (
    FieldDef,
    ZoneInfo,
    DynamicZoneMapping,
    DsInfo,
    FieldAssignment
)

from .generator import ZoneDataGenerator


def create_zone_data(
    zone_info: List[Dict[str, Any]],
    ds_info: Dict[str, Any],
    field_assignments: List[Dict[str, Any]],
    dynamic_zone_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    便捷函数：从 JSON 配置快速生成 ZoneData
    
    Args:
        zone_info: Zone 配置列表
        ds_info: 数据源信息（包含 fields/columns）
        field_assignments: 字段分配列表
        dynamic_zone_info: 动态区域配置（可选）
    
    Returns:
        完整的 ZoneData 结构
    """
    # 解析 ZoneInfo
    zone_info_objs = [
        ZoneInfo(
            zoneId=ZoneType(z["zoneId"]),
            needAggregation=z.get("needAggregation", False),
            minCount=z.get("minCount", 0),
            maxCount=z.get("maxCount", 1),
            setting=z.get("setting")
        )
        for z in zone_info
    ]
    
    # 解析 DsInfo
    ds_info_obj = DsInfo(config=ds_info, cdId=ds_info.get("cdId"))
    
    # 解析字段分配
    assignments = []
    for fa in field_assignments:
        aggr_raw = fa.get("aggrType")
        assignment = FieldAssignment(
            fdId=fa["fdId"],
            zoneId=ZoneType(fa["zoneId"]),
            position=fa.get("position"),
            alias=fa.get("alias"),
            aggrType=AggrType(aggr_raw) if aggr_raw else None,
            granularity=fa.get("granularity"),
            dzId=fa.get("dzId"),
            filterValue=fa.get("filterValue"),
            filterType=fa.get("filterType"),
            ordering=fa.get("ordering")
        )
        assignments.append(assignment)
    
    # 生成
    generator = ZoneDataGenerator(zone_info_objs, ds_info_obj, dynamic_zone_info)
    stats = generator.add_fields(assignments)
    
    if stats["failed"] > 0:
        import warnings
        for err in stats["errors"]:
            warnings.warn(f"字段分配失败 {err['fdId']} - {err['zoneId']}: {err['error']}")
    
    return generator.get_zone_data(apply_dynamic_filter=False)


__all__ = [
    # 枚举
    "DataType",
    "DataTypeGroup",
    "MetaType",
    "AggrType",
    "ZoneType",
    "ZoneSpecialType",
    "ChartType",
    # 模型
    "FieldDef",
    "ZoneInfo",
    "DynamicZoneMapping",
    "DsInfo",
    "FieldAssignment",
    # 生成器
    "ZoneDataGenerator",
    # 便捷函数
    "create_zone_data",
]
