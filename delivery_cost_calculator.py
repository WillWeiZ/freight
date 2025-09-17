"""
司机配送成本计算模块
基于GPS打卡数据和直线距离计算配送成本
"""

import pandas as pd
import numpy as np
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json

class DeliveryCostCalculator:
    """配送成本计算器"""

    def __init__(self, cost_params: Optional[Dict] = None):
        """
        初始化成本参数

        Args:
            cost_params: 成本参数字典，如为None则使用默认参数
        """
        self.cost_params = cost_params or {
            "fuel_price": 7.5,          # 油费单价（元/升）
            "fuel_consumption": 8.0,    # 百公里油耗（升）
            "toll_rate": 0.45,          # 过路费率（元/公里）
            "driver_hourly_wage": 25,   # 司机时薪（元/小时）
            "vehicle_depreciation": 150, # 车辆日折旧（元）
            "insurance_daily": 50,      # 日保险费（元）
        }

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        使用Haversine公式计算地球表面两点间的直线距离

        Args:
            lat1, lon1: 第一个点的纬度和经度
            lat2, lon2: 第二个点的纬度和经度

        Returns:
            距离（公里）
        """
        # 地球半径（公里）
        R = 6371.0

        # 转换为弧度
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # Haversine公式
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        distance = R * c
        return distance

    def analyze_driver_trajectory(self, driver_data: pd.DataFrame) -> Dict:
        """
        分析单个司机的配送轨迹

        Args:
            driver_data: 单个司机的打卡数据（已按时间排序）

        Returns:
            轨迹分析结果字典
        """
        if len(driver_data) == 0:
            return {}

        # 获取司机基本信息
        driver_id = driver_data['微信open_id'].iloc[0]
        delivery_date = driver_data['提交日期'].iloc[0]
        branch_name = driver_data['匹配分公司名'].iloc[0]

        # 起点坐标（匹配的仓库位置）
        depot_lat = driver_data['匹配纬度'].iloc[0]
        depot_lon = driver_data['匹配经度'].iloc[0]

        # 按时间排序构建配送路径
        sorted_data = driver_data.sort_values('提交时间')

        # 提取配送点坐标
        delivery_points = []
        for _, row in sorted_data.iterrows():
            delivery_points.append({
                'lat': row['纬度'],
                'lon': row['经度'],
                'time': row['提交时间'],
                'address': row['送货地址'],
                'store_name': row.get('收货方名称', ''),
            })

        # 计算路径总距离
        total_distance = 0
        path_details = []

        # 仓库到第一个配送点
        if delivery_points:
            first_point = delivery_points[0]
            distance = self.haversine_distance(
                depot_lat, depot_lon,
                first_point['lat'], first_point['lon']
            )
            total_distance += distance
            path_details.append({
                'from': '仓库',
                'to': f"配送点1",
                'distance': distance,
                'from_coords': (depot_lat, depot_lon),
                'to_coords': (first_point['lat'], first_point['lon'])
            })

        # 配送点之间的距离
        for i in range(1, len(delivery_points)):
            prev_point = delivery_points[i-1]
            curr_point = delivery_points[i]

            distance = self.haversine_distance(
                prev_point['lat'], prev_point['lon'],
                curr_point['lat'], curr_point['lon']
            )
            total_distance += distance
            path_details.append({
                'from': f"配送点{i}",
                'to': f"配送点{i+1}",
                'distance': distance,
                'from_coords': (prev_point['lat'], prev_point['lon']),
                'to_coords': (curr_point['lat'], curr_point['lon'])
            })

        # 计算配送时长
        if len(delivery_points) >= 2:
            start_time = pd.to_datetime(delivery_points[0]['time'])
            end_time = pd.to_datetime(delivery_points[-1]['time'])
            delivery_duration_hours = (end_time - start_time).total_seconds() / 3600
        else:
            delivery_duration_hours = 0.5  # 默认30分钟

        return {
            'driver_id': driver_id,
            'delivery_date': delivery_date,
            'branch_name': branch_name,
            'depot_coords': (depot_lat, depot_lon),
            'delivery_points_count': len(delivery_points),
            'total_distance_km': round(total_distance, 2),
            'delivery_duration_hours': round(delivery_duration_hours, 2),
            'path_details': path_details,
            'delivery_points': delivery_points
        }

    def calculate_delivery_cost(self, trajectory_analysis: Dict) -> Dict:
        """
        基于轨迹分析结果计算配送成本

        Args:
            trajectory_analysis: 轨迹分析结果

        Returns:
            成本分析结果
        """
        if not trajectory_analysis:
            return {}

        total_distance = trajectory_analysis['total_distance_km']
        delivery_duration = trajectory_analysis['delivery_duration_hours']

        # 里程成本计算
        fuel_cost = total_distance * (
            self.cost_params['fuel_price'] *
            self.cost_params['fuel_consumption'] / 100
        )
        toll_cost = total_distance * self.cost_params['toll_rate']
        mileage_cost = fuel_cost + toll_cost

        # 时间成本计算
        time_cost = delivery_duration * self.cost_params['driver_hourly_wage']

        # 固定成本（按配送点数量分摊）
        points_count = trajectory_analysis['delivery_points_count']
        if points_count > 0:
            fixed_cost_per_delivery = (
                self.cost_params['vehicle_depreciation'] +
                self.cost_params['insurance_daily']
            ) / max(points_count, 1)  # 避免除零
        else:
            fixed_cost_per_delivery = 0

        fixed_cost_total = fixed_cost_per_delivery * points_count

        # 总成本
        total_cost = mileage_cost + time_cost + fixed_cost_total

        # 平均单点成本
        avg_cost_per_point = total_cost / max(points_count, 1)

        return {
            'driver_id': trajectory_analysis['driver_id'],
            'delivery_date': trajectory_analysis['delivery_date'],
            'branch_name': trajectory_analysis['branch_name'],
            'total_distance_km': total_distance,
            'delivery_duration_hours': delivery_duration,
            'delivery_points_count': points_count,
            'fuel_cost': round(fuel_cost, 2),
            'toll_cost': round(toll_cost, 2),
            'mileage_cost': round(mileage_cost, 2),
            'time_cost': round(time_cost, 2),
            'fixed_cost': round(fixed_cost_total, 2),
            'total_cost': round(total_cost, 2),
            'avg_cost_per_point': round(avg_cost_per_point, 2),
            'cost_efficiency': round(total_cost / max(total_distance, 0.1), 2)  # 元/公里
        }

    def process_daily_data(self, data_file: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        处理每日配送数据，生成司机成本分析和分公司汇总

        Args:
            data_file: 数据文件路径

        Returns:
            (司机成本分析DataFrame, 分公司汇总DataFrame)
        """
        # 读取数据
        df = pd.read_csv(data_file)

        # 数据预处理
        df['提交日期'] = pd.to_datetime(df['提交时间']).dt.date
        df = df.dropna(subset=['微信open_id', '经度', '纬度', '匹配经度', '匹配纬度'])

        # 按司机分组分析
        driver_results = []

        for driver_id, driver_data in df.groupby('微信open_id'):
            # 分析司机轨迹
            trajectory = self.analyze_driver_trajectory(driver_data)
            if trajectory:
                # 计算成本
                cost_analysis = self.calculate_delivery_cost(trajectory)
                if cost_analysis:
                    driver_results.append(cost_analysis)

        # 创建司机成本分析DataFrame
        driver_cost_df = pd.DataFrame(driver_results)

        # 生成分公司汇总
        if not driver_cost_df.empty:
            branch_summary = driver_cost_df.groupby('branch_name').agg({
                'driver_id': 'count',
                'total_distance_km': ['sum', 'mean'],
                'delivery_points_count': 'sum',
                'total_cost': ['sum', 'mean'],
                'avg_cost_per_point': 'mean',
                'cost_efficiency': 'mean'
            }).round(2)

            # 重命名列
            branch_summary.columns = [
                '司机数量', '总里程', '平均里程', '配送点总数',
                '总成本', '平均成本', '平均单点成本', '成本效率'
            ]
            branch_summary = branch_summary.reset_index()
        else:
            branch_summary = pd.DataFrame()

        return driver_cost_df, branch_summary

    def save_cost_parameters(self, file_path: str):
        """保存成本参数到JSON文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.cost_params, f, ensure_ascii=False, indent=2)

    def load_cost_parameters(self, file_path: str):
        """从JSON文件加载成本参数"""
        with open(file_path, 'r', encoding='utf-8') as f:
            self.cost_params = json.load(f)


if __name__ == "__main__":
    # 测试代码
    calculator = DeliveryCostCalculator()

    # 处理数据
    data_file = "data/2025-08-20_打卡_已匹配.csv"
    driver_costs, branch_summary = calculator.process_daily_data(data_file)

    print("司机成本分析结果:")
    print(driver_costs.head())
    print("\n分公司汇总:")
    print(branch_summary)