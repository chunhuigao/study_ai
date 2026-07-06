import json
import sys

from .rag import clear_index, ingest_pdf, list_documents, query


def _print(data):
    print(json.dumps(data, ensure_ascii=False))


def main():
    try:
        if "--rag-ingest-pdf" in sys.argv:
            file_path = sys.argv[sys.argv.index("--rag-ingest-pdf") + 1]
            _print(ingest_pdf(file_path))
            return

        if "--rag-query" in sys.argv:
            payload = json.loads(sys.stdin.read() or "{}")
            _print(query(payload.get("question", ""), payload.get("topK", 4)))
            return

        if "--rag-documents" in sys.argv:
            _print(list_documents())
            return

        if "--rag-clear" in sys.argv:
            _print(clear_index())
            return

        _print({"ok": False, "error": "未知命令"})
    except Exception as error:
        _print({"ok": False, "error": str(error)})


if __name__ == "__main__":
    main()

