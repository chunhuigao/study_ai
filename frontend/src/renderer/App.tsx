import {
  Activity,
  BookOpen,
  CheckCircle2,
  Circle,
  Loader2,
  Network,
  Send,
  Wrench,
} from 'lucide-react';
import type { ReactNode } from 'react';
import {
  FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';

import type { PlanStep, RelayEvent, TaskState } from '@shared/relay';

const WS_URL = 'ws://127.0.0.1:8000/ws';

const seedSteps: PlanStep[] = [
  {
    id: 'seed-plan',
    title: '等待任务',
    goal: '输入你想学习的 AI 主题，Relay 会规划并分派给 sub-agent',
    agent: 'plan_agent',
    status: 'pending',
  },
];

function asString(value: unknown): string | undefined {
  return typeof value === 'string' ? value : undefined;
}

function findLastResult(events: RelayEvent[]): string {
  for (let i = events.length - 1; i >= 0; i--) {
    if (events[i].type === 'step.completed') {
      const result = asString(events[i].payload.result);
      if (result) return result;
    }
  }
  return '';
}

type EventHandler = (
  event: RelayEvent,
  setTask: React.Dispatch<React.SetStateAction<TaskState | null>>,
) => void;

const eventHandlers: Record<string, EventHandler> = {
  'task.created': (event, setTask) => {
    setTask(event.payload as unknown as TaskState);
  },
  'task.planned': (event, setTask) => {
    const steps = event.payload.steps as PlanStep[];
    setTask((current) =>
      current ? { ...current, status: 'running', steps } : current,
    );
  },
  'step.started': (event, setTask) => {
    const incoming = event.payload.step as PlanStep;
    setTask((current) =>
      current
        ? {
            ...current,
            steps: current.steps.map((step) =>
              step.id === incoming.id
                ? { ...step, status: 'running' as const }
                : step,
            ),
          }
        : current,
    );
  },
  'step.completed': (event, setTask) => {
    const incoming = event.payload.step as PlanStep;
    const result = asString(event.payload.result);
    setTask((current) =>
      current
        ? {
            ...current,
            steps: current.steps.map((step) =>
              step.id === incoming.id
                ? {
                    ...step,
                    status: 'completed' as const,
                    result: result ?? step.result,
                  }
                : step,
            ),
          }
        : current,
    );
  },
  'task.completed': (event, setTask) => {
    const result = asString(event.payload.result);
    setTask((current) =>
      current
        ? { ...current, status: 'completed', result: result ?? current.result }
        : current,
    );
  },
};

export function App() {
  const [input, setInput] = useState(
    '我想学习 AI agent、ReAct、MCP，并做一个 Python demo',
  );
  const [task, setTask] = useState<TaskState | null>(null);
  const [events, setEvents] = useState<RelayEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);

  const steps = useMemo(
    () => (task?.steps?.length ? task.steps : seedSteps),
    [task],
  );
  const progress = useMemo(() => {
    const completed = steps.filter(
      (step) => step.status === 'completed',
    ).length;
    return Math.round((completed / steps.length) * 100);
  }, [steps]);

  const latestResult = useMemo(
    () => task?.result || findLastResult(events),
    [events, task],
  );

  useEffect(() => {
    return () => {
      socketRef.current?.close();
      socketRef.current = null;
    };
  }, []);

  const ensureSocket = useCallback(() => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      return socketRef.current;
    }
    socketRef.current?.close();

    const socket = new WebSocket(WS_URL);
    socketRef.current = socket;

    socket.onopen = () => {
      setConnected(true);
      setError(null);
    };
    socket.onclose = () => setConnected(false);
    socket.onerror = () =>
      setError('无法连接 Relay 服务端，请先启动 agent-server。');
    socket.onmessage = (message) => {
      const event = JSON.parse(message.data) as RelayEvent;
      setEvents((current) => [...current, event]);
      eventHandlers[event.type]?.(event, setTask);
    };
    return socket;
  }, []);

  const submit = useCallback(
    (event: FormEvent) => {
      event.preventDefault();
      const text = input.trim();
      if (!text) return;
      setTask(null);
      setEvents([]);
      const socket = ensureSocket();
      const send = () =>
        socket.send(JSON.stringify({ type: 'task.create', input: text }));
      if (socket.readyState === WebSocket.OPEN) {
        send();
      } else {
        socket.addEventListener('open', send, { once: true });
      }
    },
    [input, ensureSocket],
  );

  return (
    <main className="app-shell">
      <section className="workspace">
        <header className="titlebar">
          <div>
            <p className="eyebrow">Relay</p>
            <h1>AI 学习协作台</h1>
          </div>
          <div className={connected ? 'status online' : 'status'}>
            <Activity size={16} />
            {connected ? '已连接' : '未连接'}
          </div>
        </header>

        <form className="composer" onSubmit={submit}>
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
          />
          <button type="submit" title="发送任务">
            <Send size={18} />
            运行
          </button>
        </form>

        {error && <div className="error">{error}</div>}

        <section className="progress-band">
          <div>
            <span>执行进度</span>
            <strong>{progress}%</strong>
          </div>
          <div className="progress-track">
            <div style={{ width: `${progress}%` }} />
          </div>
        </section>

        <section className="agent-grid">
          <AgentCard
            icon={<BookOpen size={20} />}
            name="Plan-Agent"
            text="ReAct 模式规划与协调"
          />
          <AgentCard
            icon={<Network size={20} />}
            name="Sub-Agents"
            text="按领域执行具体子任务"
          />
          <AgentCard
            icon={<Wrench size={20} />}
            name="Skills + MCP"
            text="四层 skill 与工具扩展"
          />
        </section>

        <section className="timeline">
          {steps.map((step) => (
            <article className="step" key={step.id}>
              <StepIcon status={step.status} />
              <div>
                <div className="step-head">
                  <h2>{step.title}</h2>
                  <span>{step.agent}</span>
                </div>
                <p>{step.goal}</p>
                {step.result && <pre>{step.result}</pre>}
              </div>
            </article>
          ))}
        </section>
      </section>

      <aside className="side-panel">
        <h2>执行结果</h2>
        <pre className="result">
          {latestResult || '任务完成后会显示汇总结果。'}
        </pre>
        <h2>事件流</h2>
        <div className="events">
          {events.length === 0 && <p>暂无事件</p>}
          {events.map((event, index) => (
            <code key={`${event.type}-${index}`}>{event.type}</code>
          ))}
        </div>
      </aside>
    </main>
  );
}

function AgentCard({
  icon,
  name,
  text,
}: {
  icon: ReactNode;
  name: string;
  text: string;
}) {
  return (
    <article className="agent-card">
      {icon}
      <div>
        <h2>{name}</h2>
        <p>{text}</p>
      </div>
    </article>
  );
}

function StepIcon({ status }: { status: PlanStep['status'] }) {
  if (status === 'completed')
    return <CheckCircle2 className="step-icon done" size={22} />;
  if (status === 'running')
    return <Loader2 className="step-icon spin" size={22} />;
  return <Circle className="step-icon" size={22} />;
}
