"""
回归测试配置模块
定义测试用例结构、验证规则和全局配置
修复关键指标验证逻辑：与基准数据比较而不是预设范围
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable
from pathlib import Path

# 路径配置
PROJECT_ROOT = Path(__file__).parent.parent
TESTS_DIR = Path(__file__).parent
TEST_CASES_DIR = TESTS_DIR / "test_cases"
FIXTURES_DIR = TESTS_DIR / "fixtures"
OUTPUT_DIR = PROJECT_ROOT / "test_output"

# 全局测试配置
class TestConfig:
    """测试全局配置"""
    
    # 允许的差异百分比（用于数值比较）
    ALLOWED_DIFF_PERCENT = 0.01  # 0.01% 差异
    
    # 必需包含的列（所有CSV文件都应包含这些列）
    REQUIRED_COLUMNS = [
        "Date",
        "Indicator", 
        "Label",
        "Value",
        "Unit",
        "Company Name",
        "Ticker",
        "CIK",
        "Fiscal Year",
        "Fiscal Period"
    ]
    
    # 关键财务指标（用于快速验证）
    KEY_INDICATORS = {
        "balance_sheet": [
            "Assets",
            "Liabilities",
            "StockholdersEquity"
        ],
        "income_statement": [
            "Revenues",
            "CostOfGoodsAndServicesSold",
            "OperatingIncomeLoss",
            "NetIncomeLoss"
        ],
        "cash_flow": [
            "NetCashFlow",
            "NetCashFlowFromOperatingActivities",
            "NetCashFlowFromInvestingActivities",
            "NetCashFlowFromFinancingActivities"
        ]
    }
    
    # 测试超时时间（秒）
    TEST_TIMEOUT = 300  # 5分钟
    
    # 是否启用详细日志
    VERBOSE = False
    
    # 是否生成HTML报告
    GENERATE_REPORT = False


# 支持的测试模块类型
TEST_MODULES = [
    "sec_data_fetcher",
    "stock_analyzer"
]


@dataclass
class TestCase:
    """
    测试用例定义
    
    属性:
        name: 测试用例名称（唯一标识符）
        ticker: 股票代码
        test_type: 测试模块类型（如 sec_data_fetcher, stock_analyzer）
        year: 年份（单一年份模式）
        quarter: 季度（None表示全年）
        start_year: 起始年份（年份范围模式）
        end_year: 结束年份（年份范围模式）
        start_quarter: 起始季度（季度范围模式）
        end_quarter: 结束季度（季度范围模式）
        description: 测试描述
        expected_files: 期望生成的CSV文件列表
        key_indicators: 关键指标验证规则（现在只存储指标名称列表）
        custom_validators: 自定义验证函数列表
        skip: 是否跳过此测试
    """
    name: str
    ticker: str
    test_type: str = "sec_data_fetcher"  # 默认使用 sec_data_fetcher
    year: Optional[int] = None
    quarter: Optional[int] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    start_quarter: Optional[int] = None
    end_quarter: Optional[int] = None
    description: str = ""
    expected_files: List[str] = field(default_factory=lambda: [
        "Balance_Sheet.csv",
        "Cash_Flow.csv",
        "Income_Statement.csv"
    ])
    key_indicators: List[str] = field(default_factory=list)  # 改为指标名称列表
    custom_validators: List[Callable] = field(default_factory=list)
    skip: bool = False
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.description:
            if self.start_year is not None and self.end_year is not None:
                # 年份范围模式
                if self.start_quarter is not None and self.end_quarter is not None:
                    # 季度范围模式
                    self.description = f"{self.ticker} {self.start_year}年Q{self.start_quarter}-{self.end_year}年Q{self.end_quarter}财报数据测试"
                else:
                    # 年份范围模式（无季度）
                    self.description = f"{self.ticker} {self.start_year}-{self.end_year}年财报数据测试"
            elif self.quarter:
                # 单一年份季度模式
                self.description = f"{self.ticker} {self.year}年Q{self.quarter}财报数据测试"
            else:
                # 单一年份全年模式
                self.description = f"{self.ticker} {self.year}年全年财报数据测试"
    
    @property
    def fixture_dir(self) -> Path:
        """获取基准数据目录（按子模块分类）"""
        return FIXTURES_DIR / self.test_type / self.name
    
    @property
    def output_dir(self) -> Path:
        """获取输出目录"""
        return OUTPUT_DIR / self.test_type / self.name
    
    def get_expected_file_path(self, filename: str) -> Path:
        """获取基准文件路径"""
        return self.fixture_dir / filename
    
    def get_output_file_path(self, filename: str) -> Path:
        """获取输出文件路径"""
        return self.output_dir / filename
    
    def get_file_type(self, filename: str) -> str:
        """根据文件名获取文件类型"""
        if "Balance" in filename:
            return "balance_sheet"
        elif "Income" in filename:
            return "income_statement"
        elif "Cash" in filename:
            return "cash_flow"
        else:
            return "unknown"


class ValidationResult:
    """验证结果"""
    
    def __init__(self, success: bool, message: str = "", details: Dict[str, Any] = None):
        self.success = success
        self.message = message
        self.details = details or {}
    
    def __bool__(self):
        return self.success
    
    def __str__(self):
        status = "✅ 通过" if self.success else "❌ 失败"
        return f"{status}: {self.message}"
    
    @classmethod
    def success(cls, message: str = "", details: Dict[str, Any] = None):
        """创建成功结果"""
        return cls(True, message, details)
    
    @classmethod
    def failure(cls, message: str = "", details: Dict[str, Any] = None):
        """创建失败结果"""
        return cls(False, message, details)


# 验证函数
def validate_file_exists(filepath: Path) -> ValidationResult:
    """验证文件是否存在"""
    if filepath.exists():
        return ValidationResult.success(f"文件存在: {filepath.name}")
    else:
        return ValidationResult.failure(f"文件不存在: {filepath.name}")


def validate_file_size(filepath: Path, min_size_kb: int = 1) -> ValidationResult:
    """验证文件大小是否合理"""
    if not filepath.exists():
        return ValidationResult.failure(f"文件不存在: {filepath.name}")
    
    size_kb = filepath.stat().st_size / 1024
    if size_kb >= min_size_kb:
        return ValidationResult.success(
            f"文件大小正常: {size_kb:.1f}KB",
            {"size_kb": size_kb}
        )
    else:
        return ValidationResult.failure(
            f"文件大小过小: {size_kb:.1f}KB (最小要求: {min_size_kb}KB)",
            {"size_kb": size_kb, "min_size_kb": min_size_kb}
        )


def validate_csv_structure(filepath: Path, required_columns: List[str]) -> ValidationResult:
    """验证CSV文件结构"""
    import csv
    
    if not filepath.exists():
        return ValidationResult.failure(f"文件不存在: {filepath.name}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
            
            missing_columns = []
            for col in required_columns:
                if col not in headers:
                    missing_columns.append(col)
            
            if not missing_columns:
                return ValidationResult.success(
                    f"CSV结构验证通过: {len(headers)}列",
                    {"headers": headers, "total_columns": len(headers)}
                )
            else:
                return ValidationResult.failure(
                    f"缺少必需列: {', '.join(missing_columns)}",
                    {"headers": headers, "missing_columns": missing_columns}
                )
    except Exception as e:
        return ValidationResult.failure(f"读取CSV文件失败: {e}")


def validate_row_count(filepath1: Path, filepath2: Path) -> ValidationResult:
    """验证两个CSV文件行数是否一致"""
    import csv
    
    if not filepath1.exists():
        return ValidationResult.failure(f"文件1不存在: {filepath1.name}")
    if not filepath2.exists():
        return ValidationResult.failure(f"文件2不存在: {filepath2.name}")
    
    try:
        with open(filepath1, 'r', encoding='utf-8') as f1:
            rows1 = sum(1 for _ in csv.reader(f1))
        
        with open(filepath2, 'r', encoding='utf-8') as f2:
            rows2 = sum(1 for _ in csv.reader(f2))
        
        if rows1 == rows2:
            return ValidationResult.success(
                f"行数匹配: {rows1}行",
                {"rows1": rows1, "rows2": rows2}
            )
        else:
            return ValidationResult.failure(
                f"行数不匹配: {rows1}行 vs {rows2}行",
                {"rows1": rows1, "rows2": rows2, "difference": abs(rows1 - rows2)}
            )
    except Exception as e:
        return ValidationResult.failure(f"比较行数失败: {e}")


def validate_key_indicator(output_file: Path, expected_file: Path, indicator_name: str) -> ValidationResult:
    """验证关键财务指标：比较输出文件和基准文件中的指标值"""
    import csv
    
    if not output_file.exists():
        return ValidationResult.failure(f"输出文件不存在: {output_file.name}")
    
    if not expected_file.exists():
        return ValidationResult.failure(f"基准文件不存在: {expected_file.name}")
    
    try:
        # 从输出文件读取指标值
        output_value = None
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('Indicator') == indicator_name:
                    value_str = row.get('Value', '').replace(',', '').replace('"', '')
                    try:
                        output_value = float(value_str)
                        break
                    except ValueError:
                        continue
        
        if output_value is None:
            return ValidationResult.failure(f"输出文件中未找到指标: {indicator_name}")
        
        # 从基准文件读取指标值
        expected_value = None
        with open(expected_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('Indicator') == indicator_name:
                    value_str = row.get('Value', '').replace(',', '').replace('"', '')
                    try:
                        expected_value = float(value_str)
                        break
                    except ValueError:
                        continue
        
        if expected_value is None:
            return ValidationResult.failure(f"基准文件中未找到指标: {indicator_name}")
        
        # 比较两个值（允许微小差异）
        diff = abs(output_value - expected_value)
        diff_percent = (diff / abs(expected_value)) * 100 if expected_value != 0 else 0
        
        details = {
            "indicator": indicator_name,
            "output_value": output_value,
            "expected_value": expected_value,
            "difference": diff,
            "difference_percent": diff_percent
        }
        
        if diff_percent <= TestConfig.ALLOWED_DIFF_PERCENT:
            return ValidationResult.success(
                f"指标 {indicator_name} 匹配: {output_value} ≈ {expected_value} (差异: {diff_percent:.4f}%)",
                details
            )
        else:
            return ValidationResult.failure(
                f"指标 {indicator_name} 不匹配: {output_value} ≠ {expected_value} (差异: {diff_percent:.4f}%)",
                details
            )
            
    except Exception as e:
        return ValidationResult.failure(f"验证指标失败: {e}")


# 默认验证器集合
DEFAULT_VALIDATORS = [
    validate_file_exists,
    validate_file_size,
    validate_csv_structure,
    validate_row_count
]


# ============ stock_analyzer 专用验证器 ============

def validate_indicator_file_structure(filepath: Path) -> ValidationResult:
    """
    验证财务指标文件结构（stock_analyzer 专用）
    验证列：指标, 2017, 2018, ... 等年份列
    """
    import csv
    
    if not filepath.exists():
        return ValidationResult.failure(f"文件不存在: {filepath.name}")
    
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            headers = next(reader)
            
            # 验证第一列必须是"指标"
            if not headers or headers[0] != "指标":
                return ValidationResult.failure(
                    f"第一列必须是'指标'，实际为: {headers[0] if headers else '空'}",
                    {"headers": headers}
                )
            
            # 验证至少有"指标"列和一年份数据列
            if len(headers) < 2:
                return ValidationResult.failure(
                    f"列数不足，至少需要'指标'列和年份列",
                    {"headers": headers}
                )
            
            return ValidationResult.success(
                f"财务指标文件结构正确: {len(headers)}列",
                {"headers": headers, "total_columns": len(headers)}
            )
    except Exception as e:
        return ValidationResult.failure(f"读取CSV文件失败: {e}")


def validate_indicator_file_exact_match(output_file: Path, expected_file: Path) -> ValidationResult:
    """
    验证财务指标文件完全匹配（stock_analyzer 专用）
    比较输出文件和基准文件的每个单元格
    """
    import csv
    
    if not output_file.exists():
        return ValidationResult.failure(f"输出文件不存在: {output_file.name}")
    
    if not expected_file.exists():
        return ValidationResult.failure(f"基准文件不存在: {expected_file.name}")
    
    try:
        # 读取两个文件
        with open(output_file, 'r', encoding='utf-8-sig') as f:
            output_data = list(csv.reader(f))
        
        with open(expected_file, 'r', encoding='utf-8-sig') as f:
            expected_data = list(csv.reader(f))
        
        # 比较行数
        if len(output_data) != len(expected_data):
            return ValidationResult.failure(
                f"行数不匹配: 输出{len(output_data)}行 vs 基准{len(expected_data)}行",
                {"output_rows": len(output_data), "expected_rows": len(expected_data)}
            )
        
        # 比较每行每列
        differences = []
        for row_idx, (output_row, expected_row) in enumerate(zip(output_data, expected_data)):
            if len(output_row) != len(expected_row):
                differences.append({
                    "row": row_idx,
                    "message": f"列数不匹配: {len(output_row)}列 vs {len(expected_row)}列"
                })
                continue
            
            for col_idx, (out_val, exp_val) in enumerate(zip(output_row, expected_row)):
                # 规范化比较：去除首尾空白
                out_val_norm = out_val.strip()
                exp_val_norm = exp_val.strip()
                
                if out_val_norm != exp_val_norm:
                    differences.append({
                        "row": row_idx,
                        "col": col_idx,
                        "output": out_val_norm,
                        "expected": exp_val_norm
                    })
        
        if differences:
            # 只显示前5个差异
            sample_diffs = differences[:5]
            diff_msg = "; ".join([
                f"行{r['row']}列{r['col']}: '{r['output']}' != '{r['expected']}'" 
                if 'col' in r else r['message']
                for r in sample_diffs
            ])
            return ValidationResult.failure(
                f"存在{len(differences)}处不匹配: {diff_msg}",
                {"total_differences": len(differences), "sample": sample_diffs}
            )
        
        return ValidationResult.success(
            f"财务指标完全匹配: {len(output_data)}行 x {len(output_data[0])}列",
            {"rows": len(output_data), "columns": len(output_data[0])}
        )
        
    except Exception as e:
        return ValidationResult.failure(f"验证失败: {e}")


# stock_analyzer 默认验证器
STOCK_ANALYZER_VALIDATORS = [
    validate_file_exists,
    validate_file_size,
    validate_indicator_file_structure,
    validate_indicator_file_exact_match
]
