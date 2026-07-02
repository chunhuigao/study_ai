import React from 'react';
import { Input, Button } from 'antd';
import { SendOutlined } from '@ant-design/icons';

const { TextArea } = Input;

const Composer = React.memo(function Composer({
  input,
  isSending,
  onInputChange,
  onSend,
}) {
  return (
    <div className="composer-area">
      <TextArea
        value={input}
        onChange={(e) => onInputChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            onSend();
          }
        }}
        placeholder="输入问题，例如：现在几点？或者 23 * (17 + 5) 等于多少？"
        autoSize={{ minRows: 2, maxRows: 5 }}
        disabled={isSending}
      />
      <Button
        type="primary"
        icon={<SendOutlined />}
        onClick={onSend}
        loading={isSending}
        disabled={!input.trim() || isSending}
        size="large"
      >
        发送
      </Button>
    </div>
  );
});

export default Composer;
