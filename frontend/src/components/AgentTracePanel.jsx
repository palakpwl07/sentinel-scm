import React, { useEffect, useRef } from 'react';

const AGENT_META = {
  monitoring: { label: 'Monitoring Agent', color: 'border-sky-500', badge: 'bg-sky-500/20 text-sky-300' },
  risk: { label: 'Risk Agent', color: 'border-orange-500', badge: 'bg-orange-500/20 text-orange-300' },
  planning: { label: 'Planning Agent', color: 'border-emerald-500', badge: 'bg-emerald-500/20 text-emerald-300' },
  finance: { label: 'Finance Agent', color: 'border-violet-500', badge: 'bg-violet-500/20 text-violet-300' },
  negotiation: { label: 'Negotiation', color: 'border-amber-500', badge: 'bg-amber-500/20 text-amber-300' },
  ops_manager: { label: 'Operations Manager', color: 'border-blue-500', badge: 'bg-blue-500/20 text-blue-300' },
  system: { label: 'System', color: 'border-slate-500', badge: 'bg-slate-500/20 text-slate-300' },
};

export default function AgentTracePanel({ messages, isStreaming }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex h-full flex-col rounded-lg border border-slate-700 bg-slate-800/60">
      <div className="flex items-center justify-between border-b border-slate-700 px-4 py-2">
        <h2 className="text-sm font-semibold text-slate-200">Agent Trace</h2>
        {isStreaming && (
          <span className="flex items-center gap-2 text-xs text-emerald-400">
            <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-400" />
            agents working…
          </span>
        )}
      </div>
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.length === 0 && (
          <p className="text-sm text-slate-500">
            Select a scenario to start the agent society.
          </p>
        )}
        {messages.map((msg, idx) => {
          const meta = AGENT_META[msg.agent] || AGENT_META.system;
          return (
            <div key={idx} className={`rounded border-l-4 ${meta.color} bg-slate-900/70 p-3`}>
              <div className="mb-1 flex items-center justify-between">
                <span className={`rounded px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${meta.badge}`}>
                  {meta.label}
                </span>
                <span className="text-[10px] text-slate-500">
                  {msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString() : ''}
                </span>
              </div>
              <pre className="whitespace-pre-wrap font-sans text-xs leading-relaxed text-slate-300">
                {msg.message}
              </pre>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
