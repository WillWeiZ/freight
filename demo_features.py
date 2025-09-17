#!/usr/bin/env python3
"""
司机配送成本分析系统功能演示脚本
展示核心功能和分析结果
"""

import pandas as pd
from delivery_cost_calculator import DeliveryCostCalculator
import json

def demo_cost_calculation():
    """演示成本计算功能"""
    print("🔧 成本计算功能演示")
    print("=" * 50)

    # 创建计算器
    calculator = DeliveryCostCalculator()

    # 显示当前参数
    print("📋 当前成本参数:")
    for key, value in calculator.cost_params.items():
        param_names = {
            "fuel_price": "燃油单价",
            "fuel_consumption": "百公里油耗",
            "toll_rate": "过路费率",
            "driver_hourly_wage": "司机时薪",
            "vehicle_depreciation": "车辆日折旧",
            "insurance_daily": "日保险费"
        }
        units = {
            "fuel_price": "元/升",
            "fuel_consumption": "升",
            "toll_rate": "元/公里",
            "driver_hourly_wage": "元/小时",
            "vehicle_depreciation": "元",
            "insurance_daily": "元"
        }
        print(f"  {param_names[key]}: {value} {units[key]}")

    print("\n📊 处理2025-08-20数据...")
    driver_costs, branch_summary = calculator.process_daily_data("data/2025-08-20_打卡_已匹配.csv")

    print(f"✅ 分析完成，共{len(driver_costs)}个司机，{len(branch_summary)}个分公司")

    return driver_costs, branch_summary

def demo_data_analysis(driver_costs, branch_summary):
    """演示数据分析结果"""
    print("\n📈 数据分析结果展示")
    print("=" * 50)

    # 整体统计
    total_cost = driver_costs['total_cost'].sum()
    total_distance = driver_costs['total_distance_km'].sum()
    total_points = driver_costs['delivery_points_count'].sum()

    print("🔍 整体数据统计:")
    print(f"  总司机数: {len(driver_costs)}人")
    print(f"  总配送点: {total_points}个")
    print(f"  总里程: {total_distance:.2f}公里")
    print(f"  总成本: {total_cost:.2f}元")
    print(f"  平均单点成本: {total_cost/total_points:.2f}元/点")

    # 成本结构分析
    mileage_cost = driver_costs['mileage_cost'].sum()
    time_cost = driver_costs['time_cost'].sum()
    fixed_cost = driver_costs['fixed_cost'].sum()

    print("\n💰 成本结构分析:")
    print(f"  里程成本: {mileage_cost:.2f}元 ({mileage_cost/total_cost*100:.1f}%)")
    print(f"  时间成本: {time_cost:.2f}元 ({time_cost/total_cost*100:.1f}%)")
    print(f"  固定成本: {fixed_cost:.2f}元 ({fixed_cost/total_cost*100:.1f}%)")

    # 分公司排名
    print("\n🏆 分公司效率排名 (成本效率：元/公里):")
    efficiency_ranking = branch_summary.sort_values('成本效率')
    for i, (_, row) in enumerate(efficiency_ranking.iterrows(), 1):
        print(f"  {i}. {row['branch_name']}: {row['成本效率']:.2f}元/公里")

    # 司机绩效分析
    print("\n👤 司机绩效分析:")
    best_driver = driver_costs.loc[driver_costs['avg_cost_per_point'].idxmin()]
    worst_driver = driver_costs.loc[driver_costs['avg_cost_per_point'].idxmax()]

    print(f"  最高效司机: {best_driver['driver_id'][-8:]} - {best_driver['avg_cost_per_point']:.2f}元/点")
    print(f"  最低效司机: {worst_driver['driver_id'][-8:]} - {worst_driver['avg_cost_per_point']:.2f}元/点")

