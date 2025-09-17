"""
配送成本分析报告生成器
生成可视化图表和详细分析报告
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import json

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class CostAnalysisReport:
    """成本分析报告生成器"""

    def __init__(self, driver_cost_file: str, branch_summary_file: str):
        """
        初始化报告生成器

        Args:
            driver_cost_file: 司机成本分析文件路径
            branch_summary_file: 分公司汇总文件路径
        """
        self.driver_costs = pd.read_csv(driver_cost_file)
        self.branch_summary = pd.read_csv(branch_summary_file)

    def generate_cost_structure_chart(self, save_path: str = None):
        """生成成本结构分析图表"""
        # 计算总成本结构
        total_mileage_cost = self.driver_costs['mileage_cost'].sum()
        total_time_cost = self.driver_costs['time_cost'].sum()
        total_fixed_cost = self.driver_costs['fixed_cost'].sum()

        costs = [total_mileage_cost, total_time_cost, total_fixed_cost]
        labels = ['里程成本', '时间成本', '固定成本']
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # 饼图
        ax1.pie(costs, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax1.set_title('配送成本结构分布', fontsize=14, fontweight='bold')

        # 柱状图
        ax2.bar(labels, costs, color=colors)
        ax2.set_title('各项成本金额对比', fontsize=14, fontweight='bold')
        ax2.set_ylabel('成本 (元)')

        # 添加数值标签
        for i, cost in enumerate(costs):
            ax2.text(i, cost + 50, f'{cost:.1f}元', ha='center', va='bottom')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()

    def generate_branch_comparison_chart(self, save_path: str = None):
        """生成分公司对比分析图表"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

        # 1. 各分公司总成本对比
        ax1.bar(self.branch_summary['branch_name'], self.branch_summary['总成本'],
                color='skyblue', alpha=0.8)
        ax1.set_title('各分公司总成本对比', fontsize=12, fontweight='bold')
        ax1.set_ylabel('总成本 (元)')
        ax1.tick_params(axis='x', rotation=45)

        # 2. 各分公司配送效率对比
        ax2.bar(self.branch_summary['branch_name'], self.branch_summary['成本效率'],
                color='lightcoral', alpha=0.8)
        ax2.set_title('各分公司成本效率对比 (元/公里)', fontsize=12, fontweight='bold')
        ax2.set_ylabel('成本效率 (元/公里)')
        ax2.tick_params(axis='x', rotation=45)

        # 3. 平均里程 vs 平均成本散点图
        ax3.scatter(self.branch_summary['平均里程'], self.branch_summary['平均成本'],
                   s=100, alpha=0.7, c='green')
        ax3.set_xlabel('平均里程 (公里)')
        ax3.set_ylabel('平均成本 (元)')
        ax3.set_title('平均里程 vs 平均成本关系', fontsize=12, fontweight='bold')

        # 添加分公司标签
        for i, branch in enumerate(self.branch_summary['branch_name']):
            ax3.annotate(branch,
                        (self.branch_summary['平均里程'].iloc[i],
                         self.branch_summary['平均成本'].iloc[i]),
                        xytext=(5, 5), textcoords='offset points', fontsize=9)

        # 4. 司机数量和配送点数对比
        x = range(len(self.branch_summary))
        width = 0.35

        ax4.bar([i - width/2 for i in x], self.branch_summary['司机数量'],
                width, label='司机数量', alpha=0.8)
        ax4.bar([i + width/2 for i in x], self.branch_summary['配送点总数'],
                width, label='配送点总数', alpha=0.8)

        ax4.set_xlabel('分公司')
        ax4.set_ylabel('数量')
        ax4.set_title('各分公司司机数量与配送点数对比', fontsize=12, fontweight='bold')
        ax4.set_xticks(x)
        ax4.set_xticklabels(self.branch_summary['branch_name'], rotation=45)
        ax4.legend()

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()

    def generate_driver_performance_chart(self, save_path: str = None):
        """生成司机绩效分析图表"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        # 1. 司机配送点数 vs 总成本
        scatter = ax1.scatter(self.driver_costs['delivery_points_count'],
                             self.driver_costs['total_cost'],
                             c=self.driver_costs['total_distance_km'],
                             s=80, alpha=0.7, cmap='viridis')
        ax1.set_xlabel('配送点数')
        ax1.set_ylabel('总成本 (元)')
        ax1.set_title('司机配送点数 vs 总成本 (颜色表示里程)', fontsize=12, fontweight='bold')

        # 添加颜色条
        cbar = plt.colorbar(scatter, ax=ax1)
        cbar.set_label('总里程 (公里)')

        # 2. 单点成本分布直方图
        ax2.hist(self.driver_costs['avg_cost_per_point'], bins=10,
                alpha=0.7, color='orange', edgecolor='black')
        ax2.set_xlabel('平均单点成本 (元)')
        ax2.set_ylabel('司机数量')
        ax2.set_title('司机平均单点成本分布', fontsize=12, fontweight='bold')

        # 添加平均值线
        mean_cost = self.driver_costs['avg_cost_per_point'].mean()
        ax2.axvline(mean_cost, color='red', linestyle='--', linewidth=2,
                   label=f'平均值: {mean_cost:.1f}元')
        ax2.legend()

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()

    def generate_summary_report(self) -> str:
        """生成文字总结报告"""
        report = f"""
