"""
Meta Platforms 2024-2025财年全年财报回归测试用例
基于 output/META_2024_2025_*.csv 文件作为基准数据
使用新的验证逻辑：与基准数据比较而不是预设范围
"""

from tests.config import TestCase, ValidationResult, DEFAULT_VALIDATORS
from pathlib import Path

def skip_row_count_validation(output_file: Path, expected_file: Path) -> ValidationResult:
    """跳过行数验证，因为SEC模块会提取所有可用指标，而基准数据只包含关键指标"""
    return ValidationResult.success("跳过行数验证（基准数据只包含关键指标，SEC模块提取所有指标）")

# 创建自定义验证器列表，排除行数验证
custom_validators = [
    validator for validator in DEFAULT_VALIDATORS 
    if validator.__name__ != 'validate_row_count'
]

test_case = TestCase(
    name="meta_2024_2025",
    ticker="META",
    year=None,  # 使用年份范围模式，所以设为None
    quarter=None,
    start_year=2024,  # 起始年份
    end_year=2025,    # 结束年份
    description="Meta Platforms 2024-2025财年全年财报数据回归测试",
    expected_files=[
        "Balance_Sheet.csv",
        "Cash_Flow.csv",
        "Income_Statement.csv"
    ],
    key_indicators=[
        # 利润表关键指标
        "RevenueFromContractWithCustomerExcludingAssessedTax",  # 营收
        "NetIncomeLoss",  # 净利润
        "OperatingIncomeLoss",  # 营业利润
        
        # 资产负债表关键指标
        "Assets",  # 总资产
        "Liabilities",  # 总负债
        "StockholdersEquity",  # 股东权益
        
        # 现金流量表关键指标
        "NetCashProvidedByUsedInOperatingActivities",  # 经营活动现金流
        "NetCashProvidedByUsedInInvestingActivities",  # 投资活动现金流
        "NetCashProvidedByUsedInFinancingActivities"  # 融资活动现金流
    ],
    custom_validators=custom_validators
)
