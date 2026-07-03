import React, { useMemo, useState } from 'react';
import {
  Button,
  Checkbox,
  Empty,
  Form,
  Input,
  Modal,
  Select,
  Space,
  Switch,
  Tag,
  Typography,
} from 'antd';
import { PlusOutlined, ToolOutlined } from '@ant-design/icons';

const { Text, Paragraph } = Typography;

function makeSkillId(name) {
  return name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9_\-\u4e00-\u9fa5]+/g, '_')
    .replace(/^_+|_+$/g, '');
}

const SkillsPanel = React.memo(function SkillsPanel({
  skills,
  availableTools,
  isLoading,
  onToggleSkill,
  onCreateSkill,
}) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [form] = Form.useForm();

  const toolOptions = useMemo(
    () => availableTools.map((tool) => ({ label: tool, value: tool })),
    [availableTools],
  );

  const handleSubmit = async () => {
    const values = await form.validateFields();
    const payload = {
      id: values.id || makeSkillId(values.name),
      name: values.name,
      description: values.description || '',
      enabled: values.enabled ?? true,
      builtin: false,
      tools: values.tools || [],
      instructions: values.instructions || '',
    };
    await onCreateSkill(payload);
    form.resetFields();
    setIsModalOpen(false);
  };

  return (
    <div className="skills-panel">
      <div className="skills-panel-header">
        <Space size={6}>
          <ToolOutlined />
          <Text strong>Skills</Text>
        </Space>
        <Button
          size="small"
          type="text"
          icon={<PlusOutlined />}
          onClick={() => setIsModalOpen(true)}
        >
          新增
        </Button>
      </div>

      <div className="skills-list">
        {skills.length === 0 ? (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无 skill" />
        ) : (
          skills.map((skill) => (
            <div className="skill-item" key={skill.id}>
              <div className="skill-main">
                <div className="skill-title-row">
                  <Text strong>{skill.name}</Text>
                  <Tag color={skill.builtin ? 'blue' : 'green'}>
                    {skill.builtin ? '内置' : '配置'}
                  </Tag>
                </div>
                <Paragraph
                  type="secondary"
                  ellipsis={{ rows: 2 }}
                  className="skill-description"
                >
                  {skill.description || skill.instructions || skill.id}
                </Paragraph>
                {skill.tools?.length ? (
                  <div className="skill-tools">
                    {skill.tools.map((tool) => (
                      <Tag key={tool}>{tool}</Tag>
                    ))}
                  </div>
                ) : null}
              </div>
              <Switch
                size="small"
                checked={skill.enabled}
                loading={isLoading}
                onChange={(checked) => onToggleSkill(skill.id, checked)}
              />
            </div>
          ))
        )}
      </div>

      <Modal
        title="新增配置 Skill"
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        onOk={handleSubmit}
        okText="保存"
        cancelText="取消"
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{ enabled: true, tools: [] }}
        >
          <Form.Item
            label="名称"
            name="name"
            rules={[{ required: true, message: '请输入 skill 名称' }]}
          >
            <Input placeholder="例如：研究模式" />
          </Form.Item>
          <Form.Item label="ID" name="id">
            <Input placeholder="留空时根据名称生成" />
          </Form.Item>
          <Form.Item label="描述" name="description">
            <Input.TextArea rows={2} placeholder="这个 skill 适合什么任务" />
          </Form.Item>
          <Form.Item label="启用工具" name="tools">
            <Select
              mode="multiple"
              options={toolOptions}
              placeholder="可选：选择此 skill 开启的工具"
            />
          </Form.Item>
          <Form.Item
            label="使用规则"
            name="instructions"
            rules={[{ required: true, message: '请输入使用规则' }]}
          >
            <Input.TextArea rows={4} placeholder="告诉 Agent 何时使用、如何回答" />
          </Form.Item>
          <Form.Item name="enabled" valuePropName="checked">
            <Checkbox>保存后立即启用</Checkbox>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
});

export default SkillsPanel;