# 2025-08-20 配送成本分析报告

## 📊 整体概况
- **分析日期**: 2025年8月20日
- **总司机数**: {len(self.driver_costs)}人
- **总配送点数**: {self.driver_costs['delivery_points_count'].sum()}个
- **总里程**: {self.driver_costs['total_distance_km'].sum():.2f}公里
- **总成本**: {self.driver_costs['total_cost'].sum():.2f}元

## 💰 成本结构分析
- **里程成本**: {self.driver_costs['mileage_cost'].sum():.2f}元 ({self.driver_costs['mileage_cost'].sum()/self.driver_costs['total_cost'].sum()*100:.1f}%)
  - 燃油成本: {self.driver_costs['fuel_cost'].sum():.2f}元
  - 过路费: {self.driver_costs['toll_cost'].sum():.2f}元
- **时间成本**: {self.driver_costs['time_cost'].sum():.2f}元 ({self.driver_costs['time_cost'].sum()/self.driver_costs['total_cost'].sum()*100:.1f}%)
- **固定成本**: {self.driver_costs['fixed_cost'].sum():.2f}元 ({self.driver_costs['fixed_cost'].sum()/self.driver_costs['total_cost'].sum()*100:.1f}%)

## 🏢 分公司表现排名

### 成本效率最优 (元/公里)
"""
        # 按成本效率排序
        efficiency_ranking = self.branch_summary.sort_values('成本效率')
        for i, row in efficiency_ranking.iterrows():
            report += f"{row.name + 1}. {row['branch_name']}: {row['成本效率']:.2f}元/公里\n"

        report += f"""
### 配送规模最大 (配送点数)
"""
        # 按配送点数排序
        scale_ranking = self.branch_summary.sort_values('配送点总数', ascending=False)
        for i, row in scale_ranking.iterrows():
            report += f"{i + 1}. {row['branch_name']}: {row['配送点总数']}个配送点\n"

        report += f"""
## 🚚 司机绩效分析
- **平均单点成本**: {self.driver_costs['avg_cost_per_point'].mean():.2f}元/点
- **最低单点成本**: {self.driver_costs['avg_cost_per_point'].min():.2f}元/点
- **最高单点成本**: {self.driver_costs['avg_cost_per_point'].max():.2f}元/点
- **成本标准差**: {self.driver_costs['avg_cost_per_point'].std():.2f}元

## 📈 关键发现
1. **固定成本占比过高**: 固定成本占总成本的{self.driver_costs['fixed_cost'].sum()/self.driver_costs['total_cost'].sum()*100:.1f}%，说明需要提高配送密度来摊薄固定成本
2. **分公司效率差异显著**: 最优与最差分公司的成本效率相差{efficiency_ranking['成本效率'].max()/efficiency_ranking['成本效率'].min():.1f}倍
3. **里程与成本相关性**: 配送里程是影响成本的主要因素之一

## 💡 优化建议
1. **提高配送密度**: 增加单次配送的点数，降低单点固定成本
2. **路径优化**: 优化配送路径规划，减少无效里程
3. **区域调配**: 将高效率分公司的经验推广到其他分公司
4. **司机培训**: 针对成本效率较低的司机进行路径规划培训

---
*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        return report

    def save_full_report(self, output_dir: str = "data/reports"):
        """保存完整分析报告"""
        import os
        os.makedirs(output_dir, exist_ok=True)

        # 生成图表
        self.generate_cost_structure_chart(f"{output_dir}/成本结构分析.png")
        self.generate_branch_comparison_chart(f"{output_dir}/分公司对比分析.png")
        self.generate_driver_performance_chart(f"{output_dir}/司机绩效分析.png")

        # 保存文字报告
        report_text = self.generate_summary_report()
        with open(f"{output_dir}/配送成本分析报告.md", 'w', encoding='utf-8') as f:
            f.write(report_text)

        print(f"✅ 完整分析报告已保存到 {output_dir}/ 目录")


if __name__ == "__main__":
    # 生成分析报告
    analyzer = CostAnalysisReport(
        driver_cost_file="data/2025-08-20_司机成本分析.csv",
        branch_summary_file="data/2025-08-20_分公司汇总.csv"
    )

    # 生成并保存完整报告
    analyzer.save_full_report()

    # 显示总结报告
    print(analyzer.generate_summary_report())