import React from 'react';

const fmtSGD = (v) =>
  typeof v === 'number' ? `SGD ${v.toLocaleString(undefined, { maximumFractionDigits: 0 })}` : '—';

export default function EvidenceChainCard({ recommendation }) {
  if (!recommendation) {
    return (
      <div className="rounded-lg border border-slate-700 bg-slate-800/60 p-4">
        <h2 className="text-sm font-semibold text-slate-200">Evidence Chain</h2>
        <p className="mt-2 text-xs text-slate-500">
          The final recommendation and its evidence chain will appear here after the
          Operations Manager arbitrates.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-blue-700 bg-slate-800/80 p-4">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-blue-300">Final Recommendation</h2>
        <span className="rounded bg-blue-600/30 px-2 py-0.5 text-[10px] font-semibold text-blue-200">
          confidence {(recommendation.confidence_score * 100).toFixed(0)}%
        </span>
      </div>

      <p className="mb-3 text-xs leading-relaxed text-slate-200">{recommendation.decision}</p>

      <h3 className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
        Primary actions
      </h3>
      <ul className="mb-3 list-inside list-disc space-y-1 text-xs text-slate-300">
        {(recommendation.primary_actions || []).map((action, idx) => (
          <li key={idx}>{action}</li>
        ))}
      </ul>

      <h3 className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
        Evidence chain
      </h3>
      <div className="mb-3 space-y-2">
        {(recommendation.evidence || []).map((evidence, idx) => (
          <div key={idx} className="rounded border border-slate-700 bg-slate-900/70 p-2">
            <p className="text-[10px] font-semibold text-sky-400">{evidence.source}</p>
            <p className="text-xs text-slate-300">{evidence.fact}</p>
            <p className="text-[11px] italic text-slate-400">→ {evidence.impact}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="rounded bg-slate-900/70 p-2">
          <p className="text-[10px] text-slate-400">Additional cost</p>
          <p className="text-xs font-semibold text-red-300">{fmtSGD(recommendation.additional_cost_sgd)}</p>
        </div>
        <div className="rounded bg-slate-900/70 p-2">
          <p className="text-[10px] text-slate-400">Revenue protected</p>
          <p className="text-xs font-semibold text-emerald-300">{fmtSGD(recommendation.revenue_protected_sgd)}</p>
        </div>
        <div className="rounded bg-slate-900/70 p-2">
          <p className="text-[10px] text-slate-400">Net benefit</p>
          <p className="text-xs font-semibold text-blue-300">{fmtSGD(recommendation.net_benefit_sgd)}</p>
        </div>
      </div>
    </div>
  );
}
