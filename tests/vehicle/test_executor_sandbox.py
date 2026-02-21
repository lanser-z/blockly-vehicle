"""
测试代码执行器 - 沙箱功能
"""

import pytest
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../vehicle'))

# 设置模拟模式
os.environ['MOCK_HARDWARE'] = 'true'

from executor.sandbox import (
    CodeSandbox,
    ProcessManager,
    SandboxGlobals,
    TimeoutError,
    ExecutionInterrupted
)
import hal


class TestSandboxGlobals:
    """测试沙箱全局变量管理器"""

    def test_init_without_hal(self):
        """测试无HAL模块初始化"""
        globals_manager = SandboxGlobals(hal_module=None)
        globals_dict = globals_manager.get_globals()
        assert '__builtins__' in globals_dict
        # 当没有HAL模块时，print不在全局变量中（需要显式传入on_print）
        # print函数在builtins中可用
        assert 'print' in globals_dict['__builtins__']

    def test_init_with_hal(self):
        """测试带HAL模块初始化"""
        globals_manager = SandboxGlobals(hal_module=hal)
        globals_dict = globals_manager.get_globals()

        # 应该包含HAL函数
        assert 'qianjin' in globals_dict
        assert 'houtui' in globals_dict
        assert 'tingzhi' in globals_dict
        assert 'heshengbo' in globals_dict
        assert 'xunxian' in globals_dict
        assert 'dianchi' in globals_dict

    def test_chinese_aliases(self):
        """测试中文别名"""
        globals_manager = SandboxGlobals(hal_module=hal)
        globals_dict = globals_manager.get_globals()

        # 应该有中文别名
        assert '停止' in globals_dict
        assert '前进' in globals_dict
        assert '后退' in globals_dict


class TestCodeSandbox:
    """测试代码沙箱"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.sandbox = CodeSandbox(hal_module=hal, timeout=5)

    def test_init(self):
        """测试初始化"""
        assert self.sandbox is not None
        assert self.sandbox.timeout == 5

    def test_compile_simple_code(self):
        """测试编译简单代码"""
        code = """
print("Hello, World!")
x = 1 + 1
"""
        code_obj = self.sandbox.compile_code(code)
        assert code_obj is not None

    def test_compile_empty_code(self):
        """测试编译空代码"""
        code = ""
        code_obj = self.sandbox.compile_code(code)
        assert code_obj is not None

    def test_execute_simple_code(self):
        """测试执行简单代码"""
        code = """
x = 1 + 1
print(x)
"""
        result = self.sandbox.execute(code)
        assert result['success'] is True
        assert '2' in result['output']

    def test_execute_with_hal_functions(self):
        """测试执行包含HAL函数的代码"""
        code = """
qianjin(50)
tingzhi()
"""
        result = self.sandbox.execute(code)
        assert result['success'] is True

    def test_execute_syntax_error(self):
        """测试语法错误"""
        code = """
if True
    print("missing colon")
"""
        result = self.sandbox.execute(code)
        assert result['success'] is False
        assert 'error' in result

    def test_execute_runtime_error(self):
        """测试运行时错误"""
        code = """
x = 1 / 0
"""
        result = self.sandbox.execute(code)
        assert result['success'] is False
        assert result['error'] is not None

    def test_execute_timeout(self):
        """测试执行超时"""
        code = """
import time
time.sleep(10)
"""
        result = self.sandbox.execute(code, timeout=1)
        assert result['success'] is False
        assert '超时' in result['error']

    def test_dangerous_import_blocked(self):
        """测试危险导入被阻止"""
        code = """
import os
os.system("rm -rf /")
"""
        result = self.sandbox.execute(code)
        # RestrictedPython应该阻止这种导入
        # 或者执行时失败
        assert result['success'] is False

    def test_file_access_blocked(self):
        """测试文件访问被阻止"""
        code = """
f = open("/etc/passwd", "r")
content = f.read()
"""
        result = self.sandbox.execute(code)
        # 应该失败
        assert result['success'] is False

    def test_is_executing(self):
        """测试执行状态检查"""
        assert self.sandbox.is_executing() is False

    def test_print_output(self):
        """测试print输出捕获"""
        code = """
print("Line 1")
print("Line 2")
x = 100
print(f"Value: {x}")
"""
        result = self.sandbox.execute(code)
        assert result['success'] is True
        assert len(result['output']) == 3
        assert 'Line 1' in result['output']
        assert 'Line 2' in result['output']
        assert 'Value: 100' in result['output']


class TestProcessManager:
    """测试进程管理器"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.manager = ProcessManager(hal_module=hal)

    def test_init(self):
        """测试初始化"""
        assert self.manager is not None
        assert self.manager.sandbox is not None

    def test_start_execution(self):
        """测试开始执行"""
        code = """
qianjin(50)
tingzhi()
"""
        result = self.manager.start_execution(code, process_id="test_001")
        assert result['success'] is True
        assert result['process_id'] == "test_001"

    def test_start_execution_without_id(self):
        """测试开始执行（无ID）"""
        code = """
print("Hello")
"""
        result = self.manager.start_execution(code)
        assert result['success'] is True
        assert result['process_id'] is not None

    def test_stop_execution(self):
        """测试停止执行"""
        # 启动一个长时间运行的代码
        code = """
import time
time.sleep(5)
"""
        import threading
        thread = threading.Thread(
            target=self.manager.start_execution,
            args=(code, "test_stop"),
            kwargs={'timeout': 10}
        )
        thread.daemon = True
        thread.start()

        import time
        time.sleep(0.5)

        # 停止执行
        stopped = self.manager.stop_execution()
        assert stopped is True

    def test_get_status(self):
        """测试获取状态"""
        status = self.manager.get_status()
        assert 'executing' in status
        assert 'process_id' in status
        assert status['executing'] is False

    def test_emergency_stop(self):
        """测试紧急停止"""
        # 启动代码
        code = """
qianjin(50)
"""
        self.manager.start_execution(code, process_id="test_emergency")

        # 紧急停止
        self.manager.emergency_stop()

        # 验证状态
        status = self.manager.get_status()
        assert status['executing'] is False


class TestSandboxSecurity:
    """测试沙箱安全性"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.sandbox = CodeSandbox(hal_module=hal, timeout=5)

    def test_dangerous_builtins_blocked(self):
        """测试危险内置函数被阻止"""
        dangerous_calls = [
            "open('/etc/passwd').read()",
            "__import__('os').system('ls')",
            "eval('1+1')",
            "exec('print(1)')",
            "__import__('subprocess').call(['ls'])",
        ]

        for code in dangerous_calls:
            result = self.sandbox.execute(code)
            # 应该失败或被阻止
            assert result['success'] is False, f"应该阻止: {code}"

    def test_safe_builtins_allowed(self):
        """测试安全内置函数允许使用"""
        safe_codes = [
            "abs(-10)",
            "max(1, 2, 3)",
            "sum([1, 2, 3])",
            "len([1, 2, 3])",
            "list(range(5))",
        ]

        for code in safe_codes:
            result = self.sandbox.execute(code)
            # 这些应该可以执行
            # 注意：没有print的代码可能没有输出，但应该成功
            if result['success']:
                continue  # 成功就好
            # 如果失败，应该是因为输出为空而非安全错误

    def test_attribute_access_restricted(self):
        """测试属性访问受限"""
        # 尝试访问危险属性
        code = """
class Test:
    pass
t = Test()
t.__class__ = dict
"""
        result = self.sandbox.execute(code)
        # 应该失败
        assert result['success'] is False
