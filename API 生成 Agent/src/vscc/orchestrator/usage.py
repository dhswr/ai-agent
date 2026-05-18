"""Claude 会话用量监控 —— 对接 Anthropic API 用量查询."""


def get_session_usage_pct() -> int:
    """查询当前会话用量百分比。MVP 阶段返回 0 (跳过限制)."""
    # 完整实现需要对接 Claude Code 的 /usage 命令
    # 当前版本中用量监控由 Ralph Loop bash 脚本处理
    return 0
