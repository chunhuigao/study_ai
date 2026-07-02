import { useEffect, useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const initialMessages = [
  {
    role: 'assistant',
    content:
      '你好，我是一个最简 Electron Agent。可以连续对话，也可以按需要调用计算器和当前时间工具。',
  },
];

function MessageBubble({ message }) {
  const isUser = message.role === 'user';

  return (
    <article
      className={`message ${isUser ? 'message-user' : 'message-assistant'}`}
    >
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
        <p className="empty-text">
          发送问题后，这里会显示模型的 Thought、Action 和 Observation。
        </p>
      </aside>
    );
  }

  return (
    <aside className="trace-panel">
      <div className="panel-title">执行轨迹</div>
      <div className="trace-list">
        {trace.map((item) => (
          <details
            className="trace-item"
            key={item.step}
            open={item.step === trace.length}
          >
            <summary>
              <span>Step {item.step}</span>
              <strong>{item.type}</strong>
            </summary>
            {item.tool ? (
              <div className="trace-meta">
                {item.tool}({item.toolInput || '空'})
              </div>
            ) : null}
            {item.observation ? (
              <div className="observation">{item.observation}</div>
            ) : null}
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
  const [totalUsage, setTotalUsage] = useState(null);
  const [cumulativeUsage, setCumulativeUsage] = useState(null);
  const [currentModel, setCurrentModel] = useState('');
  const [availableModels, setAvailableModels] = useState([]);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSending]);

  useEffect(() => {
    if (window.agentApi?.getTokenUsage) {
      window.agentApi
        .getTokenUsage()
        .then((data) => {
          if (data && data.total_tokens > 0) {
            setCumulativeUsage(data);
          }
        })
        .catch(() => {});
    }

    if (window.agentApi?.getModels) {
      window.agentApi
        .getModels()
        .then((data) => {
          if (data) {
            setCurrentModel(data.current || '');
            setAvailableModels(data.models || []);
          }
        })
        .catch(() => {});
    }
  }, []);

  const chatMessages = useMemo(
    () =>
      messages.filter(
        (message) => message.role === 'user' || message.role === 'assistant',
      ),
    [messages],
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
        maxSteps: 10,
      });

      setTrace(result.trace ?? []);
      setTotalUsage(result.totalUsage ?? null);

      if (result.cumulativeUsage) {
        setCumulativeUsage(result.cumulativeUsage);
      }

      if (!result.ok) {
        throw new Error(result.error || 'Agent 调用失败');
      }

      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content: result.answer || '没有获得有效回答。',
        },
      ]);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content: `调用失败：${message}`,
        },
      ]);
    } finally {
      setIsSending(false);
    }
  }

  function resetChat() {
    setMessages(initialMessages);
    setTrace([]);
    setTotalUsage(null);
    setError('');
    setInput('');
  }

  async function handleSwitchModel(event) {
    const modelId = event.target.value;
    if (!modelId || modelId === currentModel) {
      return;
    }

    try {
      const result = await window.agentApi.switchModel(modelId);
      if (result.ok) {
        setCurrentModel(modelId);
      } else {
        setError(result.message || '切换模型失败');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '切换模型失败');
    }
  }

  return (
    <main className="app-shell">
      <section className="chat-area">
        <header className="topbar">
          <div>
            <h1>React 前端 + Electron 主进程 + Python ReAct Agent</h1>
            <div className="token-usage-group">
              {availableModels.length > 0 ? (
                <span className="model-selector-wrapper">
                  模型：
                  <select
                    className="model-selector"
                    value={currentModel}
                    onChange={handleSwitchModel}
                    disabled={isSending}
                  >
                    {availableModels.map((m) => (
                      <option key={m.id} value={m.id} title={m.description}>
                        {m.name}
                      </option>
                    ))}
                  </select>
                </span>
              ) : null}
              {totalUsage ? (
                <span className="token-usage">
                  本次 — 输入: {totalUsage.prompt_tokens} | 输出:{' '}
                  {totalUsage.completion_tokens} | 合计:{' '}
                  {totalUsage.total_tokens}
                </span>
              ) : null}
              {cumulativeUsage ? (
                <span className="token-usage token-usage-cumulative">
                  累计 — 输入: {cumulativeUsage.prompt_tokens} | 输出:{' '}
                  {cumulativeUsage.completion_tokens} | 合计:{' '}
                  {cumulativeUsage.total_tokens} | 请求:{' '}
                  {cumulativeUsage.request_count}次
                </span>
              ) : (
                <span className="token-usage">Token 用量：发送问题后显示</span>
              )}
            </div>
          </div>
          <button
            type="button"
            className="secondary-button"
            onClick={resetChat}
          >
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
          <div ref={messagesEndRef} />
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
