# 财务数据回归测试套件

## 概述

这是一个用于验证 StockAnalysis 项目中各子模块（sec_data_fetcher、stock_analyzer 等）功能的回归测试套件。测试套件通过比较新生成的数据与基准数据，确保各模块功能的正确性和一致性。

## 目录结构

```
tests/
├── README.md                              # 本文档
├── __init__.py                            # 包初始化文件
├── config.py                              # 测试配置模块
├── test_runner.py                         # 回归测试运行器
├── fixtures/                              # 基准数据目录（按子模块分类）
│   ├── sec_data_fetcher/                  # SEC 数据提取器基准数据
│   │   ├── googl_2025_full_year/
│   │   │   ├── Balance_Sheet.csv
│   │   │   ├── Cash_Flow.csv
│   │   │   └── Income_Statement.csv
│   │   └── ...
│   └── stock_analyzer/                    # stock_analyzer 基准数据
│       └── aapl_financial_indicators/
│           └── AAPL_financial_indicators.csv
│
└── test_cases/                           # 测试用例定义（按子模块分类）
    ├── __init__.py
    ├── sec_data_fetcher/                  # SEC 数据提取器测试用例
    │   ├── __init__.py
    │   ├── googl_2025_full_year.py
    │   ├── googl_2025_q3.py
    │   └── ...
    └── stock_analyzer/                    # stock_analyzer 测试用例
        ├── __init__.py
        └── aapl_financial_indicators.py
```

## 功能特性

✅ **多模块支持**：支持 sec_data_fetcher、stock_analyzer 等多个子模块
✅ **智能验证系统**：与基准数据比较而不是预设范围
✅ **模块过滤运行**：支持按模块类型筛选测试
✅ **多维度验证**：文件存在性、大小、结构、行数、关键指标
✅ **灵活的测试用例**：支持自定义验证规则和关键指标
✅ **详细报告**：控制台输出详细结果
✅ **Unicode安全输出**：处理Windows控制台编码问题

## 使用方法

### 运行所有测试

```bash
# 运行所有测试用例
python -m tests.test_runner --all --verbose

# 运行所有测试用例（详细输出）
python -m tests.test_runner --all
```

### 按模块运行测试

```bash
# 只运行 stock_analyzer 模块测试
python -m tests.test_runner --all --module stock_analyzer

# 只运行 sec_data_fetcher 模块测试
python -m tests.test_runner --all --module sec_data_fetcher
```

### 运行单个测试用例

```bash
# 运行特定测试用例
python -m tests.test_runner --test-case aapl_financial_indicators

# 运行特定测试用例（详细输出）
python -m tests.test_runner --test-case aapl_financial_indicators --verbose
```

### 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--test-case` | 运行特定测试用例 | `--test-case aapl_financial_indicators` |
| `--all` | 运行所有测试用例 | `--all` |
| `--module` | 按模块筛选测试 | `--module stock_analyzer` |
| `--verbose` | 显示详细输出 | `--verbose` |
| `--generate-report` | 生成HTML报告 | `--generate-report` |

## 测试用例配置

### 创建新的测试用例

1. 在 `tests/test_cases/<模块名>/` 目录下创建新的Python文件
2. 定义测试用例对象，指定 `test_type` 为对应的模块名
3. 准备基准数据到 `tests/fixtures/<模块名>/<用例名>/` 目录

### 示例：sec_data_fetcher 测试用例

```python
# tests/test_cases/sec_data_fetcher/example_test.py
from tests.config import TestCase

test_case = TestCase(
    name="example_test",              # 测试用例名称（唯一标识符）
    ticker="AAPL",                    # 股票代码
    test_type="sec_data_fetcher",    # 模块类型
    year=2024,                       # 年份
    quarter=4,                       # 季度（None表示全年）
    description="苹果公司2024年Q4财报数据测试",
    expected_files=[                  # 期望生成的CSV文件
        "Balance_Sheet.csv",
        "Cash_Flow.csv", 
        "Income_Statement.csv"
    ],
    key_indicators=[                  # 关键指标列表
        "Revenues",
        "NetIncomeLoss",
        "Assets",
        "Liabilities"
    ],
    skip=False                        # 是否跳过此测试
)
```

### 示例：stock_analyzer 测试用例

```python
# tests/test_cases/stock_analyzer/example_indicators.py
from tests.config import TestCase

test_case = TestCase(
    name="example_indicators",        # 测试用例名称
    ticker="AAPL",                    # 股票代码
    test_type="stock_analyzer",      # 模块类型
    start_year=2020,                 # 起始年份
    end_year=2025,                   # 结束年份
    description="苹果公司2020-2025年财务指标测试",
    expected_files=[                  # 期望生成的CSV文件
        "AAPL_financial_indicators.csv"
    ],
    key_indicators=[]                # stock_analyzer 使用完全匹配验证
)
```

