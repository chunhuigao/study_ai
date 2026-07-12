from dotenv import load_dotenv

from cc_switch_config import DEFAULT_SYSTEM_PROMPT, ai_message_to_text, create_chat_model


def main() -> None:
    load_dotenv()

    llm = create_chat_model()
    messages = [("system", DEFAULT_SYSTEM_PROMPT)]

    print("LangChain 简单聊天机器人已启动。输入 exit 或 quit 退出。")

    while True:
        user_input = input("\n你：").strip()
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            print("再见！")
            break

        messages.append(("human", user_input))
        response = llm.invoke(messages)
        messages.append(response)

        print(f"\n机器人：{ai_message_to_text(response)}")


if __name__ == "__main__":
    main()
