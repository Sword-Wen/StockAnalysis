# SEC财务数据回归测试套件

## 概述

这是一个用于验证SEC财务数据提取器功能的回归测试套件。测试套件通过比较新生成的财务数据与基准数据，确保数据提取功能的正确性和一致性。

## 目录结构

```
tests/
├── README.md                    # 本文档
├── __init__.py                  # 包初始化文件
├── config.py                    # 测试配置模块
├── test_runner.py               # 完整回归测试运行器
├── fixtures/                    # 基准数据目录
│   ├── googl_2025_full_year/   # 谷歌2025年全年基准数据
│   │   ├── Balance_Sheet.csv
│   │   ├── Cash_Flow.csv
│   │   └── Income_Statement.csv
│   └── googl_2025_q3/          # 谷歌2025年Q3基准数据
│       ├── Balance_Sheet.csv
│       ├── Cash_Flow.csv
│       └── Income_Statement.csv
├── test_cases/                  # 测试用例定义
│   ├── __init__.py
│   ├── googl_2025_full_year.py # 谷歌2025年全年测试用例
│   └── googl_2025_q3.py        # 谷歌2025年Q3测试用例
└── __pycache__/                # Python缓存目录
```

## 功能特性

✅ **智能验证系统**：与基准数据比较而不是预设范围
✅ **多维度验证**：文件存在性、大小、结构、行数、关键指标
✅ **灵活的测试用例**：支持自定义验证规则和关键指标
✅ **详细报告**：控制台输出和HTML格式报告
✅ **模拟数据提取**：支持模拟模式，便于调试
✅ **Unicode安全输出**：处理Windows控制台编码问题

## 使用方法

### 运行所有测试

```bash
# 运行所有测试用例
python tests/test_runner.py --all --verbose

# 生成HTML报告
python tests/test_runner.py --all --generate-report
```

### 运行单个测试用例

```bash
# 运行特定测试用例
python tests/test_runner.py --test-case googl_2025_full_year

# 运行特定测试用例并显示详细输出
python tests/test_runner.py --test-case googl_2025_full_year --verbose
```

### 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--test-case` | 运行特定测试用例 | `--test-case googl_2025_full_year` |
| `--all` | 运行所有测试用例 | `--all` |
| `--verbose` | 显示详细输出 | `--verbose` |
| `--generate-report` | 生成HTML报告 | `--generate-report` |

## 测试用例配置

### 创建新的测试用例

1. 在 `tests/test_cases/` 目录下创建新的Python文件
2. 定义测试用例对象
3. 准备基准数据

### 示例测试用例

```python
# tests/test_cases/example_test.py
from tests.config import TestCase

test_case = TestCase(
    name="example_test",          # 测试用例名称（唯一标识符）
    ticker="AAPL",               # 股票代码
    year=2024,                   # 年份
    quarter=4,                   # 季度（None表示全年）
    description="苹果公司2024年Q4财报数据测试",
    expected_files=[             # 期望生成的CSV文件
        "Balance_Sheet.csv",
        "Cash_Flow.csv", 
        "Income_Statement.csv"
    ],
    key_indicators=[             # 关键指标列表
        "Revenues",
        "NetIncomeLoss",
        "Assets",
        "Liabilities"
    ],
    skip=False                   # 是否跳过此测试
)
```

### 准备基准数据

1. 在 `tests/fixtures/` 目录下创建与测试用例同名的子目录
2. 将基准CSV文件复制到该目录
3. 确保基准文件包含以下必需列：
   - `Date`, `Indicator`, `Label`, `Value`, `Unit`
   - `Company Name`, `Ticker`, `CIK`
   - `Fiscal Year`, `Fiscal Period`

## 验证逻辑

### 验证类型

1. **文件存在性验证**：检查输出文件是否存在
2. **文件大小验证**：检查文件大小是否合理（最小1KB）
3. **CSV结构验证**：验证CSV文件包含所有必需列
4. **行数验证**：比较输出文件和基准文件的行数
5. **关键指标验证**：比较关键财务指标的数值

### 关键指标验证机制

新的验证逻辑改为**与基准数据比较**而不是预设范围：

1. **读取指标值**：从输出文件和基准文件中读取相同指标的值
2. **计算差异**：计算两个值的绝对差异和百分比差异
3. **允许差异**：允许0.01%的微小差异（可配置）
4. **智能匹配**：只在相关文件中验证相关指标

### 验证示例

```python
# 验证关键指标
result = validate_key_indicator(
    output_file=output_path,
    expected_file=expected_path,
    indicator_name="Revenues"
)

# 结果示例
# ✅ 通过: 指标 Revenues 匹配: 123456789 ≈ 123456789 (差异: 0.0000%)
# ❌ 失败: 指标 Revenues 不匹配: 123456789 ≠ 123456000 (差异: 0.0006%)
```

## 配置说明

### 全局配置 (`tests/config.py`)

```python
class TestConfig:
    ALLOWED_DIFF_PERCENT = 0.01  # 允许的差异百分比
    REQUIRED_COLUMNS = [...]     # CSV必需列
    KEY_INDICATORS = {...}       # 关键指标分类
    TEST_TIMEOUT = 300           # 测试超时时间（秒）
    VERBOSE = False              # 是否启用详细日志
    GENERATE_REPORT = False      # 是否生成HTML报告
```

### 测试用例类 (`TestCase`)

