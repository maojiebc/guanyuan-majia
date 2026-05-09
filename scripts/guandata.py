#!/usr/bin/env python3
"""
观远BI CLI 工具 — 单文件版本
用法: python3 guandata.py <command> [args...]
"""

import sys
import os

# Windows 编码修复
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
import json
import re
import asyncio
import argparse
import base64
import copy
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx


def _load_config() -> Dict[str, str]:
    """从 config.json 加载配置，找不到时用默认值"""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config.json')
    try:
        with open(config_path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


_CFG = _load_config()


class GuandataClient:
    """观远BI API客户端"""

    # 默认配置（优先从 config.json 读取）
    DEFAULT_BASE_URL = _CFG.get("base_url", "")
    DEFAULT_DOMAIN = _CFG.get("domain", "guanbi")
    DEFAULT_LOGIN_ID = _CFG.get("login_id", "")
    DEFAULT_LOGIN_SECRET = _CFG.get("password", "")
    TOKEN_LIFETIME = 7200  # token有效期2小时（秒）
    
    # 超时配置（秒）
    DEFAULT_TIMEOUT = 30  # 普通请求超时
    DATA_TIMEOUT = 60     # 数据查询超时（可能较慢）
    LOGIN_TIMEOUT = 10    # 登录请求超时

    # 已验证的 chart_type 枚举，value 为说明
    VALID_CHART_TYPES = {
        "SINGLE_VALUE":               "指标卡（单值）",
        "KPI_CARD":                   "指标卡（带阈值样式）",
        "BASIC_COLUMN":               "柱状图",
        "GROUPED_COLUMN":             "簇状柱状图",
        "STACKED_COLUMN":             "堆积柱状图",
        "PERCENT_STACKED_COLUMN":     "百分比堆积柱状图",
        "WATERFALL_COLUMN":           "瀑布图",
        "BULLET_COLUMN":              "子弹图",
        "BASIC_BAR":                  "条形图",
        "BASIC_LINE":                 "折线图",
        "MULTI_LINE":                 "多条折线图",
        "STACKED_AREA":               "堆积面积图",
        "PERCENT_STACKED_AREA":       "百分比堆积面积图",
        "STACKED_COLUMN_WITH_LINE":   "柱线组合图",
        "GROUPED_COLUMN_WITH_LINE":   "簇状柱线组合图",
        "STACKED_COLUMN_WITH_SYMBOL": "柱标记组合图",
        "GROUPED_COLUMN_WITH_SYMBOL": "簇状柱标记组合图",
        "PIE":                        "饼图",
        "TREE_MAP":                   "矩形树图",
        "FUNNEL":                     "漏斗图",
        "HEAT_MAP":                   "热力图",
        "MULTIDIMENSIONAL_SANKEY":    "多维桑基图",
        "PIVOT_TABLE":                "交叉表",
        "WORD_CLOUD":                 "词云",
        "BASIC_BUBBLE":               "气泡图",
        "BASIC_SCATTER_PLOT":         "散点图",
    }

    @staticmethod
    def _validate_chart_type(chart_type: str) -> None:
        """校验 chart_type，不合法时打印全类型列表并退出"""
        if chart_type in GuandataClient.VALID_CHART_TYPES:
            return
        print(f'❌ chart_type="{chart_type}" 不是有效的图表类型')
        print(f'   共 {len(GuandataClient.VALID_CHART_TYPES)} 种:')
        for ct, desc in sorted(GuandataClient.VALID_CHART_TYPES.items()):
            print(f'   {ct:<35s} {desc}')
        sys.exit(1)

    @staticmethod
    def _transform_query_filter(filter_obj: Dict) -> Dict:
        """将 query -f 的 filter 转换为 API 期望格式

        用户格式: {"combineType":"AND","conditions":[{"type":"condition","fdId":"字段名","filterType":"EQ","value":["y"]}]}
        API 格式: {"combineType":"AND","conditions":[{"type":"condition","value":{"name":"字段名","filterType":"EQ","filterValue":["y"]}}]}
        
        注意：condition 里的 fdId 位置实际填的是字段名（如"门店名称"），不是真正的 fdId。
        """
        if not filter_obj or "conditions" not in filter_obj:
            return filter_obj
        result = {"combineType": filter_obj.get("combineType", "AND")}
        result["conditions"] = []
        for cond in filter_obj["conditions"]:
            if cond.get("type") == "condition" and "filterType" in cond:
                new_cond = {"type": "condition"}
                if cond.get("not"):
                    new_cond["not"] = True
                # fdId 位置实际放的是字段名，直接传给 API 的 name
                field_name = cond.get("fdId", cond.get("name", ""))
                new_cond["value"] = {
                    "name": field_name,
                    "filterType": cond["filterType"],
                    "filterValue": cond.get("value", []),
                }
                result["conditions"].append(new_cond)
            else:
                result["conditions"].append(cond)
        return result

    def __init__(self, base_url: str = None):
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.token: Optional[str] = None
        self.token_expire_at: Optional[float] = None  # token过期时间戳
        self._login_domain = self.DEFAULT_DOMAIN
        self._login_id = self.DEFAULT_LOGIN_ID
        self._login_secret = self.DEFAULT_LOGIN_SECRET
        
        # 检查配置是否完整
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config.json')
        missing = []
        if not self.base_url:
            missing.append("base_url")
        if not self._login_id:
            missing.append("login_id")
        if not self._login_secret:
            missing.append("password")
        
        if missing:
            raise ValueError(
                f"❌ 缺少配置项: {', '.join(missing)}\n"
                f"   请在配置文件 {config_path} 中设置\n"
                f"   配置格式: {{\"base_url\": \"https://...\", \"login_id\": \"账号\", \"password\": \"密码\"}}"
            )

    def _get_headers(self, include_token: bool = True) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if include_token and self.token:
            headers["X-Auth-Token"] = self.token
            headers["Authorization"] = f"Bearer {self.token}"
            headers["token"]= self.token
        return headers

    def _is_token_expired(self) -> bool:
        """检查token是否已过期（仅在真正过期时返回True）"""
        if not self.token or not self.token_expire_at:
            return True
        return time.time() >= self.token_expire_at

    async def _ensure_token(self) -> bool:
        """确保token有效，如果过期则自动重新获取

        Returns:
            是否成功获取到有效token
        """
        if not self._is_token_expired():
            return True

        # token已过期，重新登录
        try:
            await self.login(
                domain=self._login_domain,
                login_id=self._login_id,
                login_secret=self._login_secret
            )
            return True
        except Exception as e:
            print(f'⚠️ 自动登录失败: {type(e).__name__}: {e}')
            return False

    # ===== 认证相关 =====

    async def login(self, domain: str, login_id: str, login_secret: str) -> Dict[str, Any]:
        """用户登录获取token

        Args:
            domain: 域名
            login_id: 登录ID
            login_secret: 登录凭据原文（会按观远接口要求进行 Base64 编码）

        Returns:
            包含token和过期时间的响应
        """
        # 保存登录信息，用于token过期后自动重新登录
        self._login_domain = domain
        self._login_id = login_id
        self._login_secret = login_secret

        # 观远 public-api/sign-in 要求登录凭据经 Base64 编码后提交到用户配置的 BI 实例。
        encoded_login_secret = base64.b64encode(login_secret.encode()).decode()

        async with httpx.AsyncClient(timeout=self.LOGIN_TIMEOUT) as client:
            response = await client.post(
                f"{self.base_url}/public-api/sign-in",
                json={
                    "domain": domain,
                    "loginId": login_id,
                    "password": encoded_login_secret,
                },
                headers=self._get_headers(include_token=False),
            )
            response.raise_for_status()
            data = response.json()

            if data.get("result") == "ok" and "response" in data:
                self.token = data["response"]["token"]
                # 设置token过期时间（2小时后）
                self.token_expire_at = time.time() + self.TOKEN_LIFETIME
                # 更新响应中的过期时间
                data["response"]["expire_at"] = self.token_expire_at
                data["response"]["expire_in"] = self.TOKEN_LIFETIME

            return data

    def set_token(self, token: str, expires_in: int = TOKEN_LIFETIME) -> None:
        """直接设置token

        Args:
            token: 用户token
            expires_in: token有效期（秒），默认2小时
        """
        self.token = token
        self.token_expire_at = time.time() + expires_in

    # ===== 缓存目录配置（统一放在 skill 根目录下的 .cache/ 中，支持 task 隔离）=====

    # skill 根目录 = scripts/..（即 guandata/ 目录）
    SKILL_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

    # 当前 task ID（通过 --task 参数设置）
    _task_id: Optional[str] = None

    # 安全 task 名：字母数字 + 中日韩字符 + _ - .，禁止路径穿越
    _TASK_ID_PATTERN = re.compile(
        r'^[A-Za-z0-9_.一-鿿぀-ヿ가-힯-]{1,64}$'
    )

    @classmethod
    def set_task(cls, task_id: Optional[str]):
        """设置当前任务 ID，用于隔离不同任务的缓存。

        安全约束：拒绝包含 / \\ .. 或超长的 task 名，防止路径穿越把
        缓存写到 .cache/tasks 目录之外。允许字母/数字/中日韩字符/
        下划线/短横线/点，长度 1–64。
        """
        if task_id is None:
            cls._task_id = None
            return
        if (not cls._TASK_ID_PATTERN.match(task_id)) or task_id in ('.', '..'):
            raise ValueError(
                f"非法 --task 名：{task_id!r}。"
                "只允许字母/数字/中日韩字符/下划线/短横线/点，长度 1-64，"
                "禁止 / \\ . .. 等路径分隔符与保留名。"
            )
        cls._task_id = task_id

    @classmethod
    def _get_cache_dir(cls, subdir: str) -> str:
        """获取缓存目录，支持按 task 隔离"""
        if cls._task_id:
            return os.path.join(cls.SKILL_ROOT, '.cache', 'tasks', cls._task_id, subdir)
        return os.path.join(cls.SKILL_ROOT, '.cache', subdir)
    
    @property
    def DATA_CACHE_DIR(self) -> str:
        """数据查询缓存（CSV）"""
        return self._get_cache_dir('data')
    
    @property
    def DATASETS_CACHE_FILE(self) -> str:
        """数据集列表缓存（JSON）"""
        return os.path.join(self._get_cache_dir('datasets'), 'list_cache.json')
    
    @property
    def COLUMNS_CACHE_DIR(self) -> str:
        """字段列表缓存（JSON）"""
        return self._get_cache_dir('columns')

    def _ensure_data_cache_dir(self):
        """确保数据缓存目录存在"""
        os.makedirs(self.DATA_CACHE_DIR, exist_ok=True)

    def _save_to_cache(self, data: Any, prefix: str = "data") -> str:
        """保存数据到本地缓存文件（JSON），返回文件路径"""
        self._ensure_data_cache_dir()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # 精确到毫秒
        filename = f"{prefix}_{ts}.json"
        path = os.path.join(self.DATA_CACHE_DIR, filename)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path

    def _save_to_cache_csv(self, headers: list, rows: list, prefix: str = "data") -> str:
        """保存数据到本地缓存文件（CSV），返回文件路径"""
        import csv
        self._ensure_data_cache_dir()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # 精确到毫秒
        filename = f"{prefix}_{ts}.csv"
        path = os.path.join(self.DATA_CACHE_DIR, filename)
        with open(path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for row in rows:
                # 处理可能的 dict 类型 cell
                clean = []
                for cell in row:
                    if isinstance(cell, dict):
                        clean.append(cell.get('v', cell.get('value', str(cell))))
                    else:
                        clean.append(cell)
                writer.writerow(clean)
        return path

    @staticmethod
    def _format_table(headers: list, rows: list, max_rows: int = 20, max_cols: int = 12) -> str:
        """格式化为对齐的表格文本"""
        if not headers:
            return ''
        # 截断列
        h = headers[:max_cols]
        r_data = [row[:max_cols] for row in rows[:max_rows]]
        # 计算每列宽度
        widths = [len(str(col)) for col in h]
        for row in r_data:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(str(cell)))
        # 构建输出
        lines = []
        header_line = ' | '.join(str(h[i]).ljust(widths[i]) for i in range(len(h)))
        lines.append(header_line)
        lines.append('-' * len(header_line))
        for row in r_data:
            line = ' | '.join(str(cell if cell is not None else '').ljust(widths[i]) for i, cell in enumerate(row))
            lines.append(line)
        if len(rows) > max_rows:
            lines.append(f'... 共 {len(rows)} 行')
        if len(headers) > max_cols:
            lines.append(f'... 共 {len(headers)} 列，仅显示前 {max_cols} 列')
        return '\n'.join(lines)
    DATASETS_SAMPLE_SIZE = 5  # 每个数据集取前5行样本

    def _ensure_columns_cache_dir(self):
        os.makedirs(self.COLUMNS_CACHE_DIR, exist_ok=True)

    def _load_cached_columns(self, ds_id: str) -> Optional[Dict[str, Any]]:
        """从本地缓存加载字段列表"""
        try:
            path = os.path.join(self.COLUMNS_CACHE_DIR, f"{ds_id}.json")
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            print(f'⚠️ 加载字段缓存失败 ({ds_id}): {e}')
            return None

    def _save_cached_columns(self, ds_id: str, columns: list, ds_modify_time: str = ""):
        """保存字段列表到本地缓存"""
        self._ensure_columns_cache_dir()
        path = os.path.join(self.COLUMNS_CACHE_DIR, f"{ds_id}.json")
        cache = {
            "dsId": ds_id,
            "datasourceModifyTime": ds_modify_time,
            "cacheTime": time.strftime("%Y-%m-%d %H:%M:%S%z"),
            "columns": columns,
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)

    def _is_columns_cache_fresh(self, ds_id: str, ds_modify_time: str) -> bool:
        """检查缓存是否比数据源更新时间更新"""
        cached = self._load_cached_columns(ds_id)
        if not cached:
            return False
        cached_time = cached.get("datasourceModifyTime", "")
        # 缓存时间 >= 数据源修改时间 → 缓存有效
        return cached_time >= ds_modify_time if cached_time else False

    def _load_cached_datasets_list(self) -> Optional[Dict[str, Any]]:
        """从本地缓存加载数据集列表"""
        try:
            if os.path.exists(self.DATASETS_CACHE_FILE):
                with open(self.DATASETS_CACHE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            return {"error": f"加载缓存失败: {str(e)}"}

    async def _fetch_and_cache_datasets_list(self, permission_type: str = "ALL") -> Dict[str, Any]:
        """从远程获取数据集列表，并为每个数据集获取样本数据，然后缓存到本地"""
        # 确保token有效
        if not await self._ensure_token():
            return {"error": "Token失效，无法自动登录"}

        # 1. 获取数据集列表
        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
            response = await client.get(
                f"{self.base_url}/api/directory/DATA_SET/search",
                params={
                    "offset": 0,
                    "limit": 200,
                    "resourceOnly": "true",
                    "permissionType": permission_type,
                    "orderBy": "fileType",
                    "searchCategory": "ALL",
                },
                headers=self._get_headers(),
            )
            response.raise_for_status()
            data = response.json()

        if data.get("result") != "ok":
            return data

        # 2. 为每个数据集获取样本数据
        datasets = data.get("response", {}).get("contents", [])
        for ds in datasets:
            ds_id = ds.get("dsId")
            if ds_id:
                try:
                    # 获取前5行样本数据
                    sample_data = await self._fetch_dataset_sample_for_list(ds_id, self.DATASETS_SAMPLE_SIZE)
                    ds["_sample_data"] = sample_data
                except Exception as e:
                    ds["_sample_error"] = str(e)

        # 3. 添加缓存元信息
        from datetime import datetime
        cache_meta = {
            "_cache_meta": {
                "cached_at": datetime.now().isoformat(),
                "dataset_count": len(datasets),
                "permission_type": permission_type,
                "sample_size": self.DATASETS_SAMPLE_SIZE,
            }
        }
        data["response"].update(cache_meta)

        # 4. 保存到本地缓存文件
        try:
            os.makedirs(os.path.dirname(self.DATASETS_CACHE_FILE), exist_ok=True)
            with open(self.DATASETS_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            data["_cache_save_error"] = str(e)

        return data

    async def _fetch_dataset_sample_for_list(self, ds_id: str, limit: int = 5) -> Dict[str, Any]:
        """获取数据集的前N行样本数据（用于列表缓存）"""
        async with httpx.AsyncClient(timeout=self.DATA_TIMEOUT) as client:
            response = await client.post(
                f"{self.base_url}/public-api/data-source/{ds_id}/data",
                json={
                    "offset": 0,
                    "limit": limit,
                },
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()

    async def search_datasets_list(
        self,
        use_cache: bool = True,
        refresh: bool = False,
        permission_type: str = "ALL",
    ) -> Dict[str, Any]:
        """搜索数据集列表

        Args:
            use_cache: 是否优先使用本地缓存，默认为True
            refresh: 是否强制刷新缓存（重新从远程获取），默认为False
            permission_type: 权限类型 (ALL, OWNER, ONLYREADABLE)

        Returns:
            数据集列表（包含样本数据）
        """
        # 情况1: 强制刷新 - 直接远程获取并缓存
        if refresh:
            return await self._fetch_and_cache_datasets_list(permission_type)

        # 情况2: 使用缓存 - 尝试从本地加载
        if use_cache:
            cached = self._load_cached_datasets_list()
            if cached is not None:
                # 添加缓存命中标记
                if "response" in cached:
                    cached["_cache_hit"] = True
                return cached

            # 缓存不存在，回退到远程获取
            return await self._fetch_and_cache_datasets_list(permission_type)

        # 情况3: 不使用缓存 - 直接从远程获取但不保存
        # 确保token有效
        if not await self._ensure_token():
            return {"error": "Token失效，无法自动登录"}

        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
            response = await client.get(
                f"{self.base_url}/api/directory/DATA_SET/search",
                params={
                    "offset": 0,
                    "limit": 200,
                    "resourceOnly": "true",
                    "permissionType": permission_type,
                    "orderBy": "fileType",
                    "searchCategory": "ALL",
                },
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()

    async def refresh_datasets_cache(self, permission_type: str = "ALL") -> Dict[str, Any]:
        """强制刷新数据集缓存（重新从远程获取并缓存）

        Args:
            permission_type: 权限类型 (ALL, OWNER, ONLYREADABLE)

        Returns:
            数据集列表（包含样本数据）
        """
        return await self._fetch_and_cache_datasets_list(permission_type)

    async def get_dataset_columns(self, ds_id: str) -> Dict[str, Any]:
        """获取数据集的字段列表

        Args:
            ds_id: 数据集ID

        Returns:
            字段列表
        """
        # 确保token有效
        if not await self._ensure_token():
            return {"error": "Token失效，无法自动登录"}

        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
            response = await client.post(
                f"{self.base_url}/public-api/data-source/{ds_id}/columns",
                json={},
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()

    async def get_dataset_virtual_columns(self, ds_id: str) -> List[Dict[str, Any]]:
        """获取数据集的计算字段（virtualColumns）

        Args:
            ds_id: 数据集ID

        Returns:
            计算字段列表
        """
        if not await self._ensure_token():
            return []

        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
            response = await client.get(
                f"{self.base_url}/api/data-source/{ds_id}",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            data = response.json()
            resp = data.get("response", data)
            return resp.get("virtualColumns", [])

    async def get_dataset_data(
        self,
        ds_id: str,
        offset: int = 0,
        limit: int = 10,
        filter: Optional[Dict] = None,
        sort_factor: Optional[Dict] = None,
        save_local: bool = True,
        output_dir: str = "./data",
    ) -> Dict[str, Any]:
        """获取数据集数据

        Args:
            ds_id: 数据集ID
            offset: 起始位置
            limit: 返回数量
            filter: 过滤条件配置
            sort_factor: 排序配置
            save_local: 是否保存到本地
            output_dir: 输出目录

        Returns:
            数据集数据和预览
        """
        import os
        import csv
        from datetime import datetime

        # 确保token有效
        if not await self._ensure_token():
            return {"error": "Token失效，无法自动登录"}

        body = {
            "offset": offset,
            "limit": limit,
        }
        if filter:
            body["filter"] = self._transform_query_filter(filter)
        if sort_factor:
            body["sortFactor"] = sort_factor

        async with httpx.AsyncClient(timeout=self.DATA_TIMEOUT) as client:
            response = await client.post(
                f"{self.base_url}/public-api/data-source/{ds_id}/data",
                json=body,
                headers=self._get_headers(),
            )
            response.raise_for_status()
            data = response.json()

        # 保存到本地
        if save_local and data.get("result") == "ok":
            try:
                # 创建输出目录
                os.makedirs(output_dir, exist_ok=True)

                # 获取数据集名称
                ds_name = data.get("response", {}).get("name", "unknown")

                # 构建文件名: YYYYMMDD_HHMMSS_数据集名_filter描述_topN行.csv
                now = datetime.now()
                timestamp = now.strftime("%Y%m%d_%H%M%S")

                # 构建filter描述
                filter_desc = ""
                if filter:
                    conditions = []
                    for cond in filter.get("conditions", []):
                        if cond.get("type") == "condition":
                            val = cond.get("value", {})
                            name = val.get("name", "")
                            ft = val.get("filterType", "")
                            fv = val.get("filterValue", [])
                            conditions.append(f"{name}{ft}{fv}")
                    if conditions:
                        filter_desc = "_" + "_".join(conditions)[:50]  # 限制长度

                # 构建文件名
                safe_ds_name = "".join(c for c in ds_name if c.isalnum() or c in "_-").rstrip()
                filename = f"{timestamp}_{safe_ds_name}{filter_desc}_top{limit}rows.csv"
                filepath = os.path.join(output_dir, filename)

                # 准备数据
                response_data = data.get("response", {})
                columns_info = response_data.get("columns", [])
                preview = response_data.get("preview", [])

                # 写入CSV
                with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)

                    # 写入元信息（前5行）
                    writer.writerow(["#" * 80])
                    writer.writerow(["# 查询信息"])
                    writer.writerow(["#" * 80])
                    writer.writerow(["查询时间", now.strftime("%Y-%m-%d %H:%M:%S")])
                    writer.writerow(["数据集ID", ds_id])
                    writer.writerow(["数据集名称", ds_name])
                    writer.writerow(["返回行数", len(preview)])
                    writer.writerow(["请求行数", limit])
                    writer.writerow(["偏移量", offset])
                    if filter:
                        writer.writerow(["筛选条件", json.dumps(filter, ensure_ascii=False)])
                    if sort_factor:
                        writer.writerow(["排序配置", json.dumps(sort_factor, ensure_ascii=False)])
                    writer.writerow(["#" * 80])
                    writer.writerow([])  # 空行分隔

                    # 写入表头
                    if columns_info:
                        headers = [col.get("name", "") for col in columns_info]
                        writer.writerow(headers)

                    # 写入数据
                    for row in preview:
                        writer.writerow(row)

                # 添加文件路径到返回结果
                data["_local_file"] = {
                    "path": filepath,
                    "filename": filename,
                    "row_count": len(preview),
                }

            except Exception as e:
                # 保存失败不影响主流程，只记录错误
                data["_local_file_error"] = str(e)

        return data

    async def search_column_values(
        self,
        ds_id: str,
        fd_id: str,
        search: str = "",
        max_count: int = -1,
        limit: int = 200,
        offset: int = 0,
        version: Optional[int] = None,
    ) -> Dict[str, Any]:
        """搜索字段值

        Args:
            ds_id: 数据集ID
            fd_id: 字段ID
            search: 搜索字符串
            max_count: 最大返回数量
            limit: 分页限制
            offset: 分页偏移
            version: 版本号

        Returns:
            字段值列表
        """
        # 确保token有效
        if not await self._ensure_token():
            return {"error": "Token失效，无法自动登录"}

        body = {
            "dsId": ds_id,
            "fieldQuery": {
                "fdId": fd_id,
                "maxCount": max_count,
                "search": search,
                "limit": limit,
                "offset": offset,
            },
        }
        if version is not None:
            body["version"] = version

        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
            response = await client.post(
                f"{self.base_url}/api/oriput/ds-info/column/values-v2",
                json=body,
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()

    # ===== 页面相关 =====

    async def search_pages(self) -> Dict[str, Any]:
        """获取页面列表

        Returns:
            页面列表（树形结构）
        """
        # 确保token有效
        if not await self._ensure_token():
            return {"error": "Token失效，无法自动登录"}

        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
            response = await client.get(
                f"{self.base_url}/api/page-v3",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()

    async def create_page(
        self,
        name: str,
        parent_dir_id: str = None,
        pg_type: str = "PAGE",
        description: str = "",
    ) -> Dict[str, Any]:
        """创建页面

        Args:
            name: 页面名称
            parent_dir_id: 父目录ID
            pg_type: 页面类型 (PAGE, CUSTOM_REPORT, etc.)
            description: 页面描述

        Returns:
            创建的页面信息
        """
        # 确保token有效
        if not await self._ensure_token():
            return {"error": "Token失效，无法自动登录"}

        if parent_dir_id is None:
            parent_dir_id = _CFG.get("default_folder_id")
            if not parent_dir_id:
                return {"error": "未配置 default_folder_id，请在 config.json 中设置或通过 --parent-dir 传入"}

        body = {
            "name": name,
            "pgType": pg_type,
            "parentDirId": parent_dir_id,
            "meta": {
                "layoutSetting": {"layoutType": "waterfall"},
                "layout": [],
            },
            "description": description,
        }

        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
            response = await client.post(
                f"{self.base_url}/api/page",
                json=body,
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()

    # ===== 卡片相关 =====

    async def create_card(
        self,
        name: str,
        ds_id: str,
        cd_type: str = "CHART",
        chart_type: str = "PIVOT_TABLE",
    ) -> Dict[str, Any]:
        """创建临时卡片

        Args:
            name: 卡片名称
            ds_id: 数据集ID
            cd_type: 卡片类型 (默认CHART)
            chart_type: 图表类型 (默认PIVOT_TABLE)

        Returns:
            创建的卡片信息
        """
        # 确保token有效
        if not await self._ensure_token():
            return {"error": "Token失效，无法自动登录"}

        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
            response = await client.post(
                f"{self.base_url}/public-api/card/createTmpCard",
                json={
                    "name": name,
                    "cdType": cd_type,
                    "dsId": ds_id,
                    "chartType": chart_type,
                },
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()

    async def get_card_edit_session(self, card_id: str) -> Dict[str, Any]:
        """获取卡片编辑会话

        Args:
            card_id: 卡片ID

        Returns:
            会话信息，包含sessionId
        """
        # 确保token有效
        if not await self._ensure_token():
            return {"error": "Token失效，无法自动登录"}

        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
            response = await client.get(
                f"{self.base_url}/api/card/{card_id}/edit/session",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()

    async def get_card_edit_info(self, card_id: str) -> Dict[str, Any]:
        """获取卡片编辑信息

        Args:
            card_id: 卡片ID

        Returns:
            卡片编辑详细信息
        """
        # 确保token有效
        if not await self._ensure_token():
            return {"error": "Token失效，无法自动登录"}

        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
            response = await client.get(
                f"{self.base_url}/api/card/{card_id}/edit",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()

    async def update_card_config(
        self,
        card_id: str,
        session_id: str,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """修改卡片配置

        Args:
            card_id: 卡片ID
            session_id: 会话ID
            config: 卡片配置数据

        Returns:
            更新结果
        """
        # 确保token有效
        if not await self._ensure_token():
            return {"error": "Token失效，无法自动登录"}

        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
            response = await client.post(
                f"{self.base_url}/api/oriput/card/{card_id}/edit/{session_id}/modify",
                json=config,
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()

    async def save_card(
        self,
        card_id: str,
        session_id: str,
        pg_id: str,
        assoc: Optional[List] = None,
    ) -> Dict[str, Any]:
        """保存卡片

        Args:
            card_id: 卡片ID
            session_id: 会话ID
            pg_id: 页面ID (必需)
            assoc: 关联信息

        Returns:
            保存结果
        """
        # 确保token有效
        if not await self._ensure_token():
            return {"error": "Token失效，无法自动登录"}

        # 7.0+ 版本使用 draft 页面ID
        version = _CFG.get("version", "6")
        pg_id_save = f"{pg_id}_draft" if version == "7" else pg_id
        
        body = {"sessionId": session_id, "pgId": pg_id_save, "assoc": assoc or []}

        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
            response = await client.post(
                f"{self.base_url}/api/card/{card_id}/save",
                json=body,
                headers=self._get_headers(),
            )
            response.raise_for_status()
            result = response.json()
            
            # 7.0+ 版本保存后自动 release
            if version == "7":
                await self.release_page(pg_id)
            
            return result

    async def batch_delete_cards(
        self,
        cd_ids: List[str],
        pg_id: str,
    ) -> Dict[str, Any]:
        """批量删除卡片

        Args:
            cd_ids: 卡片ID列表
            pg_id: 页面ID（卡片所在页面）

        Returns:
            删除结果
        """
        if not await self._ensure_token():
            return {"error": "Token失效，无法自动登录"}

        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
            response = await client.post(
                f"{self.base_url}/api/card/{pg_id}/batchDelete",
                json={"cdIds": cd_ids},
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()


    async def release_page(
        self,
        pg_id: str,
    ) -> Dict[str, Any]:
        """发布页面（观远7.0+）

        Args:
            pg_id: 页面ID（不带 _draft 后缀）

        Returns:
            发布结果
        """
        if not await self._ensure_token():
            return {"error": "Token失效，无法自动登录"}

        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
            response = await client.post(
                f"{self.base_url}/api/page/{pg_id}/release",
                json={},
                headers=self._get_headers(),
            )
            response.raise_for_status()
            
            # 7.0+ 版本删除后自动 release
            version = _CFG.get("version", "6")
            if version == "7":
                await self.release_page(pg_id)
            
            return response.json()

    async def get_page_cards(
        self,
        pg_id: str,
    ) -> Dict[str, Any]:
        """获取页面卡片列表

        使用 public-api/page/{pgId} 接口（BI V7.1+）

        Args:
            pg_id: 页面ID

        Returns:
            页面详情，含 cards 列表
        """
        if not await self._ensure_token():
            return {"error": "Token失效，无法自动登录"}

        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
            response = await client.get(
                f"{self.base_url}/api/page/{pg_id}",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            data = response.json()

            # 提取卡片列表
            cards = data.get("cards", [])
            card_ids = [c["cdId"] for c in cards if "cdId" in c]
            data["cdIds"] = card_ids
            return data

    async def get_card_data(
        self,
        card_id: str,
        view: str = "GRID",
        offset: int = 0,
        limit: int = 200,
        filters: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        获取卡片渲染数据（公开 API）

        接口: POST /public-api/card/{cardId}/data
        认证: X-Auth-Token

        Args:
            card_id: 卡片ID
            view: 视图类型 GRID
            offset: 数据偏移
            limit: 数据条数
            filters: 额外筛选条件

        Returns:
            卡片数据。不同图表类型返回结构不同：

            PIVOT_TABLE / DATA_GRID:
                response.chartMain.data: [[{v: 值}, ...], ...] 二维数组
                response.chartMain.row.values: [[{title: 行名}, ...], ...]
                response.chartMain.column.values: [[{title: 列名}, ...], ...]
                response.chartMain.count: 总行数

            STACKED_COLUMN / BASIC_COLUMN / BASIC_LINE / PIE 等图表:
                response.chartMain.categories: ["分类1", "分类2", ...]
                response.chartMain.series: [
                    {"name": "系列名", "data": [{"y": 值}, ...]}
                ]

            示例（堆叠柱状图）:
                {
                    "chartMain": {
                        "categories": ["示例门店A"],
                        "series": [
                            {"name": "堂食", "data": [{"y": 600000.0}]},
                            {"name": "外卖", "data": [{"y": 3000.0}]}
                        ]
                    }
                }

            示例（交叉表）:
                {
                    "chartMain": {
                        "data": [[{"v": 114480}], [{"v": 4650}]],
                        "row": {"values": [[{"title": "南京市"}], [{"title": "扬州市"}]]},
                        "column": {"values": [[{"title": "客流量"}]]},
                        "count": 15
                    }
                }
        """
        if not await self._ensure_token():
            return {"error": "Token失效，无法自动登录"}

        body: Dict[str, Any] = {
            "view": view,
            "offset": offset,
            "limit": limit,
            "dynamicParams": [],
        }
        if filters:
            body["filters"] = filters

        async with httpx.AsyncClient(timeout=self.DATA_TIMEOUT) as client:
            response = await client.post(
                f"{self.base_url}/public-api/card/{card_id}/data",
                json=body,
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    def normalize_card_data(raw: Dict) -> Dict:
        """
        统一 get_card_data 返回格式，让 LLM 无需区分 chartType。

        返回:
        {
            "chartType": "PIVOT_TABLE | BASIC_COLUMN | ...",
            "headers": ["维度1", "维度2", "指标1"],
            "rows": [["值1", "值2", 123.4], ...],
            "count": 100,
            "hasMore": false
        }
        """
        response = raw.get("response", raw)
        chart_type = response.get("chartType", "")
        cm = response.get("chartMain", {})

        # --- GRID 格式（所有图表类型通用）：有 row.meta 就算数据为空也能取到表头 ---
        if cm.get("row", {}).get("meta"):
            row_meta = cm.get("row", {}).get("meta", [])
            col_meta = cm.get("column", {}).get("meta", [])
            row_vals = cm.get("row", {}).get("values", [])
            col_vals = cm.get("column", {}).get("values", [])
            data_arr = cm.get("data", [])
            count = cm.get("count", len(row_vals))
            has_more = cm.get("hasMoreData", False)

            # 构建 headers
            headers = [m.get("title", "") for m in row_meta]
            if col_vals:
                for col in col_vals:
                    headers.append(" | ".join(c.get("title", "") for c in col))
            elif col_meta:
                for m in col_meta:
                    headers.append(m.get("title", "值"))

            # 构建 rows
            rows = []
            for i, rv in enumerate(row_vals):
                row = [c.get("title", "") or "" for c in rv]
                if i < len(data_arr):
                    for cell in data_arr[i]:
                        row.append(cell.get("v", "") if cell is not None else "")
                rows.append(row)

            return {
                "chartType": chart_type,
                "headers": headers,
                "rows": rows,
                "count": count,
                "hasMore": has_more,
            }

        # --- 指标卡等无 row 结构的类型 ---
        elif chart_type in ("SINGLE_VALUE", "KPI_CARD"):
            value = cm.get("data", [None])
            if isinstance(value, list) and value:
                value = value[0]
            return {
                "chartType": chart_type,
                "headers": ["指标值"],
                "rows": [[value.get("v", "") if isinstance(value, dict) else value]] if value else [],
                "count": 1 if value else 0,
                "hasMore": False,
            }

        # --- 完全没有 chartMain 或未知类型 ---
        else:
            raise ValueError(
                f'chartMain 为空或缺少 row.meta。'
                f'请检查观远卡片是否已正确配置图表类型和字段。'
            )

    async def create_card_smart(
        self,
        name: str,
        ds_id: str,
        chart_type: str,
        pg_id: Optional[str] = None,
        row: Optional[List] = None,
        column: Optional[List] = None,
        metric: Optional[List] = None,
        metric_additional: Optional[List] = None,
        size_by: Optional[List] = None,
        color_by: Optional[List] = None,
        filters: Optional[List] = None,
        sorting: Optional[List] = None,
        custom_fields: Optional[List[Dict]] = None,
        save: bool = True,
    ) -> Dict[str, Any]:
        """
        一步创建卡片（高层 API）

        LLM 只需提供字段名，内部自动完成 6 步流程。

        Args:
            name: 卡片名称
            ds_id: 数据集 ID
            chart_type: 图表类型 (PIVOT_TABLE / PIE / BASIC_COLUMN / BASIC_LINE 等)
            pg_id: 保存到的页面 ID（save=True 时必填）
            row: 行维度，如 ['城市', '门店名称']
            column: 列维度，如 ['渠道']
            metric: 数值，如 [
                {'name': '销售额', 'aggr': 'SUM'},
                {'name': '订单编码', 'aggr': 'CNT_DISTINCT', 'alias': '订单数'},
                {'name': '客单价'}  # 已有公式的计算字段，不需要 aggr
            ]
            filters: 筛选，如 [
                {'name': '状态', 'op': 'IN', 'value': ['营业中']},
                {'name': '销售额', 'op': 'GT', 'value': ['1400000']}
            ]
            sorting: 排序，如 [{'name': '销售额', 'order': 'DESC'}]
            custom_fields: 自定义公式字段，如 [{'name': '成本率', 'fdType': 'DOUBLE', 'formula': 'SUM([实付金额])/SUM([销售额])*100'}]
            save: 是否自动保存

        Returns:
            {'success': True, 'cdId': 'xxx', 'link': 'https://...'}
        """
        from zonedata_builder import create_zone_data

        # Step 0: 校验 chart_type + 多 metric 自动降级
        self._validate_chart_type(chart_type)

        _fallback_map = {
            "BASIC_COLUMN": "GROUPED_COLUMN",
            "BASIC_LINE": "MULTI_LINE",
            "BASIC_BAR": "STACKED_COLUMN",
            "SINGLE_VALUE": "KPI_CARD",
        }
        if metric and len(metric) > 1 and chart_type in _fallback_map:
            orig = chart_type
            chart_type = _fallback_map[orig]
            print(f'⚠️ {orig} 仅支持1个指标，已自动切换为 {chart_type}（{len(metric)}个指标）')

        # Step 1: 创建临时卡片
        r1 = await self.create_card(name=name, ds_id=ds_id, chart_type=chart_type)
        cd_id = r1["response"]["cdId"]

        # Step 2: 获取编辑会话
        r2 = await self.get_card_edit_session(cd_id)
        session_id = r2.get("sessionId") or r2.get("response", {}).get("sessionId")

        # Step 3: 获取字段信息
        r3 = await self.get_card_edit_info(cd_id)
        card_data = r3 if "dsInfo" in r3 else r3.get("response", r3)
        columns = card_data["dsInfo"]["columns"]

        # Step 3.5: 添加自定义公式字段
        if custom_fields:
            import httpx as _httpx
            async with _httpx.AsyncClient() as _client:
                for cf in custom_fields:
                    resp = await _client.post(
                        f"{self.base_url}/api/card/data-source/c/{cd_id}/session/{session_id}/column",
                        json=cf,
                        headers=self._get_headers(),
                    )
                    resp.raise_for_status()
                    result = resp.json()
                    # 返回值包含更新后的 columns 列表
                    new_cols = result.get("columns", [])
                    if new_cols:
                        columns = new_cols

        # 构建 name → 字段查找表
        name_lookup: Dict[str, Dict] = {}
        for col in columns:
            name_lookup[col["name"]] = col
            if col.get("alias"):
                name_lookup[col["alias"]] = col

        # SUB_DATE 粒度映射
        _gran_cn = {
            "年": "YEAR", "季度": "QUARTER", "月": "MONTH",
            "周": "WEEK", "日": "DAY", "星期": "DAYOFWEEK",
            "时": "HOUR", "分": "MINUTE", "秒": "SECOND",
        }

        def resolve(name_or_id: str) -> Dict:
            # 直接匹配
            if name_or_id in name_lookup:
                return name_lookup[name_or_id]
            # 按 fdId 查
            for col in columns:
                if col["fdId"] == name_or_id:
                    return col
            # 尝试解析 '营业日期(月)' 格式 → SUB_DATE 子字段
            # 格式: 字段名(日期颗粒类型)
            if "(" in name_or_id and name_or_id.endswith(")"):
                parent_name = name_or_id[:name_or_id.index("(")]
                sub_name = name_or_id[name_or_id.index("(") + 1:-1]
                gran = _gran_cn.get(sub_name)
                if gran and parent_name in name_lookup:
                    parent = name_lookup[parent_name]
                    return {
                        "fdId": f"{parent['fdId']}_{gran.lower()}",
                        "name": sub_name,
                        "fdType": "SUB_DATE",
                        "metaType": "DIM",
                        "parentFdName": parent_name,
                        "granularity": gran,
                        "isAggregated": False,
                        "calculationType": "normal",
                    }
            # 构建友好的错误提示
            all_names = sorted(name_lookup.keys())
            error_msg = f"❌ 字段 '{name_or_id}' 未找到\n"
            error_msg += f"\n可用字段共 {len(all_names)} 个:\n"
            
            # 分组显示：维度在前，指标在后
            dims = [n for n in all_names if name_lookup[n].get('metaType') == 'DIM']
            metrics = [n for n in all_names if name_lookup[n].get('metaType') == 'METRIC']
            
            if dims:
                error_msg += f"\n  维度 ({len(dims)} 个): {', '.join(dims[:30])}"
                if len(dims) > 30:
                    error_msg += f" ... 等共 {len(dims)} 个"
            if metrics:
                error_msg += f"\n  指标 ({len(metrics)} 个): {', '.join(metrics[:20])}"
                if len(metrics) > 20:
                    error_msg += f" ... 等共 {len(metrics)} 个"
            
            # 模糊匹配建议
            import difflib
            close_matches = difflib.get_close_matches(name_or_id, all_names, n=3, cutoff=0.4)
            if close_matches:
                error_msg += f"\n\n💡 你是不是想找: {', '.join(close_matches)}"
            
            raise ValueError(error_msg)

        # 组装 field_assignments
        assignments: List[Dict] = []

        for r in (row or []):
            f = resolve(r)
            assignments.append({"fdId": f["fdId"], "zoneId": "row"})

        # color_by — 颜色分组（气泡图/散点图）
        for c in (color_by or []):
            f = resolve(c if isinstance(c, str) else c["name"])
            assignments.append({"fdId": f["fdId"], "zoneId": "colorBy"})

        for c in (column or []):
            f = resolve(c)
            # 气泡图/散点图不支持 column zone
            if chart_type not in ("BASIC_BUBBLE", "BASIC_SCATTER_PLOT"):
                assignments.append({"fdId": f["fdId"], "zoneId": "column"})

        # 交叉表自动加 MPH
        if chart_type == "PIVOT_TABLE" and metric and (row or column):
            assignments.append({"fdId": "__MPH__", "zoneId": "column"})

        for m in (metric or []):
            f = resolve(m["name"])
            a: Dict[str, Any] = {"fdId": f["fdId"], "zoneId": "metric"}
            if f.get("isAggregated") and f.get("formula"):
                pass  # 已有公式的计算字段，不需要 aggrType
            elif m.get("aggr"):
                a["aggrType"] = m["aggr"]
            elif f["metaType"] == "METRIC":
                a["aggrType"] = "SUM"
            if m.get("alias"):
                a["alias"] = m["alias"]
            assignments.append(a)

        # metric_additional — 组合图的叠加图形数值
        for m in (metric_additional or []):
            f = resolve(m["name"])
            a = {"fdId": f["fdId"], "zoneId": "metric_additional"}
            if f.get("isAggregated") and f.get("formula"):
                pass
            elif m.get("aggr"):
                a["aggrType"] = m["aggr"]
            elif f["metaType"] == "METRIC":
                a["aggrType"] = "SUM"
            if m.get("alias"):
                a["alias"] = m["alias"]
            assignments.append(a)

        # size_by — 气泡图的气泡大小
        for m in (size_by or []):
            f = resolve(m["name"] if isinstance(m, dict) else m)
            a = {"fdId": f["fdId"], "zoneId": "sizeBy"}
            if f.get("isAggregated") and f.get("formula"):
                pass
            elif m.get("aggr"):
                a["aggrType"] = m["aggr"]
            elif f["metaType"] == "METRIC":
                a["aggrType"] = "SUM"
            if m.get("alias"):
                a["alias"] = m["alias"]
            assignments.append(a)

        for fl in (filters or []):
            f = resolve(fl["name"])
            # filterType 兼容映射：友好名称 → API 实际值
            _ft_map = {"NOT_IN": "NI", "NULL": "IS_NULL"}
            filter_type = _ft_map.get(fl["op"], fl["op"])
            assignments.append({
                "fdId": f["fdId"],
                "zoneId": "filters",
                "filterType": filter_type,
                "filterValue": fl["value"],
            })

        # 构建 fdId → 已有 assignment 的 zoneId/aggrType 查找表
        _sort_lookup = {}
        for a in assignments:
            if a["zoneId"] in ("row", "column", "metric", "metric_additional", "sizeBy", "colorBy"):
                _sort_lookup[a["fdId"]] = a

        for idx, s in enumerate(sorting or [], 1):
            f = resolve(s["name"])
            fd_id = f["fdId"]
            
            # 校验：排序字段必须在 row/column/metric/metric_additional/sizeBy/colorBy 中
            if fd_id not in _sort_lookup:
                _fdid_to_name = {c["fdId"]: c["name"] for c in columns}
                _available = [_fdid_to_name.get(a["fdId"], a["fdId"]) for a in assignments if a["zoneId"] in ("row", "column", "metric", "metric_additional", "sizeBy", "colorBy")]
                raise ValueError(f"排序字段 '{s['name']}' 不在 row/column/metric/metric_additional/sizeBy/colorBy 中，无法排序。可用字段: {_available}")
            
            # aggrType 确定逻辑：
            # 1. 排序字段在已有 row/column 中 → "NUL"
            # 2. 排序字段在 metric/metric_additional/sizeBy 中 → 复制它的 aggrType
            # 3. 计算字段 (isAggregated: True) → 不传 aggrType
            # 4. 其他 → "NUL"
            _aggr = "NUL"
            if fd_id in _sort_lookup:
                _existing = _sort_lookup[fd_id]
                if _existing["zoneId"] in ("row", "column"):
                    _aggr = "NUL"
                elif _existing.get("aggrType"):
                    _aggr = _existing["aggrType"]
            
            a = {
                "seqNo": idx,
                "calculationType": s.get("calculationType", "normal"),
                "editable": True,
                "level": "dataset",
                "zoneId": "sorting",
                "dsId": ds_id,
                "maxCount": s.get("maxCount", 20),
                "name": s.get("label") or s["name"],
                "isSensitive": False,
                "isAggregated": False,
                "ordering": s.get("order", "asc"),
                "fdType": f.get("fdType", "DOUBLE"),
                "fdId": fd_id,
                "key": f.get("fdId", ""),
                "metaType": f.get("metaType", "METRIC"),
            }
            # 计算字段不传 aggrType，其他传
            if not f.get("isAggregated"):
                a["aggrType"] = _aggr
            assignments.append(a)

        # Step 4: 构建 zoneData
        # 将动态创建的 SUB_DATE 字段注入 columns 供 builder 查找
        builder_columns = list(columns)
        for a in assignments:
            fd_id = a["fdId"]
            # 检查是否是动态 SUB_DATE（不在原始 columns 中）
            if fd_id.endswith(("_year", "_quarter", "_month", "_week", "_day", "_dayofweek")):
                exists = any(c["fdId"] == fd_id for c in builder_columns)
                if not exists:
                    # 从 fdId 反推父字段和粒度
                    for col in columns:
                        if fd_id.startswith(col["fdId"] + "_"):
                            gran = fd_id[len(col["fdId"]) + 1:].upper()
                            builder_columns.append({
                                "fdId": fd_id,
                                "name": col["name"],
                                "fdType": "SUB_DATE",
                                "metaType": "DIM",
                                "parentFdName": col["name"],
                                "granularity": gran,
                                "isAggregated": False,
                                "calculationType": "normal",
                            })
                            break

        # 图表类型配置（row/metric/column 上限，来源：观远平台实际 zoneInfo）
        CHART_CONFIG = {
            # 柱状图系列
            "BASIC_COLUMN":        {"row": -1, "metric": 1, "column": 0},
            "GROUPED_COLUMN":      {"row": -1, "metric": -1, "column": 1},
            "STACKED_COLUMN":      {"row": -1, "metric": -1, "column": 1},
            "PERCENT_STACKED_COLUMN": {"row": -1, "metric": -1, "column": 1},
            "WATERFALL_COLUMN":    {"row": -1, "metric": 1, "column": 0},
            "BULLET_COLUMN":       {"row": -1, "metric": 2, "column": 0},
            # 条形图
            "BASIC_BAR":           {"row": -1, "metric": 1, "column": 0},
            # 折线图
            "BASIC_LINE":          {"row": -1, "metric": 1, "column": 0},
            "MULTI_LINE":          {"row": -1, "metric": -1, "column": 1},
            # 面积图
            "STACKED_AREA":        {"row": 1, "metric": -1, "column": 1},
            "PERCENT_STACKED_AREA": {"row": 1, "metric": -1, "column": 1},
            # 组合图（柱+线）
            "STACKED_COLUMN_WITH_LINE":   {"row": 1, "metric": -1, "column": 1, "metric_additional": True},
            "GROUPED_COLUMN_WITH_LINE":   {"row": 1, "metric": -1, "column": 1, "metric_additional": True},
            "STACKED_COLUMN_WITH_SYMBOL": {"row": 1, "metric": -1, "column": 1, "metric_additional": True},
            "GROUPED_COLUMN_WITH_SYMBOL": {"row": 1, "metric": -1, "column": 1, "metric_additional": True},
            # 饼图/词云
            "PIE":                 {"row": 1, "metric": 1, "column": 0},
            "WORD_CLOUD":          {"row": 1, "metric": 1, "column": 0},
            # 其他
            "TREE_MAP":            {"row": -1, "metric": 1, "column": 0},
            "FUNNEL":              {"row": 0, "metric": -1, "column": 0},
            "SINGLE_VALUE":        {"row": 0, "metric": 1, "column": 0},
            "KPI_CARD":            {"row": 0, "metric": -1, "column": 0},
            "HEAT_MAP":            {"row": 1, "metric": 1, "column": 1},
            "MULTIDIMENSIONAL_SANKEY": {"row": -1, "metric": 1, "column": 0},
            "PIVOT_TABLE":         {"row": -1, "metric": -1, "column": -1},
            # 气泡图/散点图
            "BASIC_BUBBLE":        {"row": -1, "metric": 2, "column": 0},
            "BASIC_SCATTER_PLOT":  {"row": 1, "metric": 1, "column": 0},
        }

        cfg = CHART_CONFIG.get(chart_type, CHART_CONFIG["PIVOT_TABLE"])
        has_column = cfg["column"] != 0

        zone_info = [
            {"zoneId": "row", "title": "维度", "minCount": 0, "maxCount": cfg["row"], "needAggregation": False},
        ]
        if has_column:
            zone_info.append({"zoneId": "column", "title": "对比维度", "minCount": 0, "maxCount": cfg["column"], "needAggregation": False})
        zone_info.append({"zoneId": "metric", "title": "数值", "minCount": 0, "maxCount": cfg["metric"], "needAggregation": True})
        if cfg.get("metric_additional"):
            zone_info.append({"zoneId": "metric_additional", "title": "叠加图形数值", "minCount": 0, "maxCount": -1, "needAggregation": True, "setting": {"plotOn": "secondary"}})
        if chart_type == "BASIC_BUBBLE":
            zone_info.append({"zoneId": "sizeBy", "title": "气泡大小", "minCount": 0, "maxCount": 1, "needAggregation": True})
            zone_info.append({"zoneId": "colorBy", "minCount": 0, "maxCount": 1, "needAggregation": True})
            zone_info.append({"zoneId": "tooltip", "minCount": 0, "maxCount": 20, "needAggregation": True})
        zone_info.extend([
            {"zoneId": "filters", "title": "筛选", "minCount": 0, "maxCount": 20, "needAggregation": False},
            {"zoneId": "sorting", "title": "排序", "minCount": 0, "maxCount": 20, "needAggregation": True},
        ])

        zd_result = create_zone_data(
            zone_info=zone_info,
            ds_info={"columns": builder_columns, "dsId": ds_id},
            field_assignments=assignments,
        )

        # Step 5: 更新卡片配置
        config = copy.deepcopy(card_data)
        config["content"]["meta"]["chartMain"]["zoneInfo"] = zone_info
        config["content"]["meta"]["chartMain"]["zoneData"] = zd_result["zoneData"]
        config["name"] = name
        config.pop("dsInfo", None)
        config.pop("pgIds", None)
        config.pop("pgPaths", None)

        await self.update_card_config(cd_id, session_id, config)

        # Step 6: 保存
        if save and pg_id:
            await self.save_card(cd_id, session_id, pg_id)

        return {
            "success": True,
            "cdId": cd_id,
            "sessionId": session_id,
            "link": f"{self.base_url}/card/{cd_id}",
            "saved": save and pg_id is not None,
        }

#!/usr/bin/env python3
"""
观远BI CLI 工具 — 直接调用 client.py，不走 mcporter
用法: python3 guandata.py <command> [args...]

命令:
  list-datasets                    列出数据集
  get-columns <ds_id>              获取字段列表
  query <ds_id> [options]          查询数据（支持筛选）
  search-values <ds_id> <fd_id>    搜索字段枚举值
  list-pages                       列出页面
  create-card <json_params>        创建卡片（JSON参数）
  get-card-data <card_id>          获取卡片渲染数据
  delete-cards <card_ids...>       批量删除卡片
"""



def _print_api_error(e: httpx.HTTPStatusError) -> None:
    """解析 API 错误并打印友好提示"""
    status = e.response.status_code
    try:
        body = e.response.json()
        msg = body.get("error", {}).get("message", "")
    except Exception:
        msg = e.response.text[:200] if e.response.text else "(无响应内容)"

    print(f'❌ API 错误 ({status})')

    # 解析枚举错误，给出正确值提示
    if "Enumeration expected" in msg and "ChartType" in msg:
        print(f'   chart_type 值不合法')
        print(f'   共 {len(GuandataClient.VALID_CHART_TYPES)} 种:')
        for ct, desc in sorted(GuandataClient.VALID_CHART_TYPES.items()):
            print(f'   {ct:<35s} {desc}')
    elif "error.path.missing" in msg:
        # 缺少必填字段
        import re
        fields = re.findall(r'\(/(\w+)', msg)
        print(f'   缺少必填字段: {", ".join(fields)}')
    else:
        # 其他错误，截断显示
        print(f'   {msg[:300]}')


async def resolve_ds_id(client: GuandataClient, ds_input: str) -> str:
    """解析数据集输入：如果是名称则自动转为 ds_id"""
    # 如果输入已经是 ds_id 格式（24位hex），直接返回
    if re.match(r'^[a-f0-9]{24,32}$', ds_input):
        return ds_input
    
    # 否则从数据集列表中查找
    ds_list = await client.search_datasets_list()
    datasets = ds_list.get('contents', [])
    for ds in datasets:
        if ds.get('name') == ds_input or ds.get('dsId') == ds_input:
            ds_id = ds.get('dsId')
            print(f"📌 数据集名 '{ds_input}' → ds_id '{ds_id}'")
            return ds_id
    
    print(f"⚠️  未找到数据集 '{ds_input}'，按原值处理")
    return ds_input


async def cmd_list_datasets(args):
    client = GuandataClient()
    await client.login(GuandataClient.DEFAULT_DOMAIN, GuandataClient.DEFAULT_LOGIN_ID, GuandataClient.DEFAULT_LOGIN_SECRET)
    result = await client.search_datasets_list(use_cache=not args.refresh)
    datasets = result.get('contents', [])
    
    if args.json:
        print(json.dumps(datasets, ensure_ascii=False, indent=2))
        return
    
    print(f'共 {len(datasets)} 个数据集:\n')
    
    # 如果需要查询字段，先并行获取所有字段信息
    columns_cache = {}
    if args.columns:
        # 收集需要查询的数据集
        to_fetch = []
        for ds in datasets:
            ds_id = ds.get('dsId', '')
            ds_modify_time = ds.get('datasourceModifyTime', '')
            if not args.refresh and client._is_columns_cache_fresh(ds_id, ds_modify_time):
                cached = client._load_cached_columns(ds_id)
                columns_cache[ds_id] = cached.get('columns', [])
            else:
                to_fetch.append((ds_id, ds_modify_time))
        
        # 并行查询所有需要获取的字段
        if to_fetch:
            print(f'正在并行获取 {len(to_fetch)} 个数据集的字段信息...\n')
            
            async def fetch_columns(ds_id, modify_time):
                try:
                    result_cols = await client.get_dataset_columns(ds_id)
                    columns = result_cols.get('response', result_cols.get('contents', result_cols.get('columns', [])))
                    if isinstance(columns, list):
                        client._save_cached_columns(ds_id, columns, modify_time)
                    return ds_id, columns
                except Exception as e:
                    print(f'  ⚠️ 获取 {ds_id} 字段失败: {e}')
                    return ds_id, []
            
            # 并发执行所有查询（限制并发数为5，避免服务器压力过大）
            semaphore = asyncio.Semaphore(5)
            
            async def fetch_with_limit(ds_id, modify_time):
                async with semaphore:
                    return await fetch_columns(ds_id, modify_time)
            
            tasks = [fetch_with_limit(ds_id, mt) for ds_id, mt in to_fetch]
            results = await asyncio.gather(*tasks)
            
            for ds_id, columns in results:
                columns_cache[ds_id] = columns
    
    for ds in datasets:
        name = ds.get('name', '')
        ds_id = ds.get('dsId', '')
        rows = ds.get('rowCount', 0)
        cols = ds.get('colCount', 0)
        status = ds.get('status', '')
        path_parts = ds.get('dirPath', [])
        path = ' > '.join(p.get('dirName', '') for p in path_parts) if path_parts else ''
        parent_dir_id = ds.get('parentDirId', '')
        print(f'  {name}')
        desc = ds.get('description', '')
        print(f'    ID: {ds_id}  |  {rows:,}行  {cols}列  |  {status}')
        if parent_dir_id:
            print(f'    父文件夹ID: {parent_dir_id}')
        if desc:
            print(f'    描述: {desc}')
        if path:
            print(f'    路径: {path}')
        if args.columns:
            columns = columns_cache.get(ds_id, [])
            if isinstance(columns, list):
                for c in columns:
                    meta = c.get('metaType', '')
                    ftype = c.get('fdType', '')
                    fdid = c.get('fdId', '')
                    cname = c.get('name', '')
                    print(f'    {meta:6s} {ftype:10s} {fdid:26s} {cname}')
        print()


async def cmd_get_columns(args):
    client = GuandataClient()
    await client.login(GuandataClient.DEFAULT_DOMAIN, GuandataClient.DEFAULT_LOGIN_ID, GuandataClient.DEFAULT_LOGIN_SECRET)
    args.ds_id = await resolve_ds_id(client, args.ds_id)

    # 先拉数据集列表获取 datasourceModifyTime
    if not args.refresh:
        ds_list = await client.search_datasets_list()
        datasets = ds_list.get('contents', [])
        ds_modify_time = ''
        for ds in datasets:
            if ds.get('dsId') == args.ds_id:
                ds_modify_time = ds.get('datasourceModifyTime', '')
                break
        if ds_modify_time and client._is_columns_cache_fresh(args.ds_id, ds_modify_time):
            cached = client._load_cached_columns(args.ds_id)
            columns = cached.get('columns', [])
        else:
            result = await client.get_dataset_columns(args.ds_id)
            columns = result.get('response', result if isinstance(result, list) else [])
            if isinstance(columns, list):
                client._save_cached_columns(args.ds_id, columns, ds_modify_time)
    else:
        result = await client.get_dataset_columns(args.ds_id)
        columns = result.get('response', result if isinstance(result, list) else [])
        # 拿 datasourceModifyTime 一起存
        ds_list = await client.search_datasets_list()
        datasets = ds_list.get('contents', [])
        ds_modify_time = ''
        for ds in datasets:
            if ds.get('dsId') == args.ds_id:
                ds_modify_time = ds.get('datasourceModifyTime', '')
                break
        if isinstance(columns, list):
            client._save_cached_columns(args.ds_id, columns, ds_modify_time)
    
    # 始终获取计算字段
    virtual = await client.get_dataset_virtual_columns(args.ds_id)

    # 自动排除含 DYNAMIC_PARAMS 的字段（这些字段API调用下不可用）
    all_cols_check = columns[:] + (virtual or [])
    dynamic_names = {c['name'] for c in all_cols_check if 'DYNAMIC_PARAMS' in c.get('formula', '')}
    if dynamic_names:
        columns = [c for c in columns if c.get('name') not in dynamic_names]
        virtual = [c for c in (virtual or []) if c.get('name') not in dynamic_names]

    if args.json:
        all_cols = columns[:] + (virtual or [])
        print(json.dumps(all_cols, ensure_ascii=False, indent=2))
        return

    print(f'共 {len(columns)} 个原始字段:\n')
    for col in columns:
        name = col.get('name', '')
        fd_id = col.get('fdId', '')
        fd_type = col.get('fdType', '')
        meta_type = col.get('metaType', '')
        print(f'  {meta_type:6s} {fd_type:12s} {fd_id:30s} {name}')

    if virtual:
        print(f'\n共 {len(virtual)} 个计算字段:\n')
        for col in virtual:
            name = col.get('name', '')
            fd_id = col.get('fdId', '')
            fd_type = col.get('fdType', '')
            formula = col.get('formula', '')
            print(f'  METRIC {fd_type:12s} {fd_id:30s} {name}')
            print(f'         formula: {formula}')


async def cmd_query(args):
    # 限制查询行数
    if args.limit > 50000:
        print(f'❌ 单次查询上限 50,000 行，你请求了 {args.limit:,} 行')
        print(f'   如需更多数据，请分页查询: --offset 0 --limit 50000, 然后 --offset 50000 ...')
        sys.exit(1)
    if args.limit > 1000 and not args.force:
        print(f'⚠️ 查询 {args.limit:,} 行数据量较大，可能较慢')
        print(f'   确认请加 --force 参数: python3 guandata.py query {args.ds_id} --limit {args.limit} --force')
        sys.exit(1)
    
    client = GuandataClient()
    await client.login(GuandataClient.DEFAULT_DOMAIN, GuandataClient.DEFAULT_LOGIN_ID, GuandataClient.DEFAULT_LOGIN_SECRET)
    args.ds_id = await resolve_ds_id(client, args.ds_id)
    
    filter_obj = None
    if args.filter:
        try:
            filter_obj = json.loads(args.filter)
        except json.JSONDecodeError as e:
            print(f'❌ filter 不是合法 JSON: {e}')
            print(f'   正确格式:')
            print(f'   \'{{"combineType":"AND","conditions":[{{"type":"condition","fdId":"字段fdId","filterType":"EQ","value":["值"]}}]}}\'')
            sys.exit(1)
        # 校验 filter 结构
        if not isinstance(filter_obj, dict) or "combineType" not in filter_obj:
            print('❌ filter 格式错误，缺少 combineType')
            print(f'   正确格式:')
            print(f'   \'{{"combineType":"AND","conditions":[{{"type":"condition","fdId":"字段fdId","filterType":"EQ","value":["值"]}}]}}\'')
            sys.exit(1)
    
    result = await client.get_dataset_data(
        ds_id=args.ds_id,
        offset=args.offset,
        limit=args.limit,
        filter=filter_obj,
        save_local=args.save,
        output_dir=args.output_dir,
    )

    # 保存到本地缓存 (CSV)
    response = result.get('response', result)
    columns = response.get('columns', [])
    preview = response.get('preview', [])
    col_names = [c.get('name', '') for c in columns]
    csv_path = client._save_to_cache_csv(col_names, preview, f"query_{args.ds_id[:8]}")

    if args.json:
        result['_cache_path'] = csv_path
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    # 提取关键信息
    response = result.get('response', result)
    total = response.get('rowCount', 0)
    preview = response.get('preview', [])
    columns = response.get('columns', [])
    
    print(f'总行数: {total:,}')
    print(f'返回行数: {len(preview)}')
    
    if columns and preview:
        # 打印表头
        col_names = [c.get('name', '') for c in columns[:args.display_cols]]
        print('\n' + ' | '.join(col_names))
        print('-' * (len(col_names) * 20))
        
        # 打印数据
        for row in preview[:args.display_rows]:
            vals = []
            for cell in row[:args.display_cols]:
                if isinstance(cell, dict):
                    vals.append(str(cell.get('v', '')))
                else:
                    vals.append(str(cell))
            print(' | '.join(vals))

    print(f'\n📁 缓存: {csv_path}')


async def cmd_search_values(args):
    if not args.ds_id:
        print('❌ 缺少 ds_id')
        print(f'   用法: python3 guandata.py search-values <ds_id> <fd_id> [--search "关键词"]')
        print(f'   或:   python3 guandata.py search-values <ds_id> --name "字段名" [--search "关键词"]')
        sys.exit(1)

    fd_id = args.fd_id

    # 通过字段名解析 fdId
    if not fd_id and args.name:
        client_tmp = GuandataClient()
        await client_tmp.login(GuandataClient.DEFAULT_DOMAIN, GuandataClient.DEFAULT_LOGIN_ID, GuandataClient.DEFAULT_LOGIN_SECRET)
        # 先尝试缓存
        cached = client_tmp._load_cached_columns(args.ds_id)
        if cached:
            columns = cached.get('columns', [])
        else:
            result = await client_tmp.get_dataset_columns(args.ds_id)
            columns = result.get('response', result if isinstance(result, list) else [])
        # 精确匹配字段名
        for col in columns:
            if col.get('name') == args.name or col.get('alias') == args.name:
                fd_id = col['fdId']
                break
        # 模糊匹配
        if not fd_id:
            matches = [c for c in columns if args.name.lower() in c.get('name', '').lower()]
            if len(matches) == 1:
                fd_id = matches[0]['fdId']
            elif len(matches) > 1:
                print(f'❌ 字段名 "{args.name}" 匹配到多个字段:')
                for m in matches[:10]:
                    print(f'   {m["name"]}')
                sys.exit(1)
        if not fd_id:
            print(f'❌ 字段 "{args.name}" 未找到')
            
            # 分组显示所有维度
            all_dims = [c['name'] for c in columns if c.get('metaType') == 'DIM']
            print(f'   可用维度共 {len(all_dims)} 个:')
            print(f'   {", ".join(all_dims[:30])}', end='')
            if len(all_dims) > 30:
                print(f' ... 等', end='')
            print()
            
            # 模糊匹配建议
            import difflib
            close_matches = difflib.get_close_matches(args.name, all_dims, n=3, cutoff=0.4)
            if close_matches:
                print(f'\n💡 你是不是想找: {", ".join(close_matches)}')
            sys.exit(1)

    if not fd_id:
        print('❌ 缺少 fd_id 或 --name')
        print(f'   用法: python3 guandata.py search-values <ds_id> <fd_id> [--search "关键词"]')
        print(f'   或:   python3 guandata.py search-values <ds_id> --name "字段名" [--search "关键词"]')
        sys.exit(1)

    client = GuandataClient()
    await client.login(GuandataClient.DEFAULT_DOMAIN, GuandataClient.DEFAULT_LOGIN_ID, GuandataClient.DEFAULT_LOGIN_SECRET)
    result = await client.search_column_values(
        ds_id=args.ds_id,
        fd_id=fd_id,
        search=args.search or '',
        limit=args.limit,
    )
    
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    items = result.get('result', [])
    count = result.get('count', 0)
    print(f'共 {count} 个值{"（超过限制）" if result.get("exceedLimit") else ""}:\n')
    for item in items[:50]:
        if isinstance(item, list):
            print(f'  {item[0]}')
        else:
            print(f'  {item}')


async def cmd_list_pages(args):
    client = GuandataClient()
    await client.login(GuandataClient.DEFAULT_DOMAIN, GuandataClient.DEFAULT_LOGIN_ID, GuandataClient.DEFAULT_LOGIN_SECRET)
    result = await client.search_pages()
    
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    # 收集所有页面（扁平化）
    def collect_pages(items, results=None):
        if results is None:
            results = []
        for p in items:
            is_page = p.get('isPage', False)
            can_manage = p.get('canManage', False)
            if is_page:
                results.append({
                    'name': p.get('name', ''),
                    'id': p.get('id', ''),
                    'canManage': can_manage,
                })
            children = p.get('contents', [])
            if children:
                collect_pages(children, results)
        return results
    
    root_contents = result.get('contents', [])
    
    if args.manageable:
        # 只显示有编辑权限的页面
        all_pages = collect_pages(root_contents)
        manageable = [p for p in all_pages if p['canManage']]
        if not manageable:
            print('没有找到有编辑权限的页面')
            return
        print(f'共 {len(manageable)} 个可编辑页面:\n')
        for p in manageable:
            print(f'  ✅ {p["name"]}  ({p["id"]})')
    else:
        # 显示完整树形结构
        def show_pages(items, indent=0):
            for p in items:
                name = p.get('name', '')
                pg_id = p.get('id', '')
                is_page = p.get('isPage', False)
                can_manage = p.get('canManage', False)
                children = p.get('contents', [])
                prefix = '📄' if is_page else '📁'
                mark = ' ✅' if is_page and can_manage else ''
                print(f'{"  " * indent}{prefix} {name}  ({pg_id}){mark}')
                if children:
                    show_pages(children, indent + 1)
        
        show_pages(root_contents)


async def cmd_create_page(args):
    """创建BI页面"""
    client = GuandataClient()
    await client.login(GuandataClient.DEFAULT_DOMAIN, GuandataClient.DEFAULT_LOGIN_ID, GuandataClient.DEFAULT_LOGIN_SECRET)

    result = await client.create_page(
        name=args.name,
        parent_dir_id=args.parent_dir,
        description=args.desc or "",
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    pg_id = result.get("pgId", "")
    if pg_id:
        print(f'✅ 页面已创建: {client.base_url}/page/{pg_id}')
        print(f'   pg_id: {pg_id}')
    else:
        print(f'❌ 创建失败: {json.dumps(result, ensure_ascii=False)}')


async def cmd_get_page_cards(args):
    """获取页面卡片列表"""
    if not args.pg_id:
        print('❌ 缺少 pg_id')
        print(f'   用法: python3 guandata.py get-page-cards <pg_id> [--json]')
        sys.exit(1)

    client = GuandataClient()
    await client.login(GuandataClient.DEFAULT_DOMAIN, GuandataClient.DEFAULT_LOGIN_ID, GuandataClient.DEFAULT_LOGIN_SECRET)
    result = await client.get_page_cards(args.pg_id)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    cd_ids = result.get('cdIds', [])
    print(f'页面 {args.pg_id}: {len(cd_ids)} 张卡片')
    for cd_id in cd_ids:
        print(f'  - {cd_id}')


async def cmd_create_card(args):
    """创建卡片 — 直接调用 client.create_card_smart"""
    client = GuandataClient()
    await client.login(GuandataClient.DEFAULT_DOMAIN, GuandataClient.DEFAULT_LOGIN_ID, GuandataClient.DEFAULT_LOGIN_SECRET)

    try:
        params = json.loads(args.params_json)
    except json.JSONDecodeError as e:
        print(f'❌ 参数不是合法 JSON: {e}')
        print(f'   正确格式: \'{{"name":"卡片名","ds_id":"数据集ID","chart_type":"PIVOT_TABLE","pg_id":"页面ID",...}}\'')
        sys.exit(1)

    # 必填校验
    missing = [k for k in ('name', 'ds_id', 'chart_type') if k not in params]
    if missing:
        print(f'❌ 缺少必填参数: {", ".join(missing)}')
        print(f'   最少需要: name, ds_id, chart_type, pg_id（保存时需要）')
        sys.exit(1)

    GuandataClient._validate_chart_type(params['chart_type'])

    result = await client.create_card_smart(
        name=params['name'],
        ds_id=params['ds_id'],
        chart_type=params['chart_type'],
        pg_id=params.get('pg_id'),
        row=params.get('row'),
        column=params.get('column'),
        metric=params.get('metric'),
        filters=params.get('filters'),
        sorting=params.get('sorting'),
        custom_fields=params.get('custom_fields'),
        save=params.get('save', True),
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


async def cmd_get_card_data(args):
    client = GuandataClient()
    await client.login(GuandataClient.DEFAULT_DOMAIN, GuandataClient.DEFAULT_LOGIN_ID, GuandataClient.DEFAULT_LOGIN_SECRET)

    if not args.card_id:
        print('❌ 缺少 card_id')
        print(f'   用法: python3 guandata.py get-card-data <card_id> [--json] [--limit 10]')
        sys.exit(1)

    PAGE_SIZE = 500
    result = await client.get_card_data(
        card_id=args.card_id,
        view=args.view,
        offset=0,
        limit=PAGE_SIZE,
    )

    # PIVOT_TABLE 自动分页
    response = result.get('response', result)
    chart_main = response.get('chartMain', {})
    if 'data' in chart_main and chart_main.get('row', {}).get('values'):
        row_vals = chart_main['row']['values']
        data_arr = chart_main['data']
        count = chart_main.get('count', len(row_vals))
        data_limit = 5000  # 软限制：卡片数据最多返回5000行

        offset = PAGE_SIZE
        while offset < count and offset < data_limit:
            # 打印进度
            progress = min(offset, count) / count * 100
            print(f'  获取数据中... {min(offset, count):,} / {count:,} 行 ({progress:.0f}%)', end='\r')
            
            next_page = await client.get_card_data(
                card_id=args.card_id, view=args.view,
                offset=offset, limit=PAGE_SIZE,
            )
            next_cm = next_page.get('response', next_page).get('chartMain', {})
            next_rows = next_cm.get('row', {}).get('values', [])
            next_data = next_cm.get('data', [])
            if not next_rows:
                break
            row_vals.extend(next_rows)
            data_arr.extend(next_data)
            offset += PAGE_SIZE
        
        # 清除进度行
        print(' ' * 50, end='\r')

        if len(row_vals) < count:
            print(f'⚠️ 已返回 {len(row_vals)} 行，总计 {count} 行（上限 {data_limit}），请加筛选条件缩小范围\n')

        chart_main['row']['values'] = row_vals
        chart_main['data'] = data_arr

    # 统一格式输出
    norm = client.normalize_card_data(result)

    # 保存到本地缓存 (CSV)
    csv_path = client._save_to_cache_csv(norm['headers'], norm['rows'], f"card_{args.card_id[:8]}")

    if args.json:
        norm['_raw'] = result
        norm['_cache_path'] = csv_path
        print(json.dumps(norm, ensure_ascii=False, indent=2))
        return

    # 获取卡片配置（维度、指标、筛选条件）
    try:
        edit_info = await client.get_card_edit_info(args.card_id)
        card_name = edit_info.get('name', '')
        content = edit_info.get('content', {})
        meta = content.get('meta', {})
        if isinstance(meta, str):
            meta = json.loads(meta)
        zone_data = meta.get('chartMain', {}).get('zoneData', {})

        if card_name:
            print(f'卡片名称: {card_name}')

        # 维度
        rows = zone_data.get('row', [])
        if rows:
            print(f'维度: {", ".join(r.get("name","") for r in rows)}')

        # 指标
        metrics = zone_data.get('metric', [])
        if metrics:
            m_strs = []
            for m in metrics:
                aggr = m.get('aggr', '')
                name = m.get('name', '')
                m_strs.append(f'{aggr}({name})' if aggr else name)
            print(f'指标: {", ".join(m_strs)}')

        # 筛选条件
        filters = zone_data.get('filters', [])
        if filters:
            print(f'筛选条件:')
            for f in filters:
                fname = f.get('name', '')
                ftype = f.get('filterType', '')
                fval = f.get('filterValue', [])
                if ftype == 'BT':
                    print(f'  {fname}: {fval[0]} ~ {fval[1]}')
                elif ftype == 'GE':
                    print(f'  {fname} >= {fval[0] if fval else ""}')
                elif ftype == 'LE':
                    print(f'  {fname} <= {fval[0] if fval else ""}')
                elif ftype == 'GT':
                    print(f'  {fname} > {fval[0] if fval else ""}')
                elif ftype == 'LT':
                    print(f'  {fname} < {fval[0] if fval else ""}')
                elif ftype == 'NE':
                    print(f'  {fname} != {fval[0] if fval else ""}')
                elif ftype == 'IN':
                    print(f'  {fname}: {", ".join(str(v) for v in fval)}')
                elif ftype == 'EQ':
                    print(f'  {fname} = {fval[0] if fval else ""}')
                elif ftype == 'NOT_IN':
                    print(f'  {fname} not in: {", ".join(str(v) for v in fval)}')
                elif ftype == 'NULL':
                    print(f'  {fname} 为空')
                elif ftype == 'NOT_NULL':
                    print(f'  {fname} 不为空')
                elif ftype == 'LIKE':
                    print(f'  {fname} like {fval[0] if fval else ""}')
                else:
                    print(f'  {fname} {ftype} {fval}')
        else:
            print('筛选条件: 无')
        print()
    except Exception as e:
        print(f'⚠️ 卡片配置获取失败: {type(e).__name__}: {e}')
        print('(仅显示数据)\n')

    print(f'返回行数: {len(norm["rows"])}')
    print()
    print(client._format_table(norm['headers'], norm['rows'], max_rows=args.display_rows))
    print(f'\n📁 缓存: {csv_path}')


async def cmd_delete_cards(args):
    if not args.pg_id:
        print('❌ 缺少 pg_id')
        print(f'   用法: python3 guandata.py delete-cards <pg_id> <card_id1> [card_id2] ...')
        sys.exit(1)
    if not args.card_ids:
        print('❌ 缺少 card_id 列表')
        print(f'   用法: python3 guandata.py delete-cards <pg_id> <card_id1> [card_id2] ...')
        sys.exit(1)

    client = GuandataClient()
    await client.login(GuandataClient.DEFAULT_DOMAIN, GuandataClient.DEFAULT_LOGIN_ID, GuandataClient.DEFAULT_LOGIN_SECRET)
    result = await client.batch_delete_cards(args.card_ids, args.pg_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))


async def cmd_release_page(args):
    """手动发布页面（7.0+ 版本专用）"""
    if not args.pg_id:
        print('❌ 缺少 pg_id')
        print(f'   用法: python3 guandata.py release-page <pg_id>')
        sys.exit(1)

    client = GuandataClient()
    await client.login(GuandataClient.DEFAULT_DOMAIN, GuandataClient.DEFAULT_LOGIN_ID, GuandataClient.DEFAULT_LOGIN_SECRET)
    result = await client.release_page(args.pg_id)
    
    if 'error' in result:
        print(f'❌ 发布失败: {result["error"]}')
    else:
        print(f'✅ 页面 {args.pg_id} 发布成功')
        print(json.dumps(result, ensure_ascii=False, indent=2))


async def cmd_clean_cache(args):
    """清理过期缓存文件"""
    import glob
    from datetime import datetime, timedelta

    days = args.days
    cutoff = datetime.now() - timedelta(days=days)
    total_freed = 0
    total_deleted = 0

    # 要清理的目录列表
    cache_root = os.path.join(GuandataClient.SKILL_ROOT, '.cache')
    dirs_to_clean = []
    for sub in ('data', 'columns'):
        p = os.path.join(cache_root, sub)
        if os.path.isdir(p):
            dirs_to_clean.append(p)

    # 也清理 tasks 下的缓存
    tasks_dir = os.path.join(cache_root, 'tasks')
    if os.path.exists(tasks_dir):
        for task_sub in os.listdir(tasks_dir):
            for sub in ('data', 'columns'):
                p = os.path.join(tasks_dir, task_sub, sub)
                if os.path.isdir(p):
                    dirs_to_clean.append(p)

    for cache_dir in dirs_to_clean:
        for f in os.listdir(cache_dir):
            fpath = os.path.join(cache_dir, f)
            if not os.path.isfile(fpath):
                continue
            # 从文件名解析时间戳: prefix_YYYYMMDD_HHMMSS_xxx.ext
            m = None
            parts = f.split('_')
            for part in parts:
                try:
                    m = datetime.strptime(part[:8], '%Y%m%d')
                    break
                except ValueError:
                    continue
            if m and m < cutoff:
                size = os.path.getsize(fpath)
                os.remove(fpath)
                total_deleted += 1
                total_freed += size

    freed_mb = total_freed / 1024 / 1024
    print(f'🧹 清理完成：删除 {total_deleted} 个文件，释放 {freed_mb:.1f} MB')
    print(f'   保留 {days} 天内的文件')


async def cmd_create_and_get(args):
    """一步创建卡片并获取渲染数据"""
    import time
    client = GuandataClient()
    await client.login(GuandataClient.DEFAULT_DOMAIN, GuandataClient.DEFAULT_LOGIN_ID, GuandataClient.DEFAULT_LOGIN_SECRET)

    try:
        params = json.loads(args.params_json)
    except json.JSONDecodeError as e:
        print(f'❌ 参数不是合法 JSON: {e}')
        print(f'   正确格式:')
        print(f'   \'{{"name":"卡片名","ds_id":"数据集ID","chart_type":"PIVOT_TABLE","pg_id":"页面ID","row":["城市"],"metric":[{{"name":"销售额","aggr":"SUM"}}],"filters":[{{"name":"营业日期","op":"EQ","value":["2026-03-26"]}}]}}\'')
        sys.exit(1)

    # pg_id 缺失时自动使用配置文件的 default_pg_id
    if 'pg_id' not in params:
        default_pg = _CFG.get('default_pg_id', '')
        if default_pg:
            params['pg_id'] = default_pg

    # 必填校验
    missing = [k for k in ('name', 'ds_id', 'chart_type', 'pg_id') if k not in params]
    if missing:
        print(f'❌ 缺少必填参数: {", ".join(missing)}')
        print(f'   需要: name, ds_id, chart_type, pg_id')
        sys.exit(1)

    GuandataClient._validate_chart_type(params['chart_type'])

    # 解析 ds_id（支持名称→ID自动转换）
    params['ds_id'] = await resolve_ds_id(client, params['ds_id'])

    # 建卡
    try:
        result = await client.create_card_smart(
            name=params['name'],
            ds_id=params['ds_id'],
            chart_type=params['chart_type'],
        pg_id=params['pg_id'],
        row=params.get('row'),
        column=params.get('column'),
        metric=params.get('metric'),
        filters=params.get('filters'),
        sorting=params.get('sorting'),
        custom_fields=params.get('custom_fields'),
        save=True,
    )
    except httpx.HTTPStatusError as e:
        _print_api_error(e)
        sys.exit(1)

    if not result.get('success'):
        print(f'❌ 建卡失败: {json.dumps(result, ensure_ascii=False)}')
        sys.exit(1)

    card_id = result['cdId']

    # 重试取数（避免盲等）
    for attempt in range(args.retries):
        time.sleep(2)
        try:
            PAGE_SIZE = 500  # 每次分页大小
            data = await client.get_card_data(card_id=card_id, view='GRID', limit=PAGE_SIZE)
            response = data.get('response', data)
            chart_main = response.get('chartMain', {})
            chart_type = response.get('chartType', '')

            # ========== 交叉表/热力图：自动分页 ==========
            if 'data' in chart_main and chart_main.get('row', {}).get('values'):
                row_vals = chart_main['row']['values']
                data_arr = chart_main['data']
                count = chart_main.get('count', len(row_vals))
                limit_info = chart_main.get('limitInfo', {})
                data_limit = 5000  # 软限制：卡片数据最多返回5000行

                # 自动分页：如果 count > 已返回行数
                offset = PAGE_SIZE
                while offset < count and offset < data_limit:
                    # 打印进度
                    progress = min(offset, count) / count * 100
                    print(f'  获取数据中... {min(offset, count):,} / {count:,} 行 ({progress:.0f}%)', end='\r')
                    
                    next_page = await client.get_card_data(
                        card_id=card_id, view='GRID',
                        offset=offset, limit=PAGE_SIZE,
                    )
                    next_cm = next_page.get('response', next_page).get('chartMain', {})
                    next_rows = next_cm.get('row', {}).get('values', [])
                    next_data = next_cm.get('data', [])
                    if not next_rows:
                        break
                    row_vals.extend(next_rows)
                    data_arr.extend(next_data)
                    offset += PAGE_SIZE
                
                # 清除进度行
                print(' ' * 50, end='\r')

                if len(row_vals) < count:
                    print(f'⚠️ 已返回 {len(row_vals)} 行，总计 {count} 行（上限 {data_limit}），请加筛选条件缩小范围\n')

                # 覆盖回 chart_main 供 normalize 用
                chart_main['row']['values'] = row_vals
                chart_main['data'] = data_arr

            # 统一格式输出
            norm = client.normalize_card_data(data)

            # 保存到本地缓存 (CSV)
            csv_path = client._save_to_cache_csv(norm['headers'], norm['rows'], f"create_{params.get('ds_id','')[:8]}")

            if not args.json:
                if norm['count'] == 0:
                    print(f'⚠️ 建卡成功但数据为空（count=0），请检查筛选条件')
                else:
                    print(f'返回行数: {len(norm["rows"])}')
                    print()
                    print(client._format_table(norm['headers'], norm['rows'], max_rows=50))

            if args.json:
                data['_create_result'] = result
                data['_normalized'] = norm
                data['_cache_path'] = csv_path
                print(f'\n---JSON---\n{json.dumps(data, ensure_ascii=False)}')

            print(f'\n卡片: {result.get("link")}')
            if norm['count'] > 0:
                print(f'📁 缓存: {csv_path}')
            return

        except httpx.TimeoutException:
            if attempt < args.retries - 1:
                print(f'  取数超时，第 {attempt+1}/{args.retries} 次重试...')
                continue
            print(f'⚠️ 建卡成功但取数超时（网络/连接问题），请手动查看: {result.get("link")}')
            return
        except Exception as e:
            if attempt < args.retries - 1:
                print(f'  取数异常（{type(e).__name__}: {e}），第 {attempt+1}/{args.retries} 次重试...')
                continue
            print(f'⚠️ 建卡成功但取数失败（{type(e).__name__}: {e}），请手动查看: {result.get("link")}')
            return


def main():
    parser = argparse.ArgumentParser(description='观远BI CLI工具')
    parser.add_argument('--task', help='任务名，用于隔离不同任务的缓存（默认使用共享缓存）')
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # list-datasets
    p = subparsers.add_parser('list-datasets', help='列出数据集')
    p.add_argument('--refresh', action='store_true', help='强制刷新缓存')
    p.add_argument('--json', action='store_true', help='输出JSON')
    p.add_argument('--columns', action='store_true', help='同时显示每个数据集的字段')
    
    # get-columns
    p = subparsers.add_parser('get-columns', help='获取字段列表')
    p.add_argument('ds_id', help='数据集ID')
    p.add_argument('--json', action='store_true', help='输出JSON')
    p.add_argument('--refresh', action='store_true', help='强制刷新缓存')
    p.add_argument('--with-calc', action='store_true', help='同时显示计算字段(virtualColumns)')
    
    # query
    p = subparsers.add_parser('query', help='查询数据')
    p.add_argument('ds_id', help='数据集ID')
    p.add_argument('--filter', '-f', help='筛选条件JSON')
    p.add_argument('--offset', type=int, default=0)
    p.add_argument('--limit', type=int, default=10)
    p.add_argument('--force', action='store_true', default=False, help='导出超过1000行时需要此参数确认')
    p.add_argument('--save', action='store_true', default=False)
    p.add_argument('--output-dir', default='./data')
    p.add_argument('--display-cols', type=int, default=10, help='显示列数')
    p.add_argument('--display-rows', type=int, default=20, help='显示行数')
    p.add_argument('--json', action='store_true', help='输出JSON')
    
    # search-values
    p = subparsers.add_parser('search-values', help='搜索字段枚举值')
    p.add_argument('ds_id', help='数据集ID')
    p.add_argument('fd_id', nargs='?', help='字段ID（可选，可用 --name 替代）')
    p.add_argument('--name', '-n', help='字段名（自动解析 fdId）')
    p.add_argument('--search', '-s', help='搜索关键词')
    p.add_argument('--limit', type=int, default=200)
    p.add_argument('--json', action='store_true', help='输出JSON')
    
    # list-pages
    p = subparsers.add_parser('list-pages', help='列出页面')
    p.add_argument('--json', action='store_true', help='输出JSON')
    p.add_argument('--manageable', action='store_true', help='只显示有编辑权限(canManage)的页面')

    # create-page
    p = subparsers.add_parser('create-page', help='创建BI页面')
    p.add_argument('name', help='页面名称')
    p.add_argument('--parent-dir', help='父目录ID')
    p.add_argument('--desc', help='页面描述')
    p.add_argument('--json', action='store_true', help='输出JSON')
    
    # create-card
    p = subparsers.add_parser('create-card', help='创建卡片')
    p.add_argument('params', help='JSON参数（name, ds_id, chart_type, pg_id, row, column, metric, filters, sorting）')
    
    # get-card-data
    p = subparsers.add_parser('get-card-data', help='获取卡片数据')
    p.add_argument('card_id', help='卡片ID')
    p.add_argument('--view', default='GRID', help='视图类型')
    p.add_argument('--limit', type=int, default=200)
    p.add_argument('--display-rows', type=int, default=50, help='显示行数')
    p.add_argument('--json', action='store_true', help='输出JSON')
    
    # get-page-cards
    p = subparsers.add_parser('get-page-cards', help='获取页面卡片列表')
    p.add_argument('pg_id', help='页面ID')
    p.add_argument('--json', action='store_true', help='输出JSON')

    # delete-cards
    p = subparsers.add_parser('delete-cards', help='批量删除卡片')
    p.add_argument('pg_id', help='页面ID')
    p.add_argument('card_ids', nargs='+', help='卡片ID列表')

    # release-page — 手动发布页面（7.0+）
    p = subparsers.add_parser('release-page', help='发布页面（7.0+ 版本专用）')
    p.add_argument('pg_id', help='页面ID')

    # create-and-get — 一步建卡+取数
    p = subparsers.add_parser('create-and-get', help='一步创建卡片并获取数据')
    p.add_argument('params_json', help='卡片参数JSON字符串')
    p.add_argument('--limit', type=int, default=100, help='最大返回行数')
    p.add_argument('--retries', type=int, default=3, help='取数重试次数')
    p.add_argument('--json', action='store_true', help='输出JSON')

    p = subparsers.add_parser('clean-cache', help='清理过期缓存（默认保留7天）')
    p.add_argument('--days', type=int, default=7, help='保留最近N天的缓存')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # 设置会话ID（用于缓存隔离）
    if args.task:
        GuandataClient.set_task(args.task)
    
    cmd_map = {
        'list-datasets': cmd_list_datasets,
        'get-columns': cmd_get_columns,
        'query': cmd_query,
        'search-values': cmd_search_values,
        'list-pages': cmd_list_pages,
        'create-page': cmd_create_page,
        'get-page-cards': cmd_get_page_cards,
        'create-card': cmd_create_card,
        'get-card-data': cmd_get_card_data,
        'delete-cards': cmd_delete_cards,
        'create-and-get': cmd_create_and_get,
        'clean-cache': cmd_clean_cache,
        'release-page': cmd_release_page,
    }
    
    asyncio.run(cmd_map[args.command](args))


if __name__ == '__main__':
    main()
