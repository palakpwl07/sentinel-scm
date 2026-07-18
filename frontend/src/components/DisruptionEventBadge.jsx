import React from 'react';

const SEVERITY_STYLES = {
  CRITICAL: 'bg-red-600/20 text-red-300 border-red-600',
  HIGH: 'bg-amber-500/20 text-amber-300 border-amber-500',
  MEDIUM: 'bg-yellow-500/20 text-yellow-200 border-yellow-500',
};

export default function DisruptionEventBadge({ events }) {
  if (!events || events.length === 0) {
    return (
      <span className="rounded-full border border-emerald-600 bg-emerald-600/20 px-3 py-1 text-xs text-emerald-300">
        No active disruptions
      </span>
    );
  }
  return (
    <div className="flex flex-wrap justify-end gap-1.5">
      {events.map((event) => (
        <span
          key={event.id}
          title={event.description}
          className={`rounded-full border px-2.5 py-1 text-[10px] font-medium ${
            SEVERITY_STYLES[event.severity] || SEVERITY_STYLES.MEDIUM
          }`}
        >
          ⚠ {event.name}
        </span>
      ))}
    </div>
  );
}
