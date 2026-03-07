# SEC Financial Data Extractor

一个Python工具，用于通过SEC REST API获取美股财报数据，包括资产负债表、利润表和现金流量表。

## 功能特性

- ✅ **股票代码自动转换**：优先使用股票代码（如AAPL），内部自动转换为CIK
- ✅ **多种时间过滤模式**：
  - 特定年份（如2023年）
  - 特定季度（如2023年Q4）
  - 年份范围（如2020-2023年）
  - 季度范围（如Q1 2022 - Q4 2023）
- ✅ **智能指标匹配**：支持指标别名映射、部分匹配和基于单词的相似度匹配
- ✅ **数据去重机制**：避免重复提取相同数据
- ✅ **三表分离输出**：生成三个独立的CSV文件
- ✅ **透视表导出**：支持导出为透视表格式（列=期间，行=指标，值=数值）
- ✅ **缓存机制**：减少重复API调用，提高效率
- ✅ **命令行接口**：提供易用的CLI工具
- ✅ **详细日志**：完整的操作日志和错误处理
- ✅ **指标发现工具**：帮助查找特定公司的可用财务指标
- ✅ **代理支持**：支持通过代理服务器访问SEC API
- ✅ **智能默认行为**：年份范围模式默认只返回年度数据

## 安装依赖

项目使用Python 3.7+，需要以下依赖：

```bash
# 如果pip可用
pip install requests pandas python-dateutil

# 或者使用系统包管理器
```

## 项目结构

```
sec_data_fetcher/
├── __init__.py              # 包初始化
├── config.py               # 配置文件（API端点、指标映射等）
├── client.py               # SEC API客户端
├── ticker_mapper.py        # 股票代码↔CIK映射器
├── data_extractor.py       # 财报数据提取器（包含智能匹配逻辑）
├── time_processor.py       # 时间范围处理器
├── csv_exporter.py         # CSV导出器
├── main.py                 # 主程序/命令行接口
├── test.py                 # 测试脚本
└── requirements.txt        # 依赖包列表

tests/                      # 回归测试套件
├── __init__.py             # 包初始化
├── config.py               # 测试配置模块
├── test_runner.py          # 回归测试运行器
├── README.md               # 测试套件文档
├── fixtures/               # 基准数据目录
│   ├── googl_2025_full_year/   # 谷歌2025年全年基准数据
│   ├── googl_2025_q3/          # 谷歌2025年Q3基准数据
│   └── meta_2024_2025/         # Meta 2024-2025年基准数据
└── test_cases/             # 测试用例定义
    ├── googl_2025_full_year.py
    ├── googl_2025_q3.py
    └── meta_2024_2025.py
```

## 使用方法

### 命令行接口

```bash
# 获取特定年份数据
python -m sec_data_fetcher.main fetch AAPL --year 2023

# 获取特定季度数据
python -m sec_data_fetcher.main fetch MSFT --year 2023 --quarter 4

# 获取年份范围数据
python -m sec_data_fetcher.main fetch GOOGL --start-year 2020 --end-year 2023

# 获取季度范围数据
python -m sec_data_fetcher.main fetch AMZN --start-year 2022 --start-quarter 1 --end-year 2023 --end-quarter 4

# 使用累计数据（截至季度的9个月合计）
python -m sec_data_fetcher.main fetch GOOG --year 2025 --quarter 3 --accumulated

# 只获取年度数据（FY）
python -m sec_data_fetcher.main fetch META --start-year 2024 --end-year 2025 --annual-only

# 使用代理服务器
python -m sec_data_fetcher.main fetch AAPL --year 2023 --proxy http://127.0.0.1:10808

# 透视表功能
python -m sec_data_fetcher.main fetch GOOGL --start-year 2015 --end-year 2024 --pivot  # 年度透视表
python -m sec_data_fetcher.main fetch AAPL --year 2024 --pivot --period-type quarterly  # 季度透视表
python -m sec_data_fetcher.main fetch MSFT --start-year 2020 --end-year 2023 --pivot --period-type annual  # 年度透视表

# 搜索股票代码
python -m sec_data_fetcher.main search AAP --limit 5

# 查看统计信息
python -m sec_data_fetcher.main stats

# 清除缓存
python -m sec_data_fetcher.main clear-cache
```

