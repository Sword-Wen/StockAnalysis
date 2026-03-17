"""
Apple Inc. (AAPL) 财务指标回归测试用例
基于 output/AAPL_financial_indicators.csv 文件作为基准数据
使用完全匹配验证逻辑
"""

from tests.config import TestCase

test_case = TestCase(
    name="aapl_financial_indicators",
    ticker="AAPL",
    test_type="stock_analyzer",
    start_year=2017,  # 起始年份
    end_year=2025,    # 结束年份
    description="Apple Inc. (AAPL) 2017-2025年核心财务指标回归测试",
    expected_files=[
        "AAPL_financial_indicators.csv"
    ],
    key_indicators=[]
)
