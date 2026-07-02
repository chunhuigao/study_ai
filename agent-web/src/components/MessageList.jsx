import React, { useEffect, useMemo, useRef } from 'react';
import { Typography } from 'antd';
import MessageBubble from './MessageBubble';
import ThinkingIndicator from './ThinkingIndicator';

const { Text } = Typography;

const MAX_RENDER_MESSAGES = 50;

const MessageList = React.memo(function MessageList({ messages, isSending }) {
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSending]);

  const { visibleMessages, hiddenCount } = useMemo(() => {
    const total = messages.length;
    if (total <= MAX_RENDER_MESSAGES) {
      return { visibleMessages: messages, hiddenCount: 0 };
    }
    return {
      visibleMessages: messages.slice(total - MAX_RENDER_MESSAGES),
      hiddenCount: total - MAX_RENDER_MESSAGES,
    };
  }, [messages]);

  return (
    <div className="messages-list">
      {hiddenCount > 0 ? (
        <div className="messages-overflow-hint">
          <Text type="secondary" style={{ fontSize: 12 }}>
            已省略前 {hiddenCount} 条历史消息
          </Text>
        </div>
      ) : null}
      {visibleMessages.map((message) => (
        <MessageBubble message={message} key={message.id} />
      ))}
      {isSending ? <ThinkingIndicator /> : null}
      <div ref={messagesEndRef} />
    </div>
  );
});

export default MessageList;
