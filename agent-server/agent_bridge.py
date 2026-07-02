import contextlib
import io
import json
import sys

from zhipu_agent import run_agent_with_history


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        raw_messages = payload.get("messages", [])
        max_steps = payload.get("maxSteps", 10)
        if not isinstance(max_steps, int) or max_steps < 1:
            max_steps = 10

        with contextlib.redirect_stdout(io.StringIO()):
            result = run_agent_with_history(raw_messages, max_steps=max_steps)

        print(json.dumps(result, ensure_ascii=False))
    except Exception as error:
        print(
            json.dumps(
                {"ok": False, "error": str(error), "answer": "", "trace": []},
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
