import React from 'react';

export default function ScenarioSelector({ scenarios, activeScenarioId, disabled, onSelect }) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">
        Scenarios:
      </span>
      {scenarios.map((scenario) => (
        <button
          key={scenario.id}
          type="button"
          disabled={disabled}
          onClick={() => onSelect(scenario.id)}
          title={scenario.description}
          className={`rounded-md border px-3 py-1.5 text-xs font-medium transition
            ${activeScenarioId === scenario.id
              ? 'border-blue-500 bg-blue-600 text-white'
              : 'border-slate-600 bg-slate-800 text-slate-300 hover:border-blue-500 hover:text-white'}
            ${disabled ? 'cursor-not-allowed opacity-50' : ''}`}
        >
          {scenario.name}
        </button>
      ))}
    </div>
  );
}
