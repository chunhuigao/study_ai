import React, { useMemo } from 'react';
import { Typography, Tag, Collapse, Space } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';

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
      defaultActiveKey={activeKey}
      size="small"
      className="trace-collapse"
    />
  );
});

export default TracePanel;
