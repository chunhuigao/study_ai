import { useCallback, useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Alert,
  Button,
  ConfigProvider,
  Empty,
  Input,
  Layout,
  List,
  Space,
  Typography,
  message,
  theme,
} from 'antd';
import {
  ClearOutlined,
  FilePdfOutlined,
  SearchOutlined,
  UploadOutlined,
} from '@ant-design/icons';
import zhCN from 'antd/locale/zh_CN';
import './styles.css';

const { Header, Content, Sider } = Layout;
const { Text, Title, Paragraph } = Typography;
const { TextArea } = Input;

function App() {
  const [documents, setDocuments] = useState([]);
  const [chunkCount, setChunkCount] = useState(0);
  const [question, setQuestion] = useState('这份资料主要讲了什么？');
  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState([]);
  const [error, setError] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isAsking, setIsAsking] = useState(false);

  const hasDocuments = documents.length > 0;
  const apiReady = useMemo(() => Boolean(window.ragApi), []);

  const loadDocuments = useCallback(async () => {
    if (!window.ragApi) return;
    const result = await window.ragApi.documents();
    if (result.ok) {
      setDocuments(result.documents || []);
      setChunkCount(result.chunkCount || 0);
    }
  }, []);

  useEffect(() => {
    loadDocuments().catch((err) => setError(String(err)));
  }, [loadDocuments]);

  const ingestPdf = useCallback(
    async (filePath) => {
      setError('');

      setIsUploading(true);
      try {
        const result = await window.ragApi.ingestPdf(filePath);
        if (!result.ok) {
          throw new Error(result.error || 'PDF 处理失败');
        }
        message.success(`已索引 ${result.document.fileName}，生成 ${result.chunkCount} 个片段`);
        await loadDocuments();
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setIsUploading(false);
      }
    },
    [loadDocuments],
  );

  const selectAndUploadPdf = useCallback(async () => {
    setError('');
    if (!window.ragApi?.selectPdf) {
      setError('请使用 Electron 桌面窗口选择 PDF，浏览器预览模式无法打开本地文件选择器。');
      return;
    }

    try {
      const selected = await window.ragApi.selectPdf();
      if (!selected.ok || selected.canceled) {
        return;
      }
      await ingestPdf(selected.filePath);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, [ingestPdf]);

  const ask = useCallback(async () => {
    const text = question.trim();
    if (!text || isAsking) return;

    setError('');
    setIsAsking(true);
    try {
      const result = await window.ragApi.query({ question: text, topK: 4 });
      if (!result.ok) {
        throw new Error(result.error || '检索失败');
      }
      setAnswer(result.answer || '');
      setSources(result.sources || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsAsking(false);
    }
  }, [isAsking, question]);

  const clearLibrary = useCallback(async () => {
    setError('');
    const result = await window.ragApi.clear();
    if (result.ok) {
      setDocuments([]);
      setChunkCount(0);
      setAnswer('');
      setSources([]);
      message.success('资料库已清空');
    }
  }, []);

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
        <Header className="app-header">
          <div>
            <Text className="app-kicker">AI RAG Learning</Text>
            <Title level={3}>PDF 资料问答</Title>
          </div>
          <Space>
            <Text type="secondary">文档 {documents.length}</Text>
            <Text type="secondary">片段 {chunkCount}</Text>
          </Space>
        </Header>

        <Layout className="app-main">
          <Sider width={360} className="library-panel" theme="light">
            <section className="panel-section">
              <div className="upload-card">
                <FilePdfOutlined className="upload-icon" />
                <Text strong>上传 PDF</Text>
                <Text type="secondary">文本型 PDF 会被抽取、切块并加入本地索引</Text>
                <Button
                  type="primary"
                  icon={<UploadOutlined />}
                  loading={isUploading}
                  disabled={!apiReady}
                  onClick={selectAndUploadPdf}
                  block
                >
                  选择 PDF 文件
                </Button>
              </div>

              <Alert
                className="panel-alert"
                type="info"
                showIcon
                message="后续扩展视频资料时，也会复用同一套索引和检索流程。"
              />

              {!apiReady ? (
                <Alert
                  className="panel-alert"
                  type="warning"
                  showIcon
                  message="请使用 Electron 窗口运行"
                />
              ) : null}
            </section>

            <section className="panel-section library-list">
              <div className="section-head">
                <Text strong>资料库</Text>
                <Button
                  size="small"
                  icon={<ClearOutlined />}
                  onClick={clearLibrary}
                  disabled={!hasDocuments}
                >
                  清空
                </Button>
              </div>

              {hasDocuments ? (
                <List
                  dataSource={documents}
                  renderItem={(item) => (
                    <List.Item className="document-item">
                      <List.Item.Meta
                        avatar={<FilePdfOutlined className="pdf-icon" />}
                        title={item.fileName}
                        description={`${item.pageCount} 页 · ${item.chunkCount} 个片段`}
                      />
                    </List.Item>
                  )}
                />
              ) : (
                <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无 PDF" />
              )}
            </section>
          </Sider>

          <Content className="qa-panel">
            <section className="question-panel">
              <TextArea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                onPressEnter={(event) => {
                  if (!event.shiftKey) {
                    event.preventDefault();
                    ask();
                  }
                }}
                rows={3}
                placeholder="输入你想问资料的问题"
              />
              <Button
                type="primary"
                icon={<SearchOutlined />}
                loading={isAsking}
                onClick={ask}
              >
                检索回答
              </Button>
            </section>

            {error ? (
              <Alert
                className="error-alert"
                type="error"
                showIcon
                closable
                message={error}
                onClose={() => setError('')}
              />
            ) : null}

            <section className="answer-panel">
              <Title level={4}>回答</Title>
              {answer ? (
                <Paragraph className="answer-text">{answer}</Paragraph>
              ) : (
                <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="上传 PDF 后开始提问" />
              )}
            </section>

            <section className="sources-panel">
              <Title level={4}>引用片段</Title>
              {sources.length ? (
                <List
                  dataSource={sources}
                  renderItem={(item, index) => (
                    <List.Item className="source-item">
                      <div className="source-title">
                        <Text strong>{index + 1}. {item.fileName}</Text>
                        <Text type="secondary">第 {item.page} 页</Text>
                      </div>
                      <Paragraph className="source-text">{item.text}</Paragraph>
                    </List.Item>
                  )}
                />
              ) : (
                <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无引用" />
              )}
            </section>
          </Content>
        </Layout>
      </Layout>
    </ConfigProvider>
  );
}

createRoot(document.getElementById('root')).render(<App />);
