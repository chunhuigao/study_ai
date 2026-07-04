import React, { useMemo } from 'react';
import { Typography, Tag, Collapse, Space } from 'antd';
import {
  BulbOutlined,
  InfoCircleOutlined,
  PlayCircleOutlined,
  SearchOutlined,
} from '@ant-design/icons';

const { Text, Paragraph } = Typography;

const TracePanel = React.memo(function TracePanel({ trace }) {
  const activeKey = useMemo(() => [String(trace.length)], [trace.length]);

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
        {item.thought ? (
          <div className="trace-section trace-thought">
            <Space size={6}>
              <BulbOutlined />
              <Text strong style={{ fontSize: 12 }}>
                Thought
              </Text>
            </Space>
            <Paragraph className="trace-text">{item.thought}</Paragraph>
          </div>
        ) : null}

        {item.action || item.tool ? (
          <div className="trace-section trace-action">
            <Space size={6}>
              <PlayCircleOutlined />
              <Text strong style={{ fontSize: 12 }}>
                Action
              </Text>
            </Space>
            <Paragraph className="trace-text">
              {item.action || `${item.tool}: ${item.toolInput || ''}`}
            </Paragraph>
          </div>
        ) : null}

        {item.observation ? (
          <div className="trace-section trace-observation">
            <Space size={6}>
              <SearchOutlined />
              <Text strong style={{ fontSize: 12 }}>
                Observation
              </Text>
            </Space>
            <Paragraph className="trace-text">{item.observation}</Paragraph>
          </div>
        ) : null}

        {item.finalAnswer ? (
          <div className="trace-section trace-final">
            <Text strong style={{ fontSize: 12 }}>
              Final Answer
            </Text>
            <Paragraph className="trace-text">{item.finalAnswer}</Paragraph>
          </div>
        ) : null}

        <details className="trace-raw">
          <summary>原始模型输出</summary>
          <pre className="trace-pre">{item.modelOutput}</pre>
        </details>
      </div>
    ),
  }));

  return (
    <Collapse
      items={items}
      defaultActiveKey={activeKey}
      size="small"
      className="trace-collapse"
    />
  );
});

export default TracePanel;
