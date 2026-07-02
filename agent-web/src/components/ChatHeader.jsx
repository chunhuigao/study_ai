import React from 'react';
import { Layout, Typography, Button, Space, Badge, Tooltip } from 'antd';
import { DeleteOutlined, ThunderboltOutlined } from '@ant-design/icons';

const { Header } = Layout;
const { Title, Text } = Typography;

const TOKEN_UNITS = ['', 'K', 'M', 'G', 'T', 'P', 'E'];

function formatTokens(n) {
  if (n == null || isNaN(n)) return '0';
  let value = Number(n);
  if (value < 1000) return String(value);
  let unitIndex = 0;
  while (value >= 1000 && unitIndex < TOKEN_UNITS.length - 1) {
    value /= 1000;
    unitIndex++;
  }
  return `${value % 1 === 0 ? value : value.toFixed(1)}${TOKEN_UNITS[unitIndex]}`;
}

const ChatHeader = React.memo(function ChatHeader({
  isSending,
  totalUsage,
  cumulativeUsage,
  onReset,
}) {
  return (
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
          {totalUsage ? (
            <Text type="secondary" style={{ fontSize: 12 }}>
              本次 {formatTokens(totalUsage.total_tokens)} tokens
            </Text>
          ) : null}
          {cumulativeUsage ? (
            <Tooltip
              title={`输入: ${formatTokens(cumulativeUsage.prompt_tokens)} | 输出: ${formatTokens(cumulativeUsage.completion_tokens)} | 合计: ${formatTokens(cumulativeUsage.total_tokens)} | 请求: ${cumulativeUsage.request_count}次`}
            >
              <Badge
                count={cumulativeUsage.request_count}
                size="small"
                color="#1f5f6b"
              >
                <Text
                  type="secondary"
                  style={{ fontSize: 12, whiteSpace: 'nowrap' }}
                >
                  累计 {formatTokens(cumulativeUsage.total_tokens)} tokens
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
        onClick={onReset}
        danger
        ghost
        size="small"
      >
        清空
      </Button>
    </Header>
  );
});

export default ChatHeader;