### Python API

```python
from sec_data_fetcher import SECDataFetcher

# 初始化提取器（支持代理）
extractor = SECDataFetcher(proxy_url='http://127.0.0.1:10808')

# 获取财务数据（基础用法）
result = extractor.fetch_financial_data(
    ticker='AAPL',
    year=2023,
    output_dir='output'
)

# 获取财务数据（高级用法）
result = extractor.fetch_financial_data(
    ticker='GOOGL',
    start_year=2015,
    end_year=2024,
    output_dir='output',
    annual_only=True,      # 只获取年度数据
    pivot=True,            # 导出为透视表格式
    period_type='annual'   # 年度透视表
)

# 获取季度透视表数据
result = extractor.fetch_financial_data(
    ticker='AAPL',
    year=2024,
    quarter=4,
    output_dir='output',
    pivot=True,
    period_type='quarterly'  # 季度透视表
)

# 搜索股票代码
search_results = extractor.search_tickers('AAP', limit=5)

# 获取统计信息
stats = extractor.get_mapping_stats()

# 获取公司可用指标
available_indicators = extractor.get_available_indicators('GOOG')
```

## 输出文件

对于每个请求，工具会生成：

### 1. 标准格式CSV文件
- `{TICKER}_{YEAR}_Balance_Sheet.csv` - 资产负债表
- `{TICKER}_{YEAR}_Income_Statement.csv` - 利润表
- `{TICKER}_{YEAR}_Cash_Flow.csv` - 现金流量表

### 2. 透视表格式CSV文件（使用 `--pivot` 参数时）
- `{TICKER}_{YEAR}_Balance_Sheet_Pivot.csv` - 资产负债表透视表
- `{TICKER}_{YEAR}_Income_Statement_Pivot.csv` - 利润表透视表
- `{TICKER}_{YEAR}_Cash_Flow_Pivot.csv` - 现金流量表透视表

**透视表格式特点**：
- **列**：年份/季度（从左到右，由远及近）
- **行**：指标（使用简洁财报命名）
- **值**：数值（千分位分隔符，EPS保持2位小数）
- **数据去重**：同一指标同一期间取最新filed日期的记录

### 3. 汇总报告
- `{TICKER}_export_summary.txt` - 导出汇总信息

## 支持的GAAP指标

### 资产负债表
- Assets（资产）
- Liabilities（负债）
- StockholdersEquity（股东权益）
- AssetsCurrent（流动资产）
- LiabilitiesCurrent（流动负债）
- CashAndCashEquivalentsAtCarryingValue（现金及现金等价物）
- 等15个核心指标

### 利润表
- RevenueFromContractWithCustomerExcludingAssessedTax（收入）
- NetIncomeLoss（净利润）
- GrossProfit（毛利润）
- OperatingIncomeLoss（营业利润）
- EarningsPerShareBasic（基本每股收益）
- EarningsPerShareDiluted（稀释每股收益）
- CostOfGoodsAndServicesSold（营业成本）
- ResearchAndDevelopmentExpense（研发费用）
- SellingGeneralAndAdministrativeExpense（销售和一般行政费用）
- IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest（税前利润）
- IncomeTaxExpenseBenefit（所得税费用）
- 等13个核心指标

### 现金流量表
- NetCashProvidedByUsedInOperatingActivities（经营活动现金流）
- NetCashProvidedByUsedInInvestingActivities（投资活动现金流）
- NetCashProvidedByUsedInFinancingActivities（融资活动现金流）
- 等11个核心指标

## 智能指标匹配系统

### 解决的问题
1. **时间数据混乱**：修复了年度数据和季度数据混合的问题
2. **重复数据**：解决了多个配置指标匹配到同一个SEC指标的问题
3. **指标缺失**：改进了指标匹配逻辑，提高指标发现率

### 匹配策略
1. **精确匹配**：直接匹配配置的指标名称
2. **别名映射**：支持指标别名（如"Revenues"映射到"RevenueFromContractWithCustomerExcludingAssessedTax"）
3. **部分匹配**：支持包含关系的匹配
4. **基于单词的相似度匹配**：通过共同单词数量进行匹配

### 数据去重
当多个配置指标匹配到同一个实际SEC指标时，系统会自动去重，只保留第一个匹配的指标。

## 配置说明

在 `config.py` 中可以配置：

- **SEC API端点**：默认使用SEC官方REST API
- **用户代理**：必须设置有效的User-Agent（SEC API要求）
- **速率限制**：默认10请求/秒（SEC推荐）
- **缓存设置**：缓存过期时间、缓存目录等
- **GAAP指标**：可以自定义需要提取的财务指标
- **指标别名**：可以添加指标别名映射关系

## 常见问题与解决方案

### 1. 季度数据混入年度数据
**问题**：获取年度数据时混入了季度数据
**解决方案**：系统已修复时间过滤逻辑，确保只返回年度数据

### 2. 重复数据行
**问题**：同一指标出现多次
**解决方案**：添加了数据去重机制，基于(日期, 实际指标, 值, Frame)进行去重

### 3. 指标名称不匹配
**问题**：不同公司使用不同的指标名称
**解决方案**：使用智能指标匹配系统，支持多种匹配策略

### 4. 单季度与累计数据混合
**问题**：SEC API同时返回单季度数据（Three Months Ended）和截至该季度的累计数据（Nine Months Ended），导致每个指标都有双份
**解决方案**：使用 `--accumulated` 开关参数控制数据选择：
- 默认（不加参数）：仅输出单季度数据（Frame列包含季度标识，如CY2025Q3）
- 添加 `--accumulated` 参数：仅输出累计数据（Frame列为空）

### 5. 特定指标缺失
**问题**：某些公司可能没有标准的指标名称
**解决方案**：
- 使用指标发现工具查找实际可用指标
- 添加自定义指标别名
- 使用部分匹配或基于单词的匹配

## 指标发现工具

```python
# 查找特定公司的可用指标
from sec_data_fetcher.client import SECClient
from sec_data_fetcher.ticker_mapper import TickerMapper

client = SECClient()
mapper = TickerMapper()
cik = mapper.get_cik('GOOG')
company_data = client.get_company_facts(cik)

# 查找所有利润表相关指标
gaap_facts = company_data['facts']['us-gaap']
for indicator in gaap_facts.keys():
    label = gaap_facts[indicator].get('label', '')
    if any(keyword in label for keyword in ['Income', 'Revenue', 'Expense', 'Profit']):
        print(f'{indicator}: {label}')
```

## 测试

运行测试脚本验证功能：

```bash
python sec_data_fetcher/test.py
```

测试包括：
- 股票代码映射测试
- 单年份数据获取测试
- 单季度数据获取测试
- 年份范围数据获取测试
- 季度范围数据获取测试
- 无效股票代码测试
- 缓存操作测试
- 指标匹配测试

## 回归测试

**重要提示：在修改代码后、正式提交前，都应该执行回归测试，以确保没有引入新的问题而破坏了原有功能。**

项目包含一个完整的回归测试套件，位于 `tests/` 目录中。回归测试通过比较新生成的财务数据与基准数据，验证数据提取功能的正确性和一致性。

### 运行回归测试

```bash
# 运行所有回归测试用例
python tests/test_runner.py --all --verbose

# 运行特定测试用例
python tests/test_runner.py --test-case googl_2025_full_year

# 生成HTML格式的详细报告
python tests/test_runner.py --all --generate-report
```

### 回归测试工作原理

1. **数据提取**：使用真实SEC API提取指定股票代码和时间段的财务数据
2. **基准比较**：将新提取的数据与 `tests/fixtures/` 目录中的基准数据进行比较
3. **多维度验证**：
   - 文件存在性和大小验证
   - CSV文件结构验证（必需列检查）
   - 行数一致性验证
   - 关键财务指标数值验证（允许0.01%的微小差异）

### 测试用例配置

回归测试套件支持多种测试场景：
- **单一年份测试**：如谷歌2025年全年财报数据测试
- **单季度测试**：如谷歌2025年Q3财报数据测试  
- **年份范围测试**：如Meta 2024-2025年财报数据测试

### 开发流程建议

1. **修改代码前**：确保现有回归测试全部通过
2. **修改代码后**：立即运行回归测试验证修改是否破坏了现有功能
3. **提交代码前**：必须确保所有回归测试通过
4. **添加新功能时**：考虑添加新的测试用例到回归测试套件

### 查看详细文档

更多关于回归测试套件的详细信息，请查看 `tests/README.md`。

## 注意事项

1. **网络连接**：需要能够访问SEC官网（https://www.sec.gov）
2. **用户代理**：SEC API要求有效的User-Agent头
3. **速率限制**：遵守SEC的API使用限制（10请求/秒）
4. **数据延迟**：财报数据通常在季度结束后几周内可用
5. **缓存目录**：默认在当前目录创建 `.sec_cache` 目录存储缓存数据
6. **指标差异**：不同公司可能使用不同的指标名称，系统会尽力匹配

## 故障排除

### 常见问题

1. **"Ticker not found"**：股票代码不存在或SEC数据库未收录
2. **"No financial data found"**：指定时间段内无财报数据
3. **网络连接错误**：检查网络连接和代理设置
4. **API限制错误**：降低请求频率或等待后重试
5. **指标匹配失败**：使用指标发现工具查看实际可用指标

### 调试模式

设置环境变量查看详细日志：

```bash
# Windows
set LOG_LEVEL=DEBUG
python -m sec_data_fetcher.main fetch AAPL --year 2023

# Linux/Mac
export LOG_LEVEL=DEBUG
python -m sec_data_fetcher.main fetch AAPL --year 2023
```

## 更新日志

### 2026-03-06 v0.1.1-alpha 重要更新
1. **透视表导出功能**：新增 `--pivot` 命令行参数，支持导出为透视表格式
   - 列：年份/季度（从左到右，由远及近）
   - 行：指标（使用简洁财报命名）
   - 值：数值（千分位分隔符，EPS保持2位小数）
2. **新增命令行参数**：
   - `--proxy`：代理服务器支持（如 `http://127.0.0.1:10808`）
   - `--annual-only`：只获取年度数据（FY）
   - `--period-type`：透视表期间类型（annual/quarterly）
3. **智能默认行为**：
   - 年份范围模式（如 `--start-year 2020 --end-year 2023`）默认只返回年度数据
   - 单年份模式（如 `--year 2023`）默认只返回年度数据
4. **配置更新**：新增 `INDICATOR_SHORT_NAMES` 指标简称映射（约45个指标）
5. **默认输出目录**：改为 `output` 目录
6. **数据去重优化**：透视表数据去重逻辑，同一指标同一期间取最新filed日期的记录

### 2026-03-01 重要更新
1. **添加累计数据开关**：新增 `--accumulated` 命令行参数，支持选择单季度数据或累计数据
2. **修复时间过滤问题**：确保年度数据不混入季度数据
3. **添加数据去重机制**：避免重复数据行
4. **改进指标匹配系统**：支持别名映射、部分匹配和基于单词的匹配
5. **添加指标发现工具**：帮助查找特定公司的可用指标
6. **优化错误处理**：提供更详细的错误信息和调试信息

### 2026-02-23 重要更新
1. **修复时间过滤问题**：确保年度数据不混入季度数据
2. **添加数据去重机制**：避免重复数据行
3. **改进指标匹配系统**：支持别名映射、部分匹配和基于单词的匹配
4. **添加指标发现工具**：帮助查找特定公司的可用指标
5. **优化错误处理**：提供更详细的错误信息和调试信息

## 许可证

本项目仅供学习和研究使用，请遵守SEC的数据使用条款。