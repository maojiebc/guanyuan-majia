"""
generator.py
ZoneData 核心生成器
"""

import copy
import uuid
from typing import List, Dict, Optional, Any, Tuple

from .enums import DataType, MetaType, AggrType, ZoneType
from .models import FieldDef, ZoneInfo, DynamicZoneMapping, DsInfo, FieldAssignment


def _gen_key() -> str:
    """生成24位随机key"""
    return uuid.uuid4().hex[:24]


class ZoneDataGenerator:
    """
    ZoneData 生成器（复刻观远数据 BI 平台逻辑）
    
    核心流程：
    1. 初始化 ZoneInfo 和 DsInfo
    2. 根据 FieldAssignment 构建字段对象
    3. 验证并分配到对应 Zone
    4. 应用动态区域筛选（可选）
    """
    
    def __init__(
        self,
        zone_info: List[ZoneInfo],
        ds_info: DsInfo,
        dynamic_zone_info: Optional[Dict[str, Any]] = None
    ):
        # Zone 配置查找表
        self.zone_info = {z.zoneId: z for z in zone_info}
        
        # 数据源信息
        self.ds_info = ds_info
        self._field_lookup = {f.fdId: f for f in ds_info.get_fields()}
        
        # 动态区域配置
        self.dynamic_zone_info = dynamic_zone_info or {}
        self.dz_mappings: List[DynamicZoneMapping] = []
        self.dz_field_values: Dict[str, List[str]] = {}
        self._init_dynamic_zone()
        
        # 初始化空的 ZoneData
        self.zone_data: Dict[ZoneType, List[Dict[str, Any]]] = {
            ZoneType.ROW: [],
            ZoneType.COLUMN: [],
            ZoneType.METRIC: [],
            ZoneType.METRIC_ADDITIONAL: [],
            ZoneType.FILTER: [],
            ZoneType.SORT: [],
            ZoneType.COLOR_BY: [],
            ZoneType.SIZE_BY: [],
            ZoneType.TOOLTIP: [],
            ZoneType.SPLIT: []
        }
    
    def _init_dynamic_zone(self):
        """初始化动态区域状态（复刻 794146.x_）"""
        raw_mappings = self.dynamic_zone_info.get("dzMappings", [])
        for raw in raw_mappings:
            mapping = DynamicZoneMapping(
                dzId=raw["dzId"],
                zoneId=ZoneType(raw["zoneId"]),
                defaultValue=raw.get("defaultValue", []),
                multiSelect=raw.get("multiSelect", False)
            )
            self.dz_mappings.append(mapping)
            self.dz_field_values[mapping.dzId] = mapping.defaultValue.copy()
    
    def _get_field_key(self, field_def: FieldDef, assignment: FieldAssignment) -> str:
        """
        生成字段唯一 key（复刻原平台逻辑）
        
        规则：
        - 普通字段: fdId
        - 日期粒度: fdId_granularity
        - 动态字段: dzId_fdId 或 dzId
        - 无 fdId（如MPH占位）: 随机key
        """
        if not field_def.fdId:
            return _gen_key()
        
        if assignment.granularity and field_def.fdType in [DataType.DATE, DataType.TIMESTAMP]:
            return f"{field_def.fdId}_{assignment.granularity}"
        
        if assignment.dzId:
            return f"{assignment.dzId}_{field_def.fdId}" if field_def.fdId else assignment.dzId
        
        return field_def.fdId
    
    def _build_field_object(
        self,
        field_def: FieldDef,
        assignment: FieldAssignment
    ) -> Dict[str, Any]:
        """构建完整字段对象，与观远导出 JSON 格式对齐"""
        zone_info = self.zone_info.get(assignment.zoneId)
        
        # 基础属性
        field_obj: Dict[str, Any] = {
            "fdId": field_def.fdId,
            "name": field_def.name,
            "fdType": field_def.fdType.value,
            "metaType": field_def.metaType.value,
            "key": self._get_field_key(field_def, assignment),
            "level": "dataset",
            "isAggregated": field_def.isAggregated,
            "calculationType": field_def.calculationType,
        }
        
        # dsId
        if field_def.dsId:
            field_obj["dsId"] = field_def.dsId
        
        # alias（仅 metric 区域有意义）
        if assignment.alias:
            field_obj["alias"] = assignment.alias
        elif field_def.alias and assignment.zoneId == ZoneType.METRIC:
            field_obj["alias"] = field_def.alias
        
        # 日期相关（assignment 优先，否则取 field_def）
        granularity = assignment.granularity or field_def.granularity
        if granularity:
            field_obj["granularity"] = granularity
        if field_def.parentFdName:
            field_obj["parentFdName"] = field_def.parentFdName
        
        # 动态字段
        if assignment.dzId:
            field_obj["dzId"] = assignment.dzId
            field_obj["isStatic"] = False
        
        # 聚合类型
        # 计算字段（isAggregated + formula）不设 aggrType
        if field_def.isAggregated and field_def.formula:
            pass  # 已聚合的计算字段不需要 aggrType
        elif assignment.zoneId == ZoneType.SORT:
            # 排序区：显式指定则用之，否则 NUL
            field_obj["aggrType"] = (assignment.aggrType or AggrType.NUL).value
        elif zone_info and zone_info.needAggregation:
            if assignment.aggrType:
                field_obj["aggrType"] = assignment.aggrType.value
            elif field_def.metaType == MetaType.METRIC:
                field_obj["aggrType"] = AggrType.SUM.value
            # DIM 字段不做默认聚合（如 CNT_DISTINCT 需显式指定）
        
        # 计算公式
        if field_def.formula:
            field_obj["formula"] = field_def.formula
            field_obj["isDsField"] = False
        
        # 筛选器
        if assignment.zoneId == ZoneType.FILTER:
            if assignment.filterValue is not None:
                field_obj["filterValue"] = assignment.filterValue
            if assignment.filterType:
                field_obj["filterType"] = assignment.filterType
        
        # 排序
        if assignment.zoneId == ZoneType.SORT and assignment.ordering:
            field_obj["ordering"] = assignment.ordering
        
        return field_obj

    def _build_mph_object(self, assignment: FieldAssignment) -> Dict[str, Any]:
        """构建 MPH（度量名占位）字段对象，用于交叉表 column 区域"""
        return {
            "name": "度量名",
            "metaType": "MPH",
            "key": self._get_field_key(
                FieldDef(fdId="", name="度量名", metaType=MetaType.MPH),
                assignment
            ),
        }
    
    def _validate(self, assignment: FieldAssignment) -> Tuple[bool, Optional[str]]:
        """验证字段分配合法性"""
        zone_info = self.zone_info.get(assignment.zoneId)
        
        if not zone_info:
            return False, f"Zone {assignment.zoneId.value} 未配置"
        
        # MPH 占位不需要字段存在性检查
        is_mph = assignment.fdId == "__MPH__"
        if not is_mph:
            if assignment.fdId not in self._field_lookup:
                return False, f"字段 {assignment.fdId} 不存在"
            
            field_def = self._field_lookup[assignment.fdId]
            
            # 元类型匹配：row/column 优先 DIM，但允许 METRIC（如数值型 ID 用作维度）
            if assignment.zoneId in [ZoneType.ROW, ZoneType.COLUMN]:
                if field_def.metaType not in (MetaType.DIM, MetaType.MPH, MetaType.METRIC):
                    return False, f"{assignment.zoneId.value} 不支持 {field_def.metaType.value} 类型"
            
            # metric 区域：允许 METRIC 或 DIM+CNT_DISTINCT
            if assignment.zoneId in [ZoneType.METRIC, ZoneType.METRIC_ADDITIONAL, ZoneType.SIZE_BY]:
                if field_def.metaType == MetaType.DIM:
                    if assignment.aggrType not in (AggrType.CNT, AggrType.CNT_DISTINCT):
                        return False, (
                            f"DIM 字段进入 metric 区域必须指定 aggrType 为 CNT 或 CNT_DISTINCT"
                        )
                elif field_def.metaType != MetaType.METRIC:
                    return False, f"{assignment.zoneId.value} 只接受度量字段"
        
        # 数量限制
        current = len(self.zone_data[assignment.zoneId])
        if zone_info.maxCount >= 0 and current >= zone_info.maxCount:
            return False, f"超过最大数量限制 {zone_info.maxCount}"
        
        return True, None
    
    def add_field(self, assignment: FieldAssignment) -> Tuple[bool, Optional[str]]:
        """
        添加单个字段（复刻 ZoneDataManager.addField）
        
        Returns:
            (success, error_message)
        """
        is_valid, error = self._validate(assignment)
        if not is_valid:
            return False, error
        
        # MPH 占位
        if assignment.fdId == "__MPH__":
            field_obj = self._build_mph_object(assignment)
        else:
            field_def = self._field_lookup[assignment.fdId]
            field_obj = self._build_field_object(field_def, assignment)
        
        # 插入位置
        zone_list = self.zone_data[assignment.zoneId]
        pos = assignment.position
        
        if pos is not None and 0 <= pos <= len(zone_list):
            zone_list.insert(pos, field_obj)
        else:
            zone_list.append(field_obj)
        
        return True, None
    
    def add_fields(self, assignments: List[FieldAssignment]) -> Dict[str, Any]:
        """批量添加字段"""
        stats: Dict[str, Any] = {"success": 0, "failed": 0, "errors": []}
        
        for assignment in assignments:
            success, error = self.add_field(assignment)
            if success:
                stats["success"] += 1
            else:
                stats["failed"] += 1
                stats["errors"].append({
                    "fdId": assignment.fdId,
                    "zoneId": assignment.zoneId.value,
                    "error": error
                })
        
        return stats
    
    def update_dynamic_selection(self, dz_id: str, values: List[str]):
        """更新动态字段选中值（复刻 794146）"""
        self.dz_field_values[dz_id] = values.copy()
    
    def get_real_used_zone_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        获取实际使用的 ZoneData（应用动态筛选）
        复刻 ZoneDataManager.getRealUsedZoneData
        """
        result: Dict[str, List[Dict[str, Any]]] = {}
        
        for zone_type, fields in self.zone_data.items():
            filtered = []
            
            for f in fields:
                dz_id = f.get("dzId")
                
                # 非动态字段保留
                if not dz_id:
                    filtered.append(f)
                    continue
                
                # 动态字段：检查是否被选中
                selected = self.dz_field_values.get(dz_id, [])
                if f["key"] in selected:
                    filtered.append(f)
            
            result[zone_type.value] = filtered
        
        return result
    
    def get_zone_data(self, apply_dynamic_filter: bool = False) -> Dict[str, Any]:
        """
        获取完整 ZoneData 结构
        
        Args:
            apply_dynamic_filter: 是否应用动态字段筛选
        """
        if apply_dynamic_filter:
            zone_data = self.get_real_used_zone_data()
        else:
            zone_data = {
                zt.value: [copy.deepcopy(f) for f in fields]
                for zt, fields in self.zone_data.items()
            }
        
        return {
            "zoneData": zone_data,
            "zoneInfo": [z.to_dict() for z in self.zone_info.values()],
            "dynamicZoneInfo": {
                "dzMappings": [m.to_dict() for m in self.dz_mappings],
                "hidden": self.dynamic_zone_info.get("hidden", False)
            } if self.dz_mappings else None,
            "stateValue": {
                "dzFieldValues": {
                    k: {"value": v} for k, v in self.dz_field_values.items()
                }
            }
        }
    
    def get_zone_data_flat(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        获取纯 zoneData（不含外层包装），直接用于 API 提交
        """
        return {
            zt.value: [copy.deepcopy(f) for f in fields]
            for zt, fields in self.zone_data.items()
        }
    
    def remove_field(self, zone_id: ZoneType, field_key: str) -> bool:
        """移除字段"""
        zone_list = self.zone_data[zone_id]
        original = len(zone_list)
        self.zone_data[zone_id] = [f for f in zone_list if f["key"] != field_key]
        return len(self.zone_data[zone_id]) < original
    
    def move_field(
        self,
        field_key: str,
        from_zone: ZoneType,
        to_zone: ZoneType,
        to_position: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """移动字段到另一个 Zone"""
        # 查找字段
        field = None
        for f in self.zone_data[from_zone]:
            if f["key"] == field_key:
                field = f
                break
        
        if not field:
            return False, f"字段 {field_key} 不在 {from_zone.value}"
        
        # 创建新分配
        assignment = FieldAssignment(
            fdId=field["fdId"],
            zoneId=to_zone,
            position=to_position,
            aggrType=AggrType(field["aggrType"]) if "aggrType" in field else None,
            dzId=field.get("dzId"),
            granularity=field.get("granularity")
        )
        
        # 添加并移除
        success, error = self.add_field(assignment)
        if success:
            self.remove_field(from_zone, field_key)
        
        return success, error
