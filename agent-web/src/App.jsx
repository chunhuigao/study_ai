import { useCallback, useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { ConfigProvider, Layout, Alert, Typography, theme } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import './styles.css';

import ChatHeader from './components/ChatHeader';
import MessageList from './components/MessageList';
import Composer from './components/Composer';
import TracePanel from './components/TracePanel';

const { Content, Sider } = Layout;
const { Text } = Typography;

let nextMsgId = 1;
function createMessage(role, content) {
  return { id: nextMsgId++, role, content };
}

const initialMessages = [
  createMessage(
    'assistant',
    '你好，我是一个最简 Electron Agent。可以连续对话，也可以按需要调用计算器和当前时间工具。',
  ),
];

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

  const inputRef = useRef('');
  const sendingRef = useRef(false);
  const messagesRef = useRef(initialMessages);

  inputRef.current = input;
  sendingRef.current = isSending;

  const updateMessages = useCallback((updater) => {
    setMessages((prev) => {
      const next = typeof updater === 'function' ? updater(prev) : updater;
      messagesRef.current = next;
      return next;
    });
  }, []);

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

  const sendMessage = useCallback(async () => {
    const text = inputRef.current.trim();
    if (!text || sendingRef.current) {
      return;
    }

    setError('');
    setInput('');
    setIsSending(true);

    const userMsg = createMessage('user', text);
    updateMessages((prev) => [...prev, userMsg]);

    try {
      const chatHistory = messagesRef.current
        .filter((m) => m.role === 'user' || m.role === 'assistant')
        .map(({ role, content }) => ({ role, content }));
      chatHistory.push({ role: 'user', content: text });

      const result = await window.agentApi.chat({
        messages: chatHistory,
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

      updateMessages((prev) => [
        ...prev,
        createMessage('assistant', result.answer || '没有获得有效回答。'),
      ]);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
      updateMessages((prev) => [
        ...prev,
        createMessage('assistant', `调用失败：${message}`),
      ]);
    } finally {
      setIsSending(false);
    }
  }, [updateMessages]);

  const resetChat = useCallback(() => {
    setMessages(initialMessages);
    messagesRef.current = initialMessages;
    setTrace([]);
    setTotalUsage(null);
    setError('');
    setInput('');
  }, []);

  const handleSwitchModel = useCallback(
    async (modelId) => {
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
    },
    [currentModel],
  );

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: '#1f5f6b',
          borderRadius: 8,
          fontFamily:
            '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        },
      }}
    >
      <Layout className="app-shell">
        <Layout className="chat-layout">
          <ChatHeader
            currentModel={currentModel}
            availableModels={availableModels}
            isSending={isSending}
            totalUsage={totalUsage}
            cumulativeUsage={cumulativeUsage}
            onSwitchModel={handleSwitchModel}
            onReset={resetChat}
          />

          <Content className="chat-content">
            <MessageList messages={messages} isSending={isSending} />

            {error ? (
              <Alert
                message={error}
                type="error"
                showIcon
                closable
                onClose={() => setError('')}
                style={{ margin: '0 16px 8px' }}
              />
            ) : null}

            <Composer
              input={input}
              isSending={isSending}
              onInputChange={setInput}
              onSend={sendMessage}
            />
          </Content>
        </Layout>

        <Sider width={380} className="trace-sider" theme="light">
          <div className="trace-sider-header">
            <Text strong style={{ fontSize: 15 }}>
              执行轨迹
            </Text>
          </div>
          <div className="trace-sider-body">
            <TracePanel trace={trace} />
          </div>
        </Sider>
      </Layout>
    </ConfigProvider>
  );
}

createRoot(document.getElementById('root')).render(<App />);
