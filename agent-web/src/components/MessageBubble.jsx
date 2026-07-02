import React from 'react';
import { Typography } from 'antd';
import { RobotOutlined, UserOutlined } from '@ant-design/icons';

const { Text } = Typography;

const MessageBubble = React.memo(function MessageBubble({ message }) {
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
});

export default MessageBubble;
