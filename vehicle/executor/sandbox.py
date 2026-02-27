"""
代码沙箱 - 安全执行用户生成的Python代码

使用RestrictedPython限制危险操作
"""

import logging
import sys
import os
import signal
import time
import threading
from typing import Any, Dict, Optional, Callable
from RestrictedPython import compile_restricted
from RestrictedPython.Guards import (safe_builtins, guarded_iter_unpack_sequence,
                                     guarded_unpack_sequence, safer_getattr)
from RestrictedPython.PrintCollector import PrintCollector

# 配置日志
logger = logging.getLogger(__name__)


# 超时异常
class TimeoutError(Exception):
    """代码执行超时"""
    pass


# 执行中断异常
class ExecutionInterrupted(Exception):
    """代码执行被中断"""
    pass


# 允许的内置函数
ALLOWED_BUILTINS = {
    # 基础类型和函数
    'abs': abs,
    'all': all,
    'any': any,
    'bool': bool,
    'dict': dict,
    'enumerate': enumerate,
    'filter': filter,
    'float': float,
    'int': int,
    'isinstance': isinstance,
    'issubclass': issubclass,
    'len': len,
    'list': list,
    'map': map,
    'max': max,
    'min': min,
    'pow': pow,
    'range': range,
    'reversed': reversed,
    'round': round,
    'sorted': sorted,
    'str': str,
    'sum': sum,
    'tuple': tuple,
    'zip': zip,
    'print': print,  # 允许print用于调试
    'None': None,
    'True': True,
    'False': False,
    'NotImplemented': NotImplemented,
    'Ellipsis': Ellipsis,
    '__debug__': __debug__,
}


class SandboxGlobals:
    """沙箱全局变量管理器"""

    def __init__(self, hal_module=None, on_print: Optional[Callable] = None):
        """初始化沙箱全局变量

        Args:
            hal_module: 硬件抽象层模块
            on_print: print回调函数（可选）
        """
        self._globals = {
            '__builtins__': ALLOWED_BUILTINS.copy(),
            '__name__': '__main__',
            # RestrictedPython需要的安全函数
            '_getattr_': safer_getattr,
            '_getiter_': iter,
            '_iter_unpack_sequence_': guarded_iter_unpack_sequence,
            '_unpack_sequence_': guarded_unpack_sequence,
        }

        # 注入HAL模块
        if hal_module is not None:
            self._import_hal_functions(hal_module)

        # 自定义print函数（用于 RestrictedPython 的 _print_）
        if on_print:
            self._globals['_print_'] = on_print
            self._globals['print'] = on_print

        # 时间和睡眠函数（受限）
        self._globals['time'] = type('Time', (), {
            'sleep': lambda x: None if x > 5 else time.sleep(min(x, 5)),  # 最多sleep 5秒
        })()

    def _import_hal_functions(self, hal_module):
        """导入HAL模块的函数到沙箱"""
        # 运动控制函数
        motion_funcs = [
            'qianjin', 'houtui', 'zuopingyi', 'youpingyi',
            'xuanzhuan', 'fxuanzhuan', 'tingzhi',
            'xiaozuozhuan', 'xiaoyouzhuan',  # 新增：左右转弯
            'dengdai',  # 新增：等待函数
            'yidong_angle', 'yidong_xy',
            'set_servo', 'reset_servos'
        ]

        # 传感器函数
        sensor_funcs = [
            'heshengbo', 'heshengbo_juli',
            'xunxian', 'xunxian_zhong', 'xunxian_zuo', 'xunxian_you',
            'dianchi'
        ]

        # 云台控制函数（按设计文档命名）
        gimbal_funcs = [
            'shang', 'xia', 'zuo', 'you', 'fuwei',
            'yuntai_shang', 'yuntai_xia', 'yuntai_zuo', 'yuntai_you', 'yuntai_fuwei'
        ]

        # 视觉函数
        vision_funcs = [
            'shibieyanse'
        ]

        # 导入函数
        for func_name in motion_funcs + sensor_funcs + gimbal_funcs + vision_funcs:
            if hasattr(hal_module, func_name):
                self._globals[func_name] = getattr(hal_module, func_name)

        # 添加方便的别名
        self._globals['停止'] = self._globals.get('tingzhi')
        self._globals['前进'] = self._globals.get('qianjin')
        self._globals['后退'] = self._globals.get('houtui')

        # 导入 random 和 math 模块（用于 Blockly 内置积木）
        import random
        import math
        self._globals['random'] = random
        self._globals['math'] = math

        # 导入 threading 模块（用于并发积木）
        import threading
        self._globals['threading'] = threading

    def get_globals(self) -> Dict[str, Any]:
        """获取全局变量字典"""
        return self._globals.copy()


