import React, { useState } from 'react';

export default function HITLModal({ open, recommendation, onDecision }) {
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (!open || !recommendation) return null;

  const decide = async (decision) => {
    setSubmitting(true);
    try {
      await onDecision(decision, notes);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-xl border border-blue-700 bg-slate-900 p-6 shadow-2xl">
        <h2 className="mb-1 text-lg font-bold text-blue-300">Human Approval Required</h2>
        <p className="mb-4 text-xs text-slate-400">
          The agent society has produced a recommendation. Review and approve or reject.
        </p>

        <div className="mb-4 rounded border border-slate-700 bg-slate-800 p-3">
          <p className="text-sm text-slate-200">{recommendation.decision}</p>
          <ul className="mt-2 list-inside list-disc space-y-1 text-xs text-slate-300">
            {(recommendation.primary_actions || []).map((action, idx) => (
              <li key={idx}>{action}</li>
            ))}
          </ul>
          <p className="mt-3 text-xs text-slate-400">
            Additional cost:{' '}
            <span className="font-semibold text-red-300">
              SGD {Number(recommendation.additional_cost_sgd).toLocaleString()}
            </span>{' '}
            · Net benefit:{' '}
            <span className="font-semibold text-emerald-300">
              SGD {Number(recommendation.net_benefit_sgd).toLocaleString()}
            </span>
          </p>
        </div>

        <label className="mb-1 block text-xs font-medium text-slate-400" htmlFor="hitl-notes">
          Notes (optional)
        </label>
        <textarea
          id="hitl-notes"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={2}
          className="mb-4 w-full rounded border border-slate-600 bg-slate-800 p-2 text-xs text-slate-200 focus:border-blue-500 focus:outline-none"
          placeholder="e.g. approved, but cap air freight spend at SGD 1.2M"
        />

        <div className="flex justify-end gap-3">
          <button
            type="button"
            disabled={submitting}
            onClick={() => decide('reject')}
            className="rounded-md border border-red-600 px-4 py-2 text-sm font-medium text-red-300 hover:bg-red-600/20 disabled:opacity-50"
          >
            Reject
          </button>
          <button
            type="button"
            disabled={submitting}
            onClick={() => decide('approve')}
            className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-50"
          >
            Approve
          </button>
        </div>
      </div>
    </div>
  );
}
