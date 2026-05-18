"""完成信号检测."""

PROMISE_COMPLETE = "<promise>COMPLETE</promise>"
PROMISE_FAIL = "<promise>FAIL</promise>"


def detect_complete(text: str) -> bool:
    return PROMISE_COMPLETE in text


def detect_fail(text: str) -> bool:
    return PROMISE_FAIL in text