class CodeSandbox:
    """代码沙箱执行器"""

    def __init__(self, hal_module=None, timeout: int = 30):
        """初始化代码沙箱

        Args:
            hal_module: 硬件抽象层模块
            timeout: 默认执行超时时间（秒）
        """
        self.hal_module = hal_module
        self.timeout = timeout
        self._executing = False
        self._interrupted = False
        self._print_output = []

        # 创建沙箱全局变量（不传on_print，稍后手动设置_print_）
        self.sandbox_globals = SandboxGlobals(hal_module=hal_module, on_print=None)

        # 设置安全的print函数
        self._setup_print_function()

    def _setup_print_function(self):
        """设置print函数"""
        # 使用PrintCollector作为基础，并扩展以支持日志记录
        from RestrictedPython.PrintCollector import PrintCollector

        class _PrintCollectorWithLog(PrintCollector):
            """带日志记录的PrintCollector"""
            def __init__(self, outer_self):
                super().__init__()
                self.outer_self = outer_self

            def _getattr(self, name):
                """RestrictedPython需要此方法"""
                # 返回自己，这样后续的_call_print可以正常工作
                return self

            def _call_print(self, *objects, **kwargs):
                """捕获print输出"""
                result = super()._call_print(*objects, **kwargs)
                # 同时记录到日志
                output = ' '.join(str(obj) for obj in objects)
                logger.info(f"[代码输出] {output}")
                return result

        _print_obj = _PrintCollectorWithLog(self)
        self._print_collector = _print_obj

        # 存储到全局变量
        self.sandbox_globals._globals['_print_'] = _print_obj
        self.sandbox_globals._globals['print'] = _print_obj

    def compile_code(self, code: str) -> Optional[object]:
        """编译代码

        Args:
            code: Python代码字符串

        Returns:
            编译后的代码对象，失败返回None
        """
        try:
            # 使用RestrictedPython编译代码
            # RestrictedPython 7.0+ 返回code对象或抛出异常
            code_obj = compile_restricted(
                code,
                filename='<user_code>',
                mode='exec'
            )
            return code_obj
        except SyntaxError as e:
            logger.error(f"代码语法错误: {e}")
            return None
        except Exception as e:
            logger.error(f"代码编译异常: {e}")
            return None

    def execute(self, code: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """执行代码

        Args:
            code: Python代码字符串
            timeout: 超时时间（秒），None使用默认值

        Returns:
            执行结果字典:
            {
                'success': bool,  # 是否成功
                'error': str,     # 错误信息（如果有）
                'output': list,   # print输出
            }
        """
        if self._executing:
            return {
                'success': False,
                'error': '已有代码正在执行',
                'output': []
            }

        # 编译代码
        code_obj = self.compile_code(code)
        if code_obj is None:
            return {
                'success': False,
                'error': '代码编译失败',
                'output': []
            }

        # 重置状态
        self._executing = True
        self._interrupted = False
        if self._print_collector:
            self._print_collector.txt = []  # 清空之前的输出

        # 执行超时
        exec_timeout = timeout if timeout is not None else self.timeout

        # 在新线程中执行
        result = {'success': False, 'error': None, 'output': []}
        exception = [None]  # 使用列表在线程间传递异常

        def exec_thread():
            try:
                exec_globals = self.sandbox_globals.get_globals()
                exec(code_obj, exec_globals)
                result['success'] = True
            except Exception as e:
                exception[0] = e
                result['error'] = str(e)

        thread = threading.Thread(target=exec_thread)
        thread.daemon = True
        thread.start()

        # 等待执行完成或超时
        thread.join(timeout=exec_timeout)

        if thread.is_alive():
            # 超时，无法强制终止Python线程
            # 标记为中断状态，下次HAL调用时会检查
            self._interrupted = True
            result['success'] = False
            result['error'] = f'执行超时（{exec_timeout}秒）'
            logger.warning(f"代码执行超时: {exec_timeout}秒")
        elif exception[0]:
            # 执行异常
            result['success'] = False
            result['error'] = f'执行错误: {str(exception[0])}'
            logger.error(f"代码执行错误: {exception[0]}")

        # 从PrintCollector获取输出
        if self._print_collector:
            result['output'] = self._print_collector.txt.copy()
        else:
            result['output'] = []

        self._executing = False

        return result

    def is_executing(self) -> bool:
        """检查是否正在执行代码"""
        return self._executing

    def interrupt(self):
        """中断当前执行"""
        if self._executing:
            self._interrupted = True
            logger.info("代码执行被中断")
            # 发送停止命令
            if self.hal_module and hasattr(self.hal_module, 'motion_controller'):
                self.hal_module.motion_controller.tingzhi()

    def reset(self):
        """重置沙箱状态"""
        self._executing = False
        self._interrupted = False
        self._print_output = []


class ProcessManager:
    """进程管理器 - 管理代码执行的进程"""

    def __init__(self, hal_module=None):
        """初始化进程管理器

        Args:
            hal_module: 硬件抽象层模块
        """
        self.hal_module = hal_module
        self.sandbox = CodeSandbox(hal_module=hal_module)
        self.current_process_id = None
        self._stop_requested = False

    def start_execution(self, code: str, process_id: str = None, timeout: int = 30) -> Dict[str, Any]:
        """开始执行代码

        Args:
            code: Python代码字符串
            process_id: 进程ID（可选）
            timeout: 超时时间（秒）

        Returns:
            执行结果字典
        """
        if self.sandbox.is_executing():
            return {
                'success': False,
                'error': '已有代码正在执行，请先停止',
                'process_id': self.current_process_id
            }

        self._stop_requested = False
        self.current_process_id = process_id or f"exec_{int(time.time())}"

        logger.info(f"开始执行代码: process_id={self.current_process_id}")
        result = self.sandbox.execute(code, timeout=timeout)
        result['process_id'] = self.current_process_id

        if not self._stop_requested:
            # 执行完成（非用户停止）
            self.current_process_id = None

        return result

    def stop_execution(self):
        """停止当前执行"""
        if self.sandbox.is_executing():
            self._stop_requested = True
            self.sandbox.interrupt()
            logger.info(f"停止执行: process_id={self.current_process_id}")
            self.current_process_id = None
            return True
        return False

    def emergency_stop(self):
        """紧急停止"""
        # 立即停止所有电机
        if self.hal_module and hasattr(self.hal_module, 'motion_controller'):
            self.hal_module.motion_controller.tingzhi()

        # 停止代码执行
        self.stop_execution()

        logger.warning("紧急停止已触发")

    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            'executing': self.sandbox.is_executing(),
            'process_id': self.current_process_id,
            'interrupted': self.sandbox._interrupted,
            'stop_requested': self._stop_requested
        }
