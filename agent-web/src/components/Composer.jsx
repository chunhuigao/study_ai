import React, { useRef, useMemo } from 'react';
import { Input, Button, Select, Tooltip, Space } from 'antd';
import {
  SendOutlined,
  PlusOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';

const { TextArea } = Input;

const Composer = React.memo(function Composer({
  input,
  isSending,
  onInputChange,
  onSend,
  currentModel,
  availableModels,
  onSwitchModel,
  onFileSelect,
  attachedFiles,
  onRemoveFile,
}) {
  const fileInputRef = useRef(null);

  const modelOptions = useMemo(
    () =>
      availableModels.map((m) => ({
        value: m.id,
        label: (
          <Space size={4}>
            <span>{m.name}</span>
            <Tooltip title={m.description}>
              <InfoCircleOutlined style={{ color: '#bfbfbf', fontSize: 11 }} />
            </Tooltip>
          </Space>
        ),
      })),
    [availableModels],
  );

  const handleFileClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e) => {
    const files = e.target.files;
    if (files && files.length > 0 && onFileSelect) {
      onFileSelect(Array.from(files));
    }
    e.target.value = '';
  };

  return (
    <div className="composer-area">
      <div className="composer-box">
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
          autoSize={{ minRows: 1, maxRows: 5 }}
          disabled={isSending}
          variant="borderless"
          className="composer-textarea"
        />
        {attachedFiles && attachedFiles.length > 0 ? (
          <div className="composer-files">
            {attachedFiles.map((file, index) => (
              <div key={index} className="composer-file-tag">
                <span className="composer-file-name">{file.name}</span>
                <span
                  className="composer-file-remove"
                  onClick={() => onRemoveFile && onRemoveFile(index)}
                >
                  ×
                </span>
              </div>
            ))}
          </div>
        ) : null}
        <div className="composer-footer">
          <div className="composer-footer-left">
            <Tooltip title="添加文件">
              <Button
                type="text"
                size="small"
                icon={<PlusOutlined />}
                className="composer-tool-btn"
                onClick={handleFileClick}
                disabled={isSending}
              />
            </Tooltip>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              style={{ display: 'none' }}
              onChange={handleFileChange}
            />
            {availableModels.length > 0 ? (
              <Select
                size="small"
                variant="borderless"
                value={currentModel}
                onChange={onSwitchModel}
                disabled={isSending}
                options={modelOptions}
                className="composer-model-select"
                popupMatchSelectWidth={false}
              />
            ) : null}
          </div>
        </div>
      </div>
      <Button
        type="primary"
        icon={<SendOutlined />}
        onClick={onSend}
        loading={isSending}
        disabled={!input.trim() || isSending}
        size="large"
        className="composer-send-btn"
      >
        发送
      </Button>
    </div>
  );
});

export default Composer;