```python
@dataclass
class TestCase:
    name: str                    # 测试用例名称
    ticker: str                  # 股票代码
    year: int                    # 年份
    quarter: Optional[int]       # 季度
    description: str             # 测试描述
    expected_files: List[str]    # 期望文件列表
    key_indicators: List[str]    # 关键指标列表
    custom_validators: List[Callable]  # 自定义验证器
    skip: bool                   # 是否跳过
```

## 示例运行

### 运行完整测试

```bash
$ python tests/test_runner.py --all --verbose --generate-report

SEC财务数据回归测试运行器
============================================================
发现 2 个测试用例
发现测试用例: googl_2025_full_year - 谷歌(Alphabet) 2025财年全年财报数据回归测试
发现测试用例: googl_2025_q3 - 谷歌(Alphabet) 2025财年Q3财报数据回归测试

============================================================
运行测试用例: googl_2025_full_year
描述: 谷歌(Alphabet) 2025财年全年财报数据回归测试
============================================================
执行数据提取: GOOGL 2025
[WARN] 注意: 当前使用模拟数据提取
实际使用时需要调用 sec_data_fetcher 模块的真实数据提取功能
  复制基准数据: Balance_Sheet.csv
  复制基准数据: Cash_Flow.csv
  复制基准数据: Income_Statement.csv

验证文件: Balance_Sheet.csv
  基准文件: tests/fixtures/googl_2025_full_year/Balance_Sheet.csv
  输出文件: test_output/googl_2025_full_year/Balance_Sheet.csv
  [PASS] validate_file_exists: 文件存在: Balance_Sheet.csv
  [PASS] validate_file_size: 文件大小正常: 15.2KB
  [PASS] validate_csv_structure: CSV结构验证通过: 10列
  [PASS] validate_row_count: 行数匹配: 150行
  [PASS] 关键指标 Assets: 指标 Assets 匹配: 123456789 ≈ 123456789 (差异: 0.0000%)
  [PASS] 关键指标 Liabilities: 指标 Liabilities 匹配: 98765432 ≈ 98765432 (差异: 0.0000%)

============================================================
[PASS] 测试通过: 通过 18/18 项验证

============================================================
SEC财务数据回归测试报告
============================================================
测试时间: 2026-03-04 09:16:45
总耗时: 2.56秒
测试用例总数: 2
通过: 2
失败: 0
通过率: 100.0%
============================================================

googl_2025_full_year: [PASS] 通过
  描述: 谷歌(Alphabet) 2025财年全年财报数据回归测试
  耗时: 1.23秒
  结果: 通过 18/18 项验证

googl_2025_q3: [PASS] 通过
  描述: 谷歌(Alphabet) 2025财年Q3财报数据回归测试
  耗时: 1.33秒
  结果: 通过 18/18 项验证

============================================================
[CELE] 所有测试用例通过！

[CHART] HTML测试报告已生成: test_output/test_report_20260304_091645.html
```

## 故障排除

### 常见问题

1. **"基准数据目录不存在"**
   - 确保在 `tests/fixtures/` 目录下创建了与测试用例同名的子目录
   - 确保子目录中包含所有基准CSV文件

2. **"文件不存在"**
   - 检查输出目录是否正确生成
   - 确保数据提取功能正常工作

3. **"CSV结构验证失败"**
   - 确保输出文件包含所有必需列
   - 检查CSV文件的编码格式（应为UTF-8）

4. **"关键指标不匹配"**
   - 检查基准数据和输出数据是否对应同一时间段
   - 确认指标名称是否正确
   - 检查数据提取逻辑是否有变化

### 调试模式

```bash
# 设置详细输出
python tests/test_runner.py --test-case googl_2025_full_year --verbose

# 查看测试配置
python -c "from tests.config import TestConfig; print(TestConfig.__dict__)"
```

## 更新日志

### 2026-03-04 重要更新

1. **修复验证逻辑**：关键指标验证改为与基准数据比较而不是预设范围
2. **添加智能匹配**：只在相关文件中验证相关指标
3. **改进报告系统**：支持HTML格式的详细报告
4. **添加模拟模式**：便于调试和开发
5. **优化错误处理**：提供更清晰的错误信息

### 2026-03-03 初始版本

1. **创建测试框架**：基础测试结构和验证系统
2. **添加测试用例**：谷歌2025年全年和Q3测试用例
3. **实现验证器**：文件存在性、大小、结构、行数验证
4. **创建测试运行器**：完整测试运行器

## 注意事项

1. **基准数据**：基准数据应来自经过验证的数据源
2. **测试环境**：确保测试环境与生产环境一致
3. **数据更新**：定期更新基准数据以反映最新的财务数据
4. **性能考虑**：测试可能涉及大量数据，注意系统资源
5. **网络依赖**：实际数据提取需要网络连接

## 扩展开发

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

### 集成真实数据提取

修改 `test_runner.py` 中的 `_simulate_data_extraction` 方法，替换为真实的数据提取调用：

```python
def _real_data_extraction(self, test_case: TestCase):
    """真实数据提取"""
    from sec_data_fetcher import SECDataFetcher
    
    extractor = SECDataFetcher()
    extractor.fetch_financial_data(
        ticker=test_case.ticker,
        year=test_case.year,
        quarter=test_case.quarter,
        output_dir=str(test_case.output_dir)
    )
```

## 许可证

本测试套件是SEC财务数据提取器项目的一部分，仅供学习和研究使用。