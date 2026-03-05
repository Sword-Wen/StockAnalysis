#!/usr/bin/env python3
"""
SEC财务数据回归测试运行器
使用新的验证逻辑：与基准数据比较而不是预设范围
"""

import sys
import os
import time
import argparse
import importlib
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.config import (
    TestCase, TestConfig, ValidationResult,
    TEST_CASES_DIR, FIXTURES_DIR, OUTPUT_DIR,
    validate_file_exists, validate_file_size, validate_csv_structure,
    validate_row_count, validate_key_indicator, DEFAULT_VALIDATORS
)

# 导入真实数据提取器
from sec_financials.main import SECFinancialExtractor


def safe_print(text: str):
    """安全打印函数，处理Windows控制台的Unicode编码问题"""
    try:
        print(text)
    except UnicodeEncodeError:
        # 替换无法显示的Unicode字符
        text = text.replace('✅', '[PASS]').replace('❌', '[FAIL]')
        text = text.replace('⚠️', '[WARN]').replace('🎉', '[CELE]')
        text = text.replace('📊', '[CHART]').replace('✓', '[OK]')
        text = text.replace('✗', '[ERR]')
        print(text)


class TestRunner:
    """测试运行器"""
    
    def __init__(self, verbose: bool = False, generate_report: bool = False):
        self.verbose = verbose
        self.generate_report = generate_report
        self.test_cases: List[TestCase] = []
        self.results: Dict[str, Dict[str, Any]] = {}
        self.start_time = None
        self.end_time = None
        
        # 确保输出目录存在
        OUTPUT_DIR.mkdir(exist_ok=True)
    
    def discover_test_cases(self) -> List[TestCase]:
        """自动发现所有测试用例"""
        test_cases = []
        
        for filepath in TEST_CASES_DIR.glob("*.py"):
            if filepath.name == "__init__.py":
                continue
            
            try:
                # 动态导入测试用例模块
                module_name = f"tests.test_cases.{filepath.stem}"
                module = importlib.import_module(module_name)
                
                # 获取测试用例对象
                if hasattr(module, 'test_case'):
                    test_case = module.test_case
                    if isinstance(test_case, TestCase):
                        test_cases.append(test_case)
                        if self.verbose:
                            safe_print(f"发现测试用例: {test_case.name} - {test_case.description}")
                    else:
                        safe_print(f"警告: {filepath.name} 中的 test_case 不是 TestCase 类型")
                else:
                    safe_print(f"警告: {filepath.name} 中没有找到 test_case 变量")
                    
            except Exception as e:
                safe_print(f"加载测试用例 {filepath.name} 失败: {e}")
                if self.verbose:
                    traceback.print_exc()
        
        return test_cases
    
    def run_test_case(self, test_case: TestCase) -> Dict[str, Any]:
        """运行单个测试用例"""
        safe_print(f"\n{'='*60}")
        safe_print(f"运行测试用例: {test_case.name}")
        safe_print(f"描述: {test_case.description}")
        safe_print(f"{'='*60}")
        
        case_results = {
            "test_case": test_case,
            "start_time": time.time(),
            "validations": [],
            "success": True,
            "message": ""
        }
        
        try:
            # 1. 准备基准数据目录
            if not test_case.fixture_dir.exists():
                safe_print(f"[FAIL] 基准数据目录不存在: {test_case.fixture_dir}")
                safe_print("请将正确的CSV文件复制到该目录作为基准数据")
                case_results["success"] = False
                case_results["message"] = "基准数据目录不存在"
                return case_results
            
            # 2. 运行SEC财务数据提取器
            safe_print(f"执行数据提取: {test_case.ticker} {test_case.year}" + 
                  (f" Q{test_case.quarter}" if test_case.quarter else " 全年"))
            
            # 调用真实的数据提取器
            self._extract_real_data(test_case)
            
            # 3. 运行验证
            validation_results = self._run_validations(test_case)
            case_results["validations"] = validation_results
            
            # 4. 汇总结果
            success_count = sum(1 for r in validation_results if r["success"])
            total_count = len(validation_results)
            
            case_results["success"] = success_count == total_count
            case_results["message"] = f"通过 {success_count}/{total_count} 项验证"
            
            if case_results["success"]:
                safe_print(f"[PASS] 测试通过: {case_results['message']}")
            else:
                safe_print(f"[FAIL] 测试失败: {case_results['message']}")
                
        except Exception as e:
            safe_print(f"[FAIL] 测试执行异常: {e}")
            if self.verbose:
                traceback.print_exc()
            case_results["success"] = False
            case_results["message"] = f"执行异常: {e}"
        
        case_results["end_time"] = time.time()
        case_results["duration"] = case_results["end_time"] - case_results["start_time"]
        
        return case_results
    
    def _extract_real_data(self, test_case: TestCase):
        """使用真实SEC API提取数据"""
        safe_print("[INFO] 开始从SEC API提取真实数据...")
        
        # 创建输出目录
        test_case.output_dir.mkdir(exist_ok=True)
        
        # 创建数据提取器实例
        extractor = SECFinancialExtractor()
        
        # 确定输出目录（使用测试输出目录）
        output_dir = str(test_case.output_dir)
        
        # 调用真实数据提取，传递年份范围参数
        result = extractor.fetch_financial_data(
            ticker=test_case.ticker,
            year=test_case.year,
            quarter=test_case.quarter,
            start_year=test_case.start_year,
            end_year=test_case.end_year,
            output_dir=output_dir
        )
        
        safe_print(f"[INFO] 数据提取完成: {result.get('company_name', '')}")
        
        # SEC模块输出的文件名格式与测试期望的不同，需要重命名
        # 例如: GOOG_2025_Balance_Sheet.csv -> Balance_Sheet.csv
        self._rename_extracted_files(test_case, result.get('exported_files', {}))
        
        return result
    
    def _rename_extracted_files(self, test_case: TestCase, exported_files: Dict[str, str]):
        """重命名提取的文件以匹配测试期望的文件名"""
        import shutil
        import os
        
        # 映射关系: SEC模块输出文件名 -> 测试期望文件名
        file_mapping = {}
        
        for sec_filename, filepath in exported_files.items():
            # 提取文件类型
            if 'balance_sheet' in sec_filename.lower() or 'Balance' in sec_filename:
                expected_filename = "Balance_Sheet.csv"
            elif 'income_statement' in sec_filename.lower() or 'Income' in sec_filename:
                expected_filename = "Income_Statement.csv"
            elif 'cash_flow' in sec_filename.lower() or 'Cash' in sec_filename:
                expected_filename = "Cash_Flow.csv"
            else:
                # 未知文件类型，跳过
                continue
            
            # 构建源文件和目标文件路径
            source_path = Path(filepath)
            target_path = test_case.get_output_file_path(expected_filename)
            
            # 如果源文件存在，复制到目标位置
            if source_path.exists():
                shutil.copy2(source_path, target_path)
                safe_print(f"  重命名文件: {source_path.name} -> {expected_filename}")
                file_mapping[expected_filename] = str(target_path)
            else:
                safe_print(f"  警告: 提取的文件不存在: {source_path}")
        
        return file_mapping
    
    def _run_validations(self, test_case: TestCase) -> List[Dict[str, Any]]:
        """运行所有验证"""
        validation_results = []
        
        # 对每个预期文件运行验证
        for filename in test_case.expected_files:
            expected_file = test_case.get_expected_file_path(filename)
            output_file = test_case.get_output_file_path(filename)
            
            safe_print(f"\n验证文件: {filename}")
            safe_print(f"  基准文件: {expected_file}")
            safe_print(f"  输出文件: {output_file}")
            
            # 运行验证器（使用测试用例的自定义验证器，如果提供了的话）
            validators_to_use = test_case.custom_validators if test_case.custom_validators else DEFAULT_VALIDATORS
            
            for validator in validators_to_use:
                if validator == validate_csv_structure:
                    result = validator(output_file, TestConfig.REQUIRED_COLUMNS)
                elif validator == validate_row_count:
                    result = validator(output_file, expected_file)
                else:
                    result = validator(output_file)
                
                validation_results.append({
                    "validator": validator.__name__,
                    "file": filename,
                    "result": result,
                    "success": result.success,
                    "message": str(result)
                })
                
                status = "[PASS]" if result.success else "[FAIL]"
                safe_print(f"  {status} {validator.__name__}: {result.message}")
            
            # 运行关键指标验证（只在相关文件中验证相关指标）
            file_type = test_case.get_file_type(filename)
            
            # 根据文件类型确定应该验证哪些指标
            indicators_to_check = []
            for indicator in test_case.key_indicators:
                # 检查指标是否属于当前文件类型
                if file_type == "balance_sheet" and indicator in TestConfig.KEY_INDICATORS["balance_sheet"]:
                    indicators_to_check.append(indicator)
                elif file_type == "income_statement" and indicator in TestConfig.KEY_INDICATORS["income_statement"]:
                    indicators_to_check.append(indicator)
                elif file_type == "cash_flow" and indicator in TestConfig.KEY_INDICATORS["cash_flow"]:
                    indicators_to_check.append(indicator)
            
            # 验证相关指标
            for indicator_name in indicators_to_check:
                result = validate_key_indicator(output_file, expected_file, indicator_name)
                validation_results.append({
                    "validator": "validate_key_indicator",
                    "file": filename,
                    "indicator": indicator_name,
                    "result": result,
                    "success": result.success,
                    "message": str(result)
                })
                
                status = "[PASS]" if result.success else "[FAIL]"
                safe_print(f"  {status} 关键指标 {indicator_name}: {result.message}")
        
        return validation_results
    
    def run_all_tests(self, specific_case: Optional[str] = None) -> bool:
        """运行所有测试"""
        self.start_time = time.time()
        
        # 发现测试用例
        self.test_cases = self.discover_test_cases()
        
        if not self.test_cases:
            safe_print("未发现任何测试用例")
            return False
        
        safe_print(f"发现 {len(self.test_cases)} 个测试用例")
        
        # 运行测试
        all_success = True
        
        for test_case in self.test_cases:
            if test_case.skip:
                safe_print(f"\n跳过测试用例: {test_case.name} (标记为跳过)")
                continue
            
            if specific_case and test_case.name != specific_case:
                continue
            
            result = self.run_test_case(test_case)
            self.results[test_case.name] = result
            
            if not result["success"]:
                all_success = False
        
        self.end_time = time.time()
        
        # 生成报告
        self._generate_report()
        
        return all_success
    
    def _generate_report(self):
        """生成测试报告"""
        if not self.results:
            return
        
        total_cases = len(self.results)
        passed_cases = sum(1 for r in self.results.values() if r["success"])
        failed_cases = total_cases - passed_cases
        
        safe_print(f"\n{'='*60}")
        safe_print("SEC财务数据回归测试报告")
        safe_print(f"{'='*60}")
        safe_print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        safe_print(f"总耗时: {self.end_time - self.start_time:.2f}秒")
        safe_print(f"测试用例总数: {total_cases}")
        safe_print(f"通过: {passed_cases}")
        safe_print(f"失败: {failed_cases}")
        safe_print(f"通过率: {passed_cases/total_cases*100:.1f}%")
        safe_print(f"{'='*60}")
        
        # 详细结果
        for test_name, result in self.results.items():
            status = "[PASS] 通过" if result["success"] else "[FAIL] 失败"
            safe_print(f"\n{test_name}: {status}")
            safe_print(f"  描述: {result['test_case'].description}")
            safe_print(f"  耗时: {result['duration']:.2f}秒")
            safe_print(f"  结果: {result['message']}")
            
            if not result["success"] and self.verbose:
                for validation in result["validations"]:
                    if not validation["success"]:
                        safe_print(f"    [ERR] {validation['validator']}: {validation['message']}")
        
        safe_print(f"\n{'='*60}")
        
        if failed_cases == 0:
            safe_print("[CELE] 所有测试用例通过！")
        else:
            safe_print(f"[WARN] {failed_cases} 个测试用例失败，请检查上述错误信息")
        
        # 生成HTML报告（如果启用）
        if self.generate_report:
            self._generate_html_report()
    
    def _generate_html_report(self):
        """生成HTML格式的详细报告"""
        try:
            report_file = OUTPUT_DIR / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            
            html_content = self._create_html_report_content()
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            safe_print(f"\n[CHART] HTML测试报告已生成: {report_file}")
            
        except Exception as e:
            safe_print(f"生成HTML报告失败: {e}")
    
    def _create_html_report_content(self) -> str:
        """创建HTML报告内容"""
        total_cases = len(self.results)
        passed_cases = sum(1 for r in self.results.values() if r["success"])
        failed_cases = total_cases - passed_cases
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEC财务数据回归测试报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        .summary {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
        .stat-box {{ text-align: center; padding: 15px; border-radius: 5px; }}
        .passed {{ background: #d4edda; color: #155724; }}
        .failed {{ background: #f8d7da; color: #721c24; }}
        .total {{ background: #d1ecf1; color: #0c5460; }}
        .test-case {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
        .test-passed {{ border-left: 5px solid #28a745; }}
        .test-failed {{ border-left: 5px solid #dc3545; }}
        .validation {{ margin: 5px 0; padding: 5px; }}
        .validation-passed {{ color: #28a745; }}
        .validation-failed {{ color: #dc3545; }}
        .timestamp {{ color: #6c757d; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 SEC财务数据回归测试报告</h1>
        
        <div class="summary">
            <p><strong>测试时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>总耗时:</strong> {self.end_time - self.start_time:.2f}秒</p>
        </div>
        
        <div class="stats">
            <div class="stat-box total">
                <h3>总测试用例</h3>
                <p style="font-size: 2em;">{total_cases}</p>
            </div>
            <div class="stat-box passed">
                <h3>通过</h3>
                <p style="font-size: 2em;">{passed_cases}</p>
            </div>
            <div class="stat-box failed">
                <h3>失败</h3>
                <p style="font-size: 2em;">{failed_cases}</p>
            </div>
        </div>
        
        <h2>测试用例详情</h2>
"""
        
        for test_name, result in self.results.items():
            status_class = "test-passed" if result["success"] else "test-failed"
            status_icon = "✅" if result["success"] else "❌"
            
            html += f"""
        <div class="test-case {status_class}">
            <h3>{status_icon} {test_name}</h3>
            <p><strong>描述:</strong> {result['test_case'].description}</p>
            <p><strong>状态:</strong> {"通过" if result["success"] else "失败"}</p>
            <p><strong>耗时:</strong> {result['duration']:.2f}秒</p>
            <p><strong>结果:</strong> {result['message']}</p>
            
            <h4>验证详情:</h4>
"""
            
            for validation in result["validations"]:
                validation_class = "validation-passed" if validation["success"] else "validation-failed"
                validation_icon = "✓" if validation["success"] else "✗"
                
                html += f"""
            <div class="validation {validation_class}">
                {validation_icon} {validation['validator']}: {validation['message']}
            </div>
"""
            
            html += """
        </div>
"""
        
        html += """
    </div>
</body>
</html>
"""
        
        return html


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="SEC财务数据回归测试运行器")
    parser.add_argument("--test-case", type=str, help="运行特定测试用例")
    parser.add_argument("--all", action="store_true", help="运行所有测试用例")
    parser.add_argument("--verbose", action="store_true", help="显示详细输出")
    parser.add_argument("--generate-report", action="store_true", help="生成HTML报告")
    
    args = parser.parse_args()
    
    # 验证参数
    if not args.all and not args.test_case:
        parser.error("必须指定 --all 或 --test-case 参数")
    
    # 创建测试运行器
    runner = TestRunner(verbose=args.verbose, generate_report=args.generate_report)
    
    # 运行测试
    if args.all:
        success = runner.run_all_tests()
    else:
        success = runner.run_all_tests(specific_case=args.test_case)
    
    # 返回退出码
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
   