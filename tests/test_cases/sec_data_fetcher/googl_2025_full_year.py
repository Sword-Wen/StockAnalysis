"""
谷歌(Alphabet) 2025财年全年财报回归测试用例
基于 output/GOOG_2025_*.csv 文件作为基准数据
使用新的验证逻辑：与基准数据比较而不是预设范围
"""

from tests.config import TestCase

test_case = TestCase(
    name="googl_2025_full_year",
    ticker="GOOGL",
    year=2025,
    quarter=None,  # 全年测试
    description="谷歌(Alphabet) 2025财年全年财报数据回归测试",
    expected_files=[
        "Balance_Sheet.csv",
        "Cash_Flow.csv",
        "Income_Statement.csv"
    ],
    key_indicators=[
        # 利润表关键指标
        "Revenues",
        "NetIncomeLoss", 
        "OperatingIncomeLoss",
        
        # 资产负债表关键指标
        "Assets",
        "Liabilities",
        
        # 现金流量表关键指标（使用实际存在的指标）
        "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByUsedInInvestingActivities",
        "NetCashProvidedByUsedInFinancingActivities"
    ]
)