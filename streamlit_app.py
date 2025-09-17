"""
司机配送成本分析系统 - Streamlit Web应用
功能：
1. 司机配送路径可视化
2. 成本分析报表展示
3. 实时参数调整和成本计算
"""

import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from delivery_cost_calculator import DeliveryCostCalculator

# 页面配置
st.set_page_config(
    page_title="司机配送成本分析系统",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
}
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}
.branch-tag {
    background-color: #e1f5fe;
    color: #01579b;
    padding: 0.2rem 0.5rem;
    border-radius: 1rem;
    font-size: 0.8rem;
    margin: 0.1rem;
    display: inline-block;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """加载数据"""
    try:
        # 加载原始匹配数据
        original_data = pd.read_csv('data/2025-08-20_打卡_已匹配.csv')
        # 加载司机成本分析数据
        driver_costs = pd.read_csv('data/2025-08-20_司机成本分析.csv')
        # 加载分公司汇总数据
        branch_summary = pd.read_csv('data/2025-08-20_分公司汇总.csv')
        return original_data, driver_costs, branch_summary
    except FileNotFoundError as e:
        st.error(f"数据文件未找到: {e}")
        return None, None, None

def generate_comprehensive_csv_report(driver_costs, branch_summary, cost_params):
    """生成综合分析报告CSV"""
    report_data = []

    # 整体统计
    total_cost = driver_costs['total_cost'].sum()
    total_distance = driver_costs['total_distance_km'].sum()
    total_points = driver_costs['delivery_points_count'].sum()

    report_data.append(['整体统计', '', ''])
    report_data.append(['总司机数', len(driver_costs), '人'])
    report_data.append(['总配送点数', total_points, '个'])
    report_data.append(['总里程', f"{total_distance:.2f}", '公里'])
    report_data.append(['总成本', f"{total_cost:.2f}", '元'])
    report_data.append(['平均单点成本', f"{total_cost/total_points:.2f}", '元/点'])
    report_data.append(['', '', ''])

    # 成本结构
    mileage_cost = driver_costs['mileage_cost'].sum()
    time_cost = driver_costs['time_cost'].sum()
    fixed_cost = driver_costs['fixed_cost'].sum()

    report_data.append(['成本结构分析', '', ''])
    report_data.append(['里程成本', f"{mileage_cost:.2f}", f"{mileage_cost/total_cost*100:.1f}%"])
    report_data.append(['时间成本', f"{time_cost:.2f}", f"{time_cost/total_cost*100:.1f}%"])
    report_data.append(['固定成本', f"{fixed_cost:.2f}", f"{fixed_cost/total_cost*100:.1f}%"])
    report_data.append(['', '', ''])

    # 分公司效率排名
    report_data.append(['分公司效率排名', '', ''])
    efficiency_ranking = branch_summary.sort_values('成本效率')
    for i, (_, row) in enumerate(efficiency_ranking.iterrows(), 1):
        report_data.append([f"第{i}名", row['branch_name'], f"{row['成本效率']:.2f}元/公里"])
    report_data.append(['', '', ''])

    # 司机绩效
    best_driver = driver_costs.loc[driver_costs['avg_cost_per_point'].idxmin()]
    worst_driver = driver_costs.loc[driver_costs['avg_cost_per_point'].idxmax()]

    report_data.append(['司机绩效分析', '', ''])
    report_data.append(['最高效司机', best_driver['driver_id'][-8:], f"{best_driver['avg_cost_per_point']:.2f}元/点"])
    report_data.append(['最低效司机', worst_driver['driver_id'][-8:], f"{worst_driver['avg_cost_per_point']:.2f}元/点"])
    report_data.append(['绩效差异', f"{worst_driver['avg_cost_per_point']/best_driver['avg_cost_per_point']:.1f}", '倍'])
    report_data.append(['', '', ''])

    # 成本参数
    report_data.append(['当前成本参数', '', ''])
    report_data.append(['燃油单价', cost_params['fuel_price'], '元/升'])
    report_data.append(['百公里油耗', cost_params['fuel_consumption'], '升'])
    report_data.append(['过路费率', cost_params['toll_rate'], '元/公里'])
    report_data.append(['司机时薪', cost_params['driver_hourly_wage'], '元/小时'])
    report_data.append(['车辆日折旧', cost_params['vehicle_depreciation'], '元'])
    report_data.append(['日保险费', cost_params['insurance_daily'], '元'])

    # 转换为CSV格式
    df_report = pd.DataFrame(report_data, columns=['指标', '数值', '单位'])
    return df_report.to_csv(index=False, encoding='utf-8-sig')

def generate_comparison_report(old_driver_costs, new_driver_costs, old_params, new_params):
    """生成参数对比分析报告"""
    comparison_data = []

    # 总成本对比
    old_total = old_driver_costs['total_cost'].sum()
    new_total = new_driver_costs['total_cost'].sum()
    cost_change = new_total - old_total
    cost_change_pct = (cost_change / old_total) * 100

    comparison_data.append(['成本对比分析', '', '', '', ''])
    comparison_data.append(['总成本', f"{old_total:.2f}", f"{new_total:.2f}", f"{cost_change:+.2f}", f"{cost_change_pct:+.1f}%"])

    # 平均单点成本对比
    old_avg = old_driver_costs['avg_cost_per_point'].mean()
    new_avg = new_driver_costs['avg_cost_per_point'].mean()
    avg_change = new_avg - old_avg
    avg_change_pct = (avg_change / old_avg) * 100

    comparison_data.append(['平均单点成本', f"{old_avg:.2f}", f"{new_avg:.2f}", f"{avg_change:+.2f}", f"{avg_change_pct:+.1f}%"])
    comparison_data.append(['', '', '', '', ''])

    # 参数变化
    comparison_data.append(['参数变化', '', '', '', ''])
    param_names = {
        'fuel_price': '燃油单价',
        'fuel_consumption': '百公里油耗',
        'toll_rate': '过路费率',
        'driver_hourly_wage': '司机时薪',
        'vehicle_depreciation': '车辆日折旧',
        'insurance_daily': '日保险费'
    }

    for key, name in param_names.items():
        old_val = old_params[key]
        new_val = new_params[key]
        if old_val != new_val:
            change = new_val - old_val
            change_pct = (change / old_val) * 100
            comparison_data.append([name, f"{old_val}", f"{new_val}", f"{change:+.2f}", f"{change_pct:+.1f}%"])

    df_comparison = pd.DataFrame(comparison_data, columns=['项目', '调整前', '调整后', '变化量', '变化率'])
    return df_comparison.to_csv(index=False, encoding='utf-8-sig')

def create_route_map(original_data, selected_drivers=None, map_style="标准地图", show_heatmap=False):
    """创建司机配送路径地图"""
    if selected_drivers is None:
        selected_drivers = original_data['微信open_id'].unique()

    # 过滤数据
    filtered_data = original_data[original_data['微信open_id'].isin(selected_drivers)]

    if len(filtered_data) == 0:
        return None

    # 计算地图中心点
    center_lat = filtered_data['纬度'].mean()
    center_lon = filtered_data['经度'].mean()

    # 创建地图（不使用默认瓦片）
    m = folium.Map(location=[center_lat, center_lon], zoom_start=10, tiles=None)

    # 使用指定的图层列表
    tile_list = ['openstreetmap', 'cartodbpositron']

    tile_layers = {
        "标准地图": folium.TileLayer('OpenStreetMap', name='标准地图'),
        "简洁地图": folium.TileLayer('CartoDB positron', name='简洁地图')
    }

    # 添加选中的默认图层
    tile_layers[map_style].add_to(m)

    # 添加其他图层供选择
    for name, layer in tile_layers.items():
        if name != map_style:
            layer.add_to(m)

    # 颜色列表
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred',
              'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue',
              'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen', 'gray']

    driver_color_map = {}

    for i, driver_id in enumerate(selected_drivers):
        driver_data = filtered_data[filtered_data['微信open_id'] == driver_id].sort_values('提交时间')

        if len(driver_data) == 0:
            continue

        color = colors[i % len(colors)]
        driver_color_map[driver_id] = color

        # 获取分公司信息
        branch_name = driver_data['匹配分公司名'].iloc[0]
        depot_lat = driver_data['匹配纬度'].iloc[0]
        depot_lon = driver_data['匹配经度'].iloc[0]

        # 添加仓库标记
        folium.Marker(
            [depot_lat, depot_lon],
            popup=f"仓库 - {branch_name}",
            tooltip=f"仓库 - {branch_name}",
            icon=folium.Icon(color='black', icon='home'),
        ).add_to(m)

        # 配送路径点
        coordinates = []
        coordinates.append([depot_lat, depot_lon])  # 起点

        for idx, row in driver_data.iterrows():
            lat, lon = row['纬度'], row['经度']
            coordinates.append([lat, lon])

            # 添加配送点标记
            folium.CircleMarker(
                [lat, lon],
                radius=6,
                popup=f"""
                司机: {driver_id[-8:]}<br>
                时间: {row['提交时间']}<br>
                地址: {row['送货地址']}<br>
                分公司: {branch_name}
                """,
                tooltip=f"配送点 - {row['提交时间'][11:16]}",
                color=color,
                fillColor=color,
                fillOpacity=0.7
            ).add_to(m)

        # 绘制路径线
        if len(coordinates) > 1:
            folium.PolyLine(
                coordinates,
                color=color,
                weight=3,
                opacity=0.8,
                popup=f"司机: {driver_id[-8:]} - {branch_name}"
            ).add_to(m)

    # 添加热力图（如果启用）
    if show_heatmap and len(filtered_data) > 0:
        from folium import plugins
        heatmap_data = []
        for _, row in filtered_data.iterrows():
            heatmap_data.append([row['纬度'], row['经度']])

        plugins.HeatMap(
            heatmap_data,
            name="配送密度热力图",
            min_opacity=0.2,
            radius=20,
            blur=15,
            gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'orange', 1.0: 'red'}
        ).add_to(m)

    # 添加图层控制
    folium.LayerControl(position='topright').add_to(m)

    # 添加全屏插件
    from folium import plugins
    plugins.Fullscreen(position='topleft').add_to(m)

    # 添加鼠标位置显示
    plugins.MousePosition().add_to(m)

    return m

def create_cost_charts(driver_costs, branch_summary):
    """创建成本分析图表"""
    charts = {}

    # 1. 成本结构饼图
    fig_pie = go.Figure(data=[go.Pie(
        labels=['里程成本', '时间成本', '固定成本'],
        values=[
            driver_costs['mileage_cost'].sum(),
            driver_costs['time_cost'].sum(),
            driver_costs['fixed_cost'].sum()
        ],
        hole=0.3,
        marker_colors=['#FF6B6B', '#4ECDC4', '#45B7D1']
    )])
    fig_pie.update_layout(
        title="总成本结构分布",
        font=dict(size=14),
        height=400
    )
    charts['cost_structure'] = fig_pie

    # 2. 分公司成本对比
    fig_branch = px.bar(
        branch_summary,
        x='branch_name',
        y='总成本',
        color='成本效率',
        title="各分公司总成本对比",
        color_continuous_scale='RdYlBu_r',
        text='总成本'
    )
    fig_branch.update_traces(texttemplate='%{text:.0f}元', textposition='outside')
    fig_branch.update_layout(height=400)
    charts['branch_comparison'] = fig_branch

    # 3. 司机绩效散点图
    fig_scatter = px.scatter(
        driver_costs,
        x='delivery_points_count',
        y='total_cost',
        color='branch_name',
        size='total_distance_km',
        hover_data=['avg_cost_per_point'],
        title="司机绩效分析：配送点数 vs 总成本"
    )
    fig_scatter.update_layout(height=400)
    charts['driver_performance'] = fig_scatter

    # 4. 成本效率对比
    fig_efficiency = px.bar(
        branch_summary.sort_values('成本效率'),
        x='成本效率',
        y='branch_name',
        orientation='h',
        title="分公司成本效率对比 (元/公里)",
        color='成本效率',
        color_continuous_scale='RdYlGn_r'
    )
    fig_efficiency.update_layout(height=400)
    charts['efficiency'] = fig_efficiency

    return charts

def recalculate_costs(original_data, cost_params):
    """根据新参数重新计算成本"""
    calculator = DeliveryCostCalculator(cost_params)

    # 重新处理数据
    df = original_data.copy()
    df['提交日期'] = pd.to_datetime(df['提交时间']).dt.date
    df = df.dropna(subset=['微信open_id', '经度', '纬度', '匹配经度', '匹配纬度'])

    # 按司机分组分析
    driver_results = []
    for driver_id, driver_data in df.groupby('微信open_id'):
        trajectory = calculator.analyze_driver_trajectory(driver_data)
        if trajectory:
            cost_analysis = calculator.calculate_delivery_cost(trajectory)
            if cost_analysis:
                driver_results.append(cost_analysis)

    new_driver_costs = pd.DataFrame(driver_results)

    # 生成分公司汇总
    if not new_driver_costs.empty:
        new_branch_summary = new_driver_costs.groupby('branch_name').agg({
            'driver_id': 'count',
            'total_distance_km': ['sum', 'mean'],
            'delivery_points_count': 'sum',
            'total_cost': ['sum', 'mean'],
            'avg_cost_per_point': 'mean',
            'cost_efficiency': 'mean'
        }).round(2)

        new_branch_summary.columns = [
            '司机数量', '总里程', '平均里程', '配送点总数',
            '总成本', '平均成本', '平均单点成本', '成本效率'
        ]
        new_branch_summary = new_branch_summary.reset_index()
    else:
        new_branch_summary = pd.DataFrame()

    return new_driver_costs, new_branch_summary

