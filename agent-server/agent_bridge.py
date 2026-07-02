import contextlib
import io
import json
import logging
import os
import sys
from datetime import datetime

from zhipu_agent import run_agent_with_history

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")


class HourlyFileHandler(logging.FileHandler):
    def __init__(self, log_dir, prefix="agent", mode="a", encoding="utf-8"):
        self.log_dir = log_dir
        self.prefix = prefix
        self._current_hour = None
        os.makedirs(log_dir, exist_ok=True)
        self._current_hour = datetime.now().strftime("%Y%m%d_%H")
        filename = os.path.join(
            self.log_dir, f"{self.prefix}_{self._current_hour}.log"
        )
        super().__init__(filename, mode=mode, encoding=encoding)

    def emit(self, record):
        now_hour = datetime.now().strftime("%Y%m%d_%H")
        if now_hour != self._current_hour:
            self._current_hour = now_hour
            self.close()
            self.baseFilename = os.path.join(
                self.log_dir, f"{self.prefix}_{now_hour}.log"
            )
            self.stream = self._open()
        super().emit(record)


def _setup_logging():
    logger = logging.getLogger("agent")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = HourlyFileHandler(LOG_DIR, prefix="agent", mode="a")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


_setup_logging()
logger = logging.getLogger("agent")


def main():
    try:
        raw_input = sys.stdin.read() or "{}"
        logger.info("========== 收到前端请求 ==========")
        logger.debug("原始输入: %s", raw_input)

        payload = json.loads(raw_input)
        raw_messages = payload.get("messages", [])
        max_steps = payload.get("maxSteps", 10)
        if not isinstance(max_steps, int) or max_steps < 1:
            max_steps = 10

        logger.info("消息条数: %d, 最大步数: %d", len(raw_messages), max_steps)
        for idx, msg in enumerate(raw_messages):
            logger.info(
                "  消息[%d] role=%s content=%s",
                idx,
                msg.get("role"),
                msg.get("content", "")[:200],
            )

        with contextlib.redirect_stdout(io.StringIO()):
            result = run_agent_with_history(raw_messages, max_steps=max_steps)

        logger.info("========== 返回前端结果 ==========")
        logger.info(
            "ok=%s, answer=%s, trace步数=%d",
            result.get("ok"),
            result.get("answer", "")[:200],
            len(result.get("trace", [])),
        )
        logger.debug(
            "完整返回: %s", json.dumps(result, ensure_ascii=False)[:2000]
        )

        print(json.dumps(result, ensure_ascii=False))
    except Exception as error:
        logger.exception("处理请求异常: %s", error)
        print(
            json.dumps(
                {"ok": False, "error": str(error), "answer": "", "trace": []},
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()