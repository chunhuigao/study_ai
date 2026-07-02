import { useEffect, useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  ConfigProvider,
  Layout,
  Typography,
  Input,
  Button,
  Select,
  Tag,
  Collapse,
  Space,
  Divider,
  Alert,
  Badge,
  Tooltip,
  theme,
} from 'antd';
import {
  SendOutlined,
  DeleteOutlined,
  RobotOutlined,
  UserOutlined,
  ThunderboltOutlined,
  LoadingOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import zhCN from 'antd/locale/zh_CN';
import './styles.css';

const { Header, Content, Sider } = Layout;
const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

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
    <div
      className={`chat-bubble ${isUser ? 'chat-bubble-user' : 'chat-bubble-assistant'}`}
    >
      <div className="chat-bubble-avatar">
        {isUser ? (
          <div className="avatar avatar-user">
            <UserOutlined />
          </div>
        ) : (
          <div className="avatar avatar-assistant">
            <RobotOutlined />
          </div>
        )}
      </div>
      <div className="chat-bubble-body">
        <div className="chat-bubble-name">{isUser ? '你' : 'Agent'}</div>
        <div className="chat-bubble-content">{message.content}</div>
      </div>
    </div>
  );
}

function TracePanel({ trace }) {
  if (!trace.length) {
    return (
      <div className="trace-empty">
        <InfoCircleOutlined
          style={{ fontSize: 32, color: '#bfbfbf', marginBottom: 12 }}
        />
        <Text type="secondary">
          发送问题后，这里会显示模型的 Thought、Action 和 Observation。
        </Text>
      </div>
    );
  }

  const items = trace.map((item) => ({
    key: String(item.step),
    label: (
      <Space>
        <Text strong>Step {item.step}</Text>
        <Tag
          color={
            item.type === 'final'
              ? 'green'
              : item.type === 'action'
                ? 'blue'
                : 'orange'
          }
        >
          {item.type}
        </Tag>
        {item.tool ? (
          <Text type="secondary" style={{ fontSize: 12 }}>
            {item.tool}({item.toolInput || '空'})
          </Text>
        ) : null}
      </Space>
    ),
    children: (
      <div className="trace-detail">
        {item.observation ? (
          <div className="trace-observation">
            <Text type="secondary" strong style={{ fontSize: 12 }}>
              Observation:
            </Text>
            <Paragraph
              style={{ margin: '4px 0 0', fontSize: 12, color: '#595959' }}
            >
              {item.observation}
            </Paragraph>
          </div>
        ) : null}
        <pre className="trace-pre">{item.modelOutput}</pre>
      </div>
    ),
  }));

  return (
    <Collapse
      items={items}
      defaultActiveKey={[String(trace.length)]}
      size="small"
      className="trace-collapse"
    />
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

  async function sendMessage() {
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

  async function handleSwitchModel(modelId) {
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

  const modelOptions = availableModels.map((m) => ({
    value: m.id,
    label: (
      <Space size={4}>
        <span>{m.name}</span>
        <Tooltip title={m.description}>
          <InfoCircleOutlined style={{ color: '#bfbfbf', fontSize: 11 }} />
        </Tooltip>
      </Space>
    ),
  }));

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
          <Header className="app-header">
            <div className="header-left">
              <div className="header-title-row">
                <ThunderboltOutlined
                  style={{ fontSize: 20, color: '#1f5f6b', marginRight: 8 }}
                />
                <Title level={4} style={{ margin: 0 }}>
                  Electron Agent
                </Title>
              </div>
              <div className="header-meta">
                {availableModels.length > 0 ? (
                  <Space size={4} align="center">
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      模型
                    </Text>
                    <Select
                      size="small"
                      value={currentModel}
                      onChange={handleSwitchModel}
                      disabled={isSending}
                      options={modelOptions}
                      style={{ width: 150 }}
                      popupMatchSelectWidth={false}
                    />
                  </Space>
                ) : null}
                {totalUsage ? (
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    本次 {totalUsage.total_tokens} tokens
                  </Text>
                ) : null}
                {cumulativeUsage ? (
                  <Tooltip
                    title={`输入: ${cumulativeUsage.prompt_tokens} | 输出: ${cumulativeUsage.completion_tokens} | 合计: ${cumulativeUsage.total_tokens} | 请求: ${cumulativeUsage.request_count}次`}
                  >
                    <Badge
                      count={cumulativeUsage.request_count}
                      size="small"
                      color="#1f5f6b"
                    >
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        累计 {cumulativeUsage.total_tokens} tokens
                      </Text>
                    </Badge>
                  </Tooltip>
                ) : !totalUsage ? (
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    Token 用量：发送后显示
                  </Text>
                ) : null}
              </div>
            </div>
            <Button
              icon={<DeleteOutlined />}
              onClick={resetChat}
              danger
              ghost
              size="small"
            >
              清空
            </Button>
          </Header>

          <Content className="chat-content">
            <div className="messages-list">
              {messages.map((message, index) => (
                <MessageBubble
                  message={message}
                  key={`${message.role}-${index}`}
                />
              ))}
              {isSending ? (
                <div className="chat-bubble chat-bubble-assistant">
                  <div className="chat-bubble-avatar">
                    <div className="avatar avatar-assistant">
                      <RobotOutlined />
                    </div>
                  </div>
                  <div className="chat-bubble-body">
                    <div className="chat-bubble-name">Agent</div>
                    <div className="chat-bubble-content chat-thinking">
                      <LoadingOutlined style={{ marginRight: 6 }} />
                      正在思考...
                    </div>
                  </div>
                </div>
              ) : null}
              <div ref={messagesEndRef} />
            </div>

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

            <div className="composer-area">
              <TextArea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                  }
                }}
                placeholder="输入问题，例如：现在几点？或者 23 * (17 + 5) 等于多少？"
                autoSize={{ minRows: 2, maxRows: 5 }}
                disabled={isSending}
              />
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={sendMessage}
                loading={isSending}
                disabled={!input.trim() || isSending}
                size="large"
              >
                发送
              </Button>
            </div>
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
