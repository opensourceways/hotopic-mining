# 项目根目录下或 tests 目录下创建 conftest.py
# conftest.py

# 这个全局变量将用于在测试模块中访问命令行选项的状态
# 这种方式比直接在每个 skipif 中尝试访问 config 对象要简单
_run_specific_skips = False

def pytest_addoption(parser):
    parser.addoption(
        "--run-specific-skips",  # 你建议的 --run-skip，或者更明确的名称
        action="store_true",
        default=False,
        help="Run tests that are normally skipped by a specific conditional logic"
    )

def pytest_configure(config):
    """
    pytest_configure 钩子在命令行选项被解析后，测试会话开始前被调用。
    我们在这里读取我们自定义选项的值，并存储起来。
    """
    global _run_specific_skips
    _run_specific_skips = config.getoption("--run-specific-skips")

# 提供一个辅助函数，让测试用例可以方便地使用这个逻辑
# 这个函数将决定是否真的要跳过
def should_skip_unless_run_flag(original_skip_condition):
    """
    如果 --run-specific-skips 标志被设置，则不跳过 (返回 False)。
    否则，根据 original_skip_condition 决定是否跳过。

    返回 True 表示应该跳过，False 表示不应该跳过。
    """
    if _run_specific_skips:
        return False  # 如果标志存在，则强制运行 (不跳过)
    return original_skip_condition # 否则，按原始条件判断