### 准备基准数据

1. 在 `tests/fixtures/<模块名>/` 目录下创建与测试用例同名的子目录
2. 将基准CSV文件复制到该目录
3. 对于 sec_data_fetcher，确保基准文件包含以下必需列：
   - `Date`, `Indicator`, `Label`, `Value`, `Unit`
   - `Company Name`, `Ticker`, `CIK`
   - `Fiscal Year`, `Fiscal Period`

## 验证逻辑

### sec_data_fetcher 验证类型

1. **文件存在性验证**：检查输出文件是否存在
2. **文件大小验证**：检查文件大小是否合理（最小1KB）
3. **CSV结构验证**：验证CSV文件包含所有必需列
4. **行数验证**：比较输出文件和基准文件的行数
5. **关键指标验证**：比较关键财务指标的数值（允许0.01%差异）

### stock_analyzer 验证类型

1. **文件存在性验证**：检查输出文件是否存在
2. **文件大小验证**：检查文件大小是否合理
3. **结构验证**：验证指标文件结构（第一列必须为"指标"）
4. **完全匹配验证**：逐单元格比较输出与基准数据

## 配置说明

### 支持的模块类型

```python
# tests/config.py
TEST_MODULES = [
    "sec_data_fetcher",
    "stock_analyzer"
]
```

### 全局配置 (`tests/config.py`)

```python
class TestConfig:
    ALLOWED_DIFF_PERCENT = 0.01    # 允许的差异百分比
    REQUIRED_COLUMNS = [...]        # CSV必需列
    KEY_INDICATORS = {...}          # 关键指标分类
    TEST_TIMEOUT = 300              # 测试超时时间（秒）
    VERBOSE = False                 # 是否启用详细日志
    GENERATE_REPORT = False         # 是否生成HTML报告
```

### 测试用例类 (`TestCase`)

```python
@dataclass
class TestCase:
    name: str                       # 测试用例名称
    ticker: str                     # 股票代码
    test_type: str                  # 模块类型（sec_data_fetcher/stock_analyzer）
    year: Optional[int]             # 年份
    quarter: Optional[int]          # 季度
    start_year: Optional[int]       # 起始年份（年份范围模式）
    end_year: Optional[int]         # 结束年份（年份范围模式）
    description: str                 # 测试描述
    expected_files: List[str]       # 期望文件列表
    key_indicators: List[str]       # 关键指标列表
    custom_validators: List[Callable]  # 自定义验证器
    skip: bool                      # 是否跳过
```

## 扩展开发

### 添加新的子模块支持

1. 在 `TEST_MODULES` 中添加新模块名称
2. 在 `tests/test_cases/` 下创建对应的目录
3. 在 `tests/fixtures/` 下创建对应的目录
4. 在 `test_runner.py` 中添加对应的数据提取逻辑
5. 可选：在 `config.py` 中添加该模块专用的验证器

### 添加自定义验证器

```python
from tests.config import ValidationResult

def custom_validator(filepath: Path) -> ValidationResult:
    """自定义验证器示例"""
    # 实现自定义验证逻辑
    if some_condition:
        return ValidationResult.success("自定义验证通过")
    else:
        return ValidationResult.failure("自定义验证失败")

# 在测试用例中使用
test_case.custom_validators.append(custom_validator)
```

## 故障排除

### 常见问题

1. **"基准数据目录不存在"**
   - 确保在 `tests/fixtures/<模块名>/` 目录下创建了与测试用例同名的子目录

2. **"文件不存在"**
   - 检查输出目录是否正确生成
   - 确保数据提取功能正常工作

3. **"CSV结构验证失败"**
   - 确保输出文件包含所有必需列
   - 检查CSV文件的编码格式

4. **"关键指标不匹配"**
   - 检查基准数据和输出数据是否对应同一时间段
   - 确认指标名称是否正确

### 调试模式

```bash
# 设置详细输出
python -m tests.test_runner --test-case aapl_financial_indicators --verbose

# 查看支持的模块
python -c "from tests.config import TEST_MODULES; print(TEST_MODULES)"
```

## 更新日志

### 2026-03-17 重要更新

1. **多模块支持**：扩展测试框架支持 sec_data_fetcher 和 stock_analyzer
2. **目录重组**：fixtures 和 test_cases 按子模块分类
3. **模块过滤**：添加 --module 参数支持按模块筛选测试
4. **stock_analyzer 验证**：添加完全匹配验证逻辑
5. **新增测试用例**：AAPL 财务指标回归测试

### 2026-03-04 重要更新

1. **修复验证逻辑**：关键指标验证改为与基准数据比较
2. **添加智能匹配**：只在相关文件中验证相关指标

## 许可证

本测试套件是 StockAnalysis 项目的一部分，仅供学习和研究使用。
