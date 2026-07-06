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
  Spin,
  Typography,
  Upload,
  message,
  theme,
} from 'antd';
import {
  ClearOutlined,
  FilePdfOutlined,
  InboxOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import zhCN from 'antd/locale/zh_CN';
import './styles.css';

const { Header, Content, Sider } = Layout;
const { Text, Title, Paragraph } = Typography;
const { TextArea } = Input;
const { Dragger } = Upload;

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

  const uploadPdf = useCallback(
    async (file) => {
      setError('');
      const filePath = file.path || file.originFileObj?.path;
      if (!filePath) {
        setError('请在 Electron 桌面窗口中上传 PDF，浏览器预览模式拿不到本地文件路径。');
        return Upload.LIST_IGNORE;
      }

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
      return Upload.LIST_IGNORE;
    },
    [loadDocuments],
  );

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
              <Dragger
                accept=".pdf,application/pdf"
                multiple={false}
                showUploadList={false}
                beforeUpload={uploadPdf}
                disabled={!apiReady || isUploading}
              >
                <p className="ant-upload-drag-icon">
                  {isUploading ? <Spin /> : <InboxOutlined />}
                </p>
                <p className="ant-upload-text">上传 PDF</p>
                <p className="ant-upload-hint">文本型 PDF 会被抽取、切块并加入本地索引</p>
              </Dragger>

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

