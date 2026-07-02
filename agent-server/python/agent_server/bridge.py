import contextlib
import io
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from .zhipu_agent import run_agent_with_history
from .model_config import get_available_models, load_config, switch_model

SERVER_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = SERVER_DIR / "var" / "logs"
TOKEN_USAGE_FILE = SERVER_DIR / "var" / "token_usage.json"


class HourlyFileHandler(logging.FileHandler):
    def __init__(self, log_dir, prefix="agent", mode="a", encoding="utf-8"):
        self.log_dir = str(log_dir)
        self.prefix = prefix
        self._current_hour = None
        os.makedirs(self.log_dir, exist_ok=True)
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


def load_token_usage():
    if TOKEN_USAGE_FILE.exists():
        try:
            return json.loads(TOKEN_USAGE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "request_count": 0}


def save_token_usage(usage_data):
    TOKEN_USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_USAGE_FILE.write_text(
        json.dumps(usage_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def accumulate_token_usage(session_usage):
    cumulative = load_token_usage()
    cumulative["prompt_tokens"] += session_usage.get("prompt_tokens", 0)
    cumulative["completion_tokens"] += session_usage.get("completion_tokens", 0)
    cumulative["total_tokens"] += session_usage.get("total_tokens", 0)
    cumulative["request_count"] = cumulative.get("request_count", 0) + 1
    cumulative["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_token_usage(cumulative)
    return cumulative


def main():
    if "--get-token-usage" in sys.argv:
        cumulative = load_token_usage()
        print(json.dumps(cumulative, ensure_ascii=False))
        return

    if "--get-models" in sys.argv:
        current = load_config()
        models = get_available_models()
        result = {
            "current": current.get("model", ""),
            "models": models,
        }
        print(json.dumps(result, ensure_ascii=False))
        return

    if "--switch-model" in sys.argv:
        model_id = ""
        for i, arg in enumerate(sys.argv):
            if arg == "--switch-model" and i + 1 < len(sys.argv):
                model_id = sys.argv[i + 1]
                break
        if not model_id:
            print(json.dumps({"ok": False, "error": "请指定模型ID"}, ensure_ascii=False))
            return
        success, message = switch_model(model_id)
        current = load_config()
        print(json.dumps({
            "ok": success,
            "message": message,
            "current": current.get("model", ""),
        }, ensure_ascii=False))
        return

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

        session_usage = result.get("totalUsage")
        if session_usage:
            cumulative = accumulate_token_usage(session_usage)
            result["cumulativeUsage"] = cumulative
            logger.info(
                "累计Token用量: prompt=%d, completion=%d, total=%d, 请求次数=%d",
                cumulative["prompt_tokens"],
                cumulative["completion_tokens"],
                cumulative["total_tokens"],
                cumulative["request_count"],
            )

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