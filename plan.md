# 项目规划（迭代版）

## 阶段一：路径与成本计算（当前重点）

### 目标

- 将 `微信open_id` 视为司机标识，梳理每日、每次送货的打卡轨迹
- 调用高德路径规划 API 获取相邻站点的行驶距离，形成公里成本核算
- 产出清晰的数据表，包含可变参数、固定参数与原始采集信息，便于后续应用读取

### 数据理解与准备

- 原始关键字段：`订单号`、`微信open_id`、`提交时间`、`经度`、`纬度`、`送货地址`、`收货方名称`、`收货方编码`
- 为便于处理，将字段重命名为英文（例如 `order_id`、`driver_open_id`、`timestamp`、`lng`、`lat` 等）并统一编码
- 对 `提交时间` 解析为带时区的 datetime，派生 `date`（自然日）作为成本统计维度
- 按司机+日期进行初步聚合，统计打卡次数、首末位置、是否存在重复坐标或缺失值

### 数据清洗流程

1. 导入 CSV：使用 `pandas`（指定 `encoding="utf-8-sig"`）或 `polars`，校验列名与类型
2. 坐标标准化：将经纬度字段强制为浮点；若存在空值，记录异常并准备人工补录
3. 去重规则：同一司机在相同时间戳、相同坐标的记录视为重复；保留最先上传的一条
4. 门店统一：优先使用 `收货方编码`，若为空则回退至 `收货方名称` 或 `送货地址`；生成 `store_id`
5. 轨迹排序：对每位司机在同一天内按 `timestamp` 升序排列，得到站点序列（Stop 1, Stop 2...）
6. 质检输出：沉淀一份数据质量报告（缺失坐标、重复打卡、距离异常 >200km 等）

### 路径 & API 计算策略

- 使用高德“驾车路径规划”API（`https://restapi.amap.com/v3/direction/driving`）
  - 入参：`origin=<lng,lat>`、`destination=<lng,lat>`，可选 `originid`/`destinationid` 以标识门店
  - 针对同一路段仅调用一次，使用 `(driver_open_id, date, origin_id, destination_id)` 作为缓存键
- 处理多站点：对同一天的站点序列做相邻配对（Stop i → Stop i+1），为每个区段调用一次API
- API 限额管理：加入速率限制（如 `sleep` 或 `tenacity` 重试），捕获失败时回退至 Haversine 直线距离，并标记 `distance_source`
- 若需支持返程或跨日补录，保留 `next_day_carry` 标识以提示未闭合的轨迹

### 成本计算设计

- 以公里数（API 返回的 `distance` 单位为米）转换为 `distance_km`
- 可变参数：`cost_per_km`（默认例如 2.5 元/km）、`fuel_price`、`toll_share`（若未来扩展）
- 固定参数：车辆折旧、司机薪酬基准（若后续需要，可在配置文件中维护）
- 每段区间计算 `segment_cost = distance_km * cost_per_km`
- 对每位司机、每日累加得到 `daily_distance_km` 与 `daily_cost`
- 生成成本明细表，可输出为 CSV / Parquet，或提供给数据库落地

### 输出表设计

1. `stops_detail`（原始 + 清洗）：`date`、`driver_open_id`、`stop_seq`、`timestamp`、`store_id`、`store_name`、`lng`、`lat`
2. `route_segments`（API结果）：`date`、`driver_open_id`、`segment_seq`、`origin_store_id`、`dest_store_id`、`distance_km`、`duration_min`、`distance_source`、`segment_cost`
3. `daily_cost_summary`：`date`、`driver_open_id`、`stop_count`、`daily_distance_km`、`daily_cost`、`cost_per_km`
4. `config_snapshot`：记录每次跑批时的参数值、API key 版本、执行时间，用于审计

### 配置与参数管理

- `config.yaml` / `.env`：存储 `amap_api_key`、`cost_per_km`、`max_retries`、`request_timeout`
- 可变参数在脚本启动时加载，支持命令行覆盖（如 `--cost-per-km 2.8`）
- 记录 API 响应摘要（状态码、返回路径方案编号）以便排障

### 技术实现清单

- `src/data_pipeline/load_data.py`：读取 & 清洗原始 CSV
- `src/data_pipeline/segment_builder.py`：构建日内站点序列
- `src/services/amap_client.py`：封装高德 API 调用，带缓存与重试
- `src/calculations/costing.py`：距离转换、成本计算、表格输出
- `scripts/run_cost_pipeline.py`：主入口（接受日期范围/司机过滤、成本参数）
- 单元测试（pytest）：对数据清洗、API 客户端（使用 responses mock）、成本计算进行验证
- 样例数据集：选取 2~3 名司机 1 日的记录，作为回归测试输入

### 风险与验证步骤

- 坐标异常：若地址重复但坐标差异大，需要人工确认；提供异常列表
- API 限流：准备缓存与退避策略，必要时加入本地行驶距离备选（OSRM/自实现）
- 数据不完整：若某天只有单条打卡，无法形成区段，需在输出中标记 `is_route_complete=False`
- 核对机制：随机抽样比对 API 返回的距离 vs 人工地图测距，确保误差可接受

## 阶段二：Streamlit + Folium 可视化

### 目标

- 以 Streamlit 搭建内部可视化面板，动态展示司机轨迹与成本
- 支持参数调节（成本单价、日期范围、司机筛选），即时刷新结果

### 功能模块规划

- 侧栏控件：日期范围、司机多选、成本单价输入、距离来源过滤
- 主要视图：
  - 成本概览卡片：总公里数、总成本、单公里成本、路段数
  - 表格展示：`daily_cost_summary`、`route_segments`
  - 地图：Folium + `st_folium` 展示路线（起终点标记、Polyline 按司机/日期着色）
- 下载功能：允许导出选定筛选条件下的 CSV/Excel
- 缓存层：利用 `st.cache_data` 缓存预处理数据与 API 调用结果，减少重复计算

### 实施步骤

1. 将阶段一输出结果存储为 parquet/csv，供 Streamlit 加载
2. 搭建基础页面结构，完成数据加载与筛选逻辑
3. 集成 Folium，绘制轨迹与打卡点聚合
4. 增加交互（hover 显示门店、成本，点击跳转照片地址）
5. 部署方案：本地 Docker / Streamlit Cloud（待项目环境决定）

## 阶段三：React 全栈重构（远期）

### 目标

- 将数据管道服务化，前端以 React 提供更丰富的交互体验

### 初步架构设想

- 后端：FastAPI / NestJS，提供 REST/GraphQL 接口（司机、日期过滤、成本计算）
- 存储：PostgreSQL 或 ClickHouse（存储路线与成本历史），Redis 作为缓存
- 前端：React + TypeScript + 地图组件（React Leaflet 或 Mapbox GL），结合 Ant Design 构建界面
- 任务调度：使用 Airflow / Prefect 定时运行阶段一的数据管道

### 迁移注意点

- 把阶段一的脚本模块化，提炼为可部署的服务或 Lambda
- 保持输出表结构稳定，为前端 API 定义清晰的 schema
- 引入用户与权限管理（按区域/司机范围授权）
- 补充自动化测试与 CI/CD（Github Actions），保障后续迭代质量

---

下一步建议：先实现阶段一的数据清洗脚本与高德 API 客户端（可先离线模拟），跑通一名司机一日的距离与成本核算 Demo，再扩展到全量数据。
