import { useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const initialMessages = [
  {
    role: 'assistant',
    content: '你好，我是一个最简 Electron Agent。可以连续对话，也可以按需要调用计算器和当前时间工具。'
  }
];

function MessageBubble({ message }) {
  const isUser = message.role === 'user';

  return (
    <article className={`message ${isUser ? 'message-user' : 'message-assistant'}`}>
      <div className="message-role">{isUser ? '你' : 'Agent'}</div>
      <div className="message-content">{message.content}</div>
    </article>
  );
}

function TracePanel({ trace }) {
  if (!trace.length) {
    return (
      <aside className="trace-panel">
        <div className="panel-title">执行轨迹</div>
        <p className="empty-text">发送问题后，这里会显示模型的 Thought、Action 和 Observation。</p>
      </aside>
    );
  }

  return (
    <aside className="trace-panel">
      <div className="panel-title">执行轨迹</div>
      <div className="trace-list">
        {trace.map((item) => (
          <details className="trace-item" key={item.step} open={item.step === trace.length}>
            <summary>
              <span>Step {item.step}</span>
              <strong>{item.type}</strong>
            </summary>
            {item.tool ? (
              <div className="trace-meta">
                {item.tool}({item.toolInput || '空'})
              </div>
            ) : null}
            {item.observation ? <div className="observation">{item.observation}</div> : null}
            <pre>{item.modelOutput}</pre>
          </details>
        ))}
      </div>
    </aside>
  );
}

function App() {
  const [messages, setMessages] = useState(initialMessages);
  const [input, setInput] = useState('');
  const [trace, setTrace] = useState([]);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState('');

  const chatMessages = useMemo(
    () => messages.filter((message) => message.role === 'user' || message.role === 'assistant'),
    [messages]
  );

  async function sendMessage(event) {
    event.preventDefault();
    const text = input.trim();
    if (!text || isSending) {
      return;
    }

    setError('');
    setInput('');
    setIsSending(true);

    const nextMessages = [...chatMessages, { role: 'user', content: text }];
    setMessages(nextMessages);

    try {
      const result = await window.agentApi.chat({
        messages: nextMessages,
        maxSteps: 10
      });

      setTrace(result.trace ?? []);

      if (!result.ok) {
        throw new Error(result.error || 'Agent 调用失败');
      }

      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content: result.answer || '没有获得有效回答。'
        }
      ]);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content: `调用失败：${message}`
        }
      ]);
    } finally {
      setIsSending(false);
    }
  }

  function resetChat() {
    setMessages(initialMessages);
    setTrace([]);
    setError('');
    setInput('');
  }

  return (
    <main className="app-shell">
      <section className="chat-area">
        <header className="topbar">
          <div>
            <h1>Electron Agent</h1>
            <p>React 前端 + Electron 主进程 + Python ReAct Agent</p>
          </div>
          <button type="button" className="secondary-button" onClick={resetChat}>
            清空
          </button>
        </header>

        <div className="messages" aria-live="polite">
          {messages.map((message, index) => (
            <MessageBubble message={message} key={`${message.role}-${index}`} />
          ))}
          {isSending ? (
            <article className="message message-assistant">
              <div className="message-role">Agent</div>
              <div className="message-content muted">正在思考...</div>
            </article>
          ) : null}
        </div>

        {error ? <div className="error-banner">{error}</div> : null}

        <form className="composer" onSubmit={sendMessage}>
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                sendMessage(event);
              }
            }}
            placeholder="输入问题，例如：现在几点？或者 23 * (17 + 5) 等于多少？"
            rows={3}
          />
          <button type="submit" disabled={isSending || !input.trim()}>
            {isSending ? '发送中' : '发送'}
          </button>
        </form>
      </section>

      <TracePanel trace={trace} />
    </main>
  );
}

createRoot(document.getElementById('root')).render(<App />);