def demo_parameter_sensitivity():
    """演示参数敏感性分析"""
    print("\n⚙️ 参数敏感性分析")
    print("=" * 50)

    # 基准参数
    base_params = {
        "fuel_price": 7.5,
        "fuel_consumption": 8.0,
        "toll_rate": 0.45,
        "driver_hourly_wage": 25,
        "vehicle_depreciation": 150,
        "insurance_daily": 50,
    }

    # 计算基准成本
    base_calculator = DeliveryCostCalculator(base_params)
    base_driver_costs, _ = base_calculator.process_daily_data("data/2025-08-20_打卡_已匹配.csv")
    base_total_cost = base_driver_costs['total_cost'].sum()

    print(f"📊 基准总成本: {base_total_cost:.2f}元")

    # 测试不同参数的影响
    sensitivity_tests = [
        ("燃油价格+20%", {"fuel_price": 9.0}),
        ("司机时薪+20%", {"driver_hourly_wage": 30}),
        ("车辆折旧+20%", {"vehicle_depreciation": 180}),
        ("过路费率+20%", {"toll_rate": 0.54}),
    ]

    print("\n🔍 参数变化影响分析:")
    for test_name, param_change in sensitivity_tests:
        test_params = base_params.copy()
        test_params.update(param_change)

        test_calculator = DeliveryCostCalculator(test_params)
        test_driver_costs, _ = test_calculator.process_daily_data("data/2025-08-20_打卡_已匹配.csv")
        test_total_cost = test_driver_costs['total_cost'].sum()

        cost_change = test_total_cost - base_total_cost
        cost_change_pct = (cost_change / base_total_cost) * 100

        print(f"  {test_name}: {test_total_cost:.2f}元 (变化: {cost_change:+.2f}元, {cost_change_pct:+.1f}%)")

def demo_optimization_suggestions():
    """演示优化建议"""
    print("\n💡 优化建议分析")
    print("=" * 50)

    # 读取数据
    driver_costs = pd.read_csv("data/2025-08-20_司机成本分析.csv")
    branch_summary = pd.read_csv("data/2025-08-20_分公司汇总.csv")

    # 识别问题
    print("🔍 发现的问题:")

    # 1. 固定成本占比过高
    total_cost = driver_costs['total_cost'].sum()
    fixed_cost = driver_costs['fixed_cost'].sum()
    fixed_cost_ratio = fixed_cost / total_cost * 100

    if fixed_cost_ratio > 50:
        print(f"  ⚠️  固定成本占比过高: {fixed_cost_ratio:.1f}%")
        print("     建议: 增加配送密度，提高单次配送点数")

    # 2. 分公司效率差异大
    efficiency_std = branch_summary['成本效率'].std()
    efficiency_mean = branch_summary['成本效率'].mean()
    cv = efficiency_std / efficiency_mean

    if cv > 0.5:
        print(f"  ⚠️  分公司效率差异显著: 变异系数{cv:.2f}")
        print("     建议: 推广高效分公司经验到低效分公司")

    # 3. 司机绩效差异大
    driver_efficiency_std = driver_costs['avg_cost_per_point'].std()
    driver_efficiency_mean = driver_costs['avg_cost_per_point'].mean()

    if driver_efficiency_std > 30:
        print(f"  ⚠️  司机绩效差异大: 标准差{driver_efficiency_std:.1f}元")
        print("     建议: 对低效司机进行路径规划培训")

    print("\n📋 具体优化建议:")
    print("  1. 路径优化: 使用TSP算法优化配送顺序")
    print("  2. 配送整合: 相邻区域配送点合并为单次配送")
    print("  3. 时间调优: 避开高峰期减少时间成本")
    print("  4. 车辆匹配: 根据配送距离选择合适车型")

def main():
    """主演示函数"""
    print("🚚 司机配送成本分析系统")
    print("功能演示和分析报告")
    print("=" * 60)

    try:
        # 1. 成本计算演示
        driver_costs, branch_summary = demo_cost_calculation()

        # 2. 数据分析演示
        demo_data_analysis(driver_costs, branch_summary)

        # 3. 参数敏感性分析
        demo_parameter_sensitivity()

        # 4. 优化建议
        demo_optimization_suggestions()

        print("\n" + "=" * 60)
        print("✅ 演示完成！")
        print("🌐 启动Web应用查看详细可视化:")
        print("   python run_app.py")
        print("📊 或直接运行:")
        print("   streamlit run streamlit_app.py")

    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        print("请检查数据文件是否存在")

if __name__ == "__main__":
    main()