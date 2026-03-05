"""
Meta Platforms 2025财年Q1-Q4单季度财报回归测试用例
基于 output/META_2025_2025_*.csv 文件作为基准数据
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
    name="meta_2025",
    ticker="META",
    year=2025,  # 单一年份
    quarter=None,  # 使用季度范围模式
    start_year=2025,  # 起始年份
    end_year=2025,    # 结束年份
    start_quarter=1,  # 起始季度
    end_quarter=4,    # 结束季度
    description="Meta Platforms 2025财年Q1-Q4单季度财报数据回归测试",
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
        "CostOfGoodsAndServicesSold",  # 营业成本
        "ResearchAndDevelopmentExpense",  # 研发费用
        "SellingGeneralAndAdministrativeExpense",  # 销售和营销费用
        "GeneralAndAdministrativeExpense",  # 一般及行政费用
        
        # 资产负债表关键指标
        "Assets",  # 总资产
        "Liabilities",  # 总负债
        "StockholdersEquity",  # 股东权益
        "AssetsCurrent",  # 流动资产
        "LiabilitiesCurrent",  # 流动负债
        "CashAndCashEquivalentsAtCarryingValue",  # 现金及现金等价物
        "AccountsReceivableNetCurrent",  # 应收账款
        "Goodwill",  # 商誉
        
        # 现金流量表关键指标
        "NetCashProvidedByUsedInOperatingActivities",  # 经营活动现金流
        "NetCashProvidedByUsedInInvestingActivities",  # 投资活动现金流
        "NetCashProvidedByUsedInFinancingActivities",  # 融资活动现金流
        "PaymentsToAcquirePropertyPlantAndEquipment",  # 资本支出
        "PaymentsForRepurchaseOfCommonStock",  # 股票回购
        "PaymentsOfDividends",  # 股息支付
    ],
    custom_validators=custom_validators
)