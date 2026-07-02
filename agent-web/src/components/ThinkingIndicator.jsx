import React from 'react';
import { RobotOutlined, LoadingOutlined } from '@ant-design/icons';

const ThinkingIndicator = React.memo(function ThinkingIndicator() {
  return (
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
  );
});

export default ThinkingIndicator;