def main():
    # 主标题
    st.markdown('<h1 class="main-header">🚚 司机配送成本分析系统</h1>', unsafe_allow_html=True)

    # 加载数据
    original_data, driver_costs, branch_summary = load_data()

    if original_data is None:
        st.error("无法加载数据，请检查数据文件是否存在")
        return

    # 侧边栏 - 参数控制
    st.sidebar.header("📊 成本参数调整")
    st.sidebar.markdown("调整以下参数可实时重新计算成本：")

    # 加载默认参数
    try:
        with open('data/cost_parameters.json', 'r', encoding='utf-8') as f:
            default_params = json.load(f)
    except:
        default_params = {
            "fuel_price": 7.5,
            "fuel_consumption": 8.0,
            "toll_rate": 0.45,
            "driver_hourly_wage": 25,
            "vehicle_depreciation": 150,
            "insurance_daily": 50,
        }

    # 参数输入控件
    fuel_price = st.sidebar.slider(
        "燃油单价 (元/升)", 6.0, 10.0, default_params["fuel_price"], 0.1
    )
    fuel_consumption = st.sidebar.slider(
        "百公里油耗 (升)", 6.0, 12.0, default_params["fuel_consumption"], 0.5
    )
    toll_rate = st.sidebar.slider(
        "过路费率 (元/公里)", 0.2, 0.8, default_params["toll_rate"], 0.05
    )
    driver_hourly_wage = st.sidebar.slider(
        "司机时薪 (元/小时)", 15, 40, default_params["driver_hourly_wage"], 1
    )
    vehicle_depreciation = st.sidebar.slider(
        "车辆日折旧 (元)", 100, 300, default_params["vehicle_depreciation"], 10
    )
    insurance_daily = st.sidebar.slider(
        "日保险费 (元)", 30, 100, default_params["insurance_daily"], 5
    )

    # 新的参数字典
    new_params = {
        "fuel_price": fuel_price,
        "fuel_consumption": fuel_consumption,
        "toll_rate": toll_rate,
        "driver_hourly_wage": driver_hourly_wage,
        "vehicle_depreciation": vehicle_depreciation,
        "insurance_daily": insurance_daily,
    }

    # 检查参数是否改变
    params_changed = new_params != default_params

    if params_changed:
        st.sidebar.info("参数已修改，重新计算中...")
        current_driver_costs, current_branch_summary = recalculate_costs(original_data, new_params)
        st.sidebar.success("✅ 成本重新计算完成")
    else:
        current_driver_costs, current_branch_summary = driver_costs, branch_summary

    # 主要内容区域
    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ 配送路径地图", "📊 成本分析报表", "📈 数据详情", "📥 数据下载"])

    with tab1:
        st.header("司机配送路径可视化")

        # 地图控制选项
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            available_drivers = original_data['微信open_id'].unique()
            selected_drivers = st.multiselect(
                "选择要显示的司机 (默认显示前5个)",
                available_drivers,
                default=available_drivers[:5],  # 默认显示前5个司机
                format_func=lambda x: f"司机 {x[-8:]}"
            )

        with col2:
            # 分公司过滤
            available_branches = original_data['匹配分公司名'].unique()
            selected_branch = st.selectbox(
                "按分公司过滤",
                ['全部'] + list(available_branches)
            )

            if selected_branch != '全部':
                branch_drivers = original_data[
                    original_data['匹配分公司名'] == selected_branch
                ]['微信open_id'].unique()
                selected_drivers = [d for d in selected_drivers if d in branch_drivers]

        with col3:
            # 地图样式选择
            map_style = st.selectbox(
                "地图样式",
                ["标准地图", "简洁地图"],
                index=0
            )

            # 热力图开关
            show_heatmap = st.checkbox("显示配送密度热力图", value=False)

        if selected_drivers:
            # 创建地图
            route_map = create_route_map(original_data, selected_drivers, map_style, show_heatmap)
            if route_map:
                st_folium(route_map, width=700, height=500)

                # 添加地图功能说明
                with st.expander("🗺️ 地图功能说明"):
                    st.markdown("""
                    **地图控制功能：**
                    - 🗺️ **图层选择**：标准地图(OpenStreetMap) / 简洁地图(CartoDB)
                    - 🔄 **图层切换**：点击右上角图层控制器切换地图样式
                    - 🔍 **全屏查看**：点击左上角全屏按钮
                    - 📍 **鼠标坐标**：底部显示鼠标当前位置的经纬度
                    - 🔥 **热力图**：开启后显示配送点密度分布
                    - 📦 **配送点**：点击圆形标记查看详细配送信息
                    - 🏠 **仓库位置**：黑色home图标表示分公司仓库
                    - 🚚 **配送路径**：彩色线条显示司机配送路线
                    """)

                # 显示选中司机的基本信息
                st.subheader("选中司机信息")
                selected_info = current_driver_costs[
                    current_driver_costs['driver_id'].isin(selected_drivers)
                ][['driver_id', 'branch_name', 'delivery_points_count', 'total_distance_km', 'total_cost']]
                selected_info.columns = ['司机ID', '分公司', '配送点数', '总里程(km)', '总成本(元)']
                st.dataframe(selected_info, width='stretch')
        else:
            st.warning("请选择至少一个司机")

    with tab2:
        st.header("成本分析报表")

        # 关键指标展示
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "总司机数",
                len(current_driver_costs),
                delta=None
            )

        with col2:
            total_cost = current_driver_costs['total_cost'].sum()
            st.metric(
                "总成本",
                f"{total_cost:.2f}元",
                delta=f"{total_cost - driver_costs['total_cost'].sum():.2f}元" if params_changed else None
            )

        with col3:
            total_points = current_driver_costs['delivery_points_count'].sum()
            st.metric(
                "总配送点数",
                f"{total_points}个",
                delta=None
            )

        with col4:
            avg_cost_per_point = current_driver_costs['avg_cost_per_point'].mean()
            st.metric(
                "平均单点成本",
                f"{avg_cost_per_point:.2f}元",
                delta=f"{avg_cost_per_point - driver_costs['avg_cost_per_point'].mean():.2f}元" if params_changed else None
            )

        # 图表展示
        charts = create_cost_charts(current_driver_costs, current_branch_summary)

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(charts['cost_structure'], width='stretch')
        with col2:
            st.plotly_chart(charts['efficiency'], width='stretch')

        col3, col4 = st.columns(2)
        with col3:
            st.plotly_chart(charts['branch_comparison'], width='stretch')
        with col4:
            st.plotly_chart(charts['driver_performance'], width='stretch')

        # 分公司汇总表
        st.subheader("分公司汇总统计")
        st.dataframe(current_branch_summary, width='stretch')

    with tab3:
        st.header("详细数据")

        # 数据筛选
        col1, col2 = st.columns(2)
        with col1:
            branch_filter = st.selectbox(
                "选择分公司",
                ['全部'] + list(current_driver_costs['branch_name'].unique())
            )

        with col2:
            sort_by = st.selectbox(
                "排序方式",
                ['总成本', '配送点数', '总里程', '成本效率']
            )

        # 过滤和排序数据
        display_data = current_driver_costs.copy()
        if branch_filter != '全部':
            display_data = display_data[display_data['branch_name'] == branch_filter]

        sort_mapping = {
            '总成本': 'total_cost',
            '配送点数': 'delivery_points_count',
            '总里程': 'total_distance_km',
            '成本效率': 'cost_efficiency'
        }
        display_data = display_data.sort_values(sort_mapping[sort_by], ascending=False)

        # 显示数据表
        st.subheader("司机成本详情")
        display_columns = [
            'driver_id', 'branch_name', 'delivery_points_count',
            'total_distance_km', 'delivery_duration_hours', 'mileage_cost',
            'time_cost', 'fixed_cost', 'total_cost', 'avg_cost_per_point'
        ]
        column_names = [
            '司机ID', '分公司', '配送点数', '总里程(km)', '配送时长(h)',
            '里程成本(元)', '时间成本(元)', '固定成本(元)', '总成本(元)', '单点成本(元)'
        ]

        display_df = display_data[display_columns].copy()
        display_df.columns = column_names
        st.dataframe(display_df, width='stretch')

        # 下载按钮
        csv = display_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="下载当前数据",
            data=csv,
            file_name=f"司机成本分析_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

    with tab4:
        st.header("📥 数据下载中心")
        st.markdown("**下载项目中的所有CSV数据文件和分析报告**")

        # 创建两列布局
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 核心数据文件")

            # 原始匹配数据
            try:
                original_csv = original_data.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📋 原始打卡匹配数据",
                    data=original_csv,
                    file_name="2025-08-20_打卡_已匹配.csv",
                    mime="text/csv",
                    help="包含司机打卡记录和分公司匹配信息"
                )
            except:
                st.error("原始数据加载失败")

            # 司机成本分析数据
            driver_csv = current_driver_costs.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="💰 司机成本分析数据",
                data=driver_csv,
                file_name=f"司机成本分析_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                help="包含17个司机的详细成本分析结果"
            )

            # 分公司汇总数据
            branch_csv = current_branch_summary.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="🏢 分公司汇总统计",
                data=branch_csv,
                file_name=f"分公司汇总_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                help="包含6个分公司的效率和成本对比"
            )

        with col2:
            st.subheader("📈 分析报告")

            # 生成详细的分析报告CSV
            timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')

            # 参数配置文件
            params_json = json.dumps(new_params, ensure_ascii=False, indent=2)
            st.download_button(
                label="⚙️ 成本参数配置",
                data=params_json,
                file_name=f"成本参数配置_{timestamp}.json",
                mime="application/json",
                help="当前使用的成本计算参数"
            )

            # 生成综合分析报告
            comprehensive_report = generate_comprehensive_csv_report(
                current_driver_costs,
                current_branch_summary,
                new_params
            )
            st.download_button(
                label="📋 综合分析报告",
                data=comprehensive_report,
                file_name=f"综合分析报告_{timestamp}.csv",
                mime="text/csv",
                help="包含所有关键指标和分析结论的综合报告"
            )

            # 生成对比分析（如果参数有变化）
            if params_changed:
                comparison_report = generate_comparison_report(
                    driver_costs, current_driver_costs,
                    default_params, new_params
                )
                st.download_button(
                    label="🔄 参数对比分析",
                    data=comparison_report,
                    file_name=f"参数对比分析_{timestamp}.csv",
                    mime="text/csv",
                    help="参数调整前后的成本变化对比"
                )

        # 数据统计信息
        st.subheader("📊 数据概览")

        col3, col4, col5, col6 = st.columns(4)
        with col3:
            st.metric("数据日期", "2025-08-20")
        with col4:
            st.metric("总记录数", len(original_data))
        with col5:
            st.metric("司机数量", len(current_driver_costs))
        with col6:
            st.metric("分公司数", len(current_branch_summary))

        # 下载说明
        st.subheader("📝 下载说明")
        st.markdown("""
        **文件说明：**
        - **原始打卡匹配数据**：包含所有司机的GPS打卡记录和分公司匹配信息
        - **司机成本分析数据**：每个司机的详细成本分析，包含里程、时间、固定成本
        - **分公司汇总统计**：各分公司的效率对比和成本统计
        - **成本参数配置**：当前使用的成本计算参数（JSON格式）
        - **综合分析报告**：包含关键发现和优化建议的完整报告
        - **参数对比分析**：参数调整前后的成本变化分析（仅在参数修改时可用）

        **使用建议：**
        - 下载原始数据用于进一步分析或备份
        - 下载成本分析数据用于财务报告
        - 下载分公司汇总用于管理决策
        - 下载参数配置用于重现分析结果
        """)

if __name__ == "__main__":
    main()