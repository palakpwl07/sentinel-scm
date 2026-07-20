import React, { useState } from 'react';
import { triggerLiveSearch } from '../lib/api';

export default function LiveSearchInput({ disabled, onSearchStart, onStarted }) {
  const [query, setQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState(null);
  const [lastResult, setLastResult] = useState(null);

  const submit = async (event) => {
    event.preventDefault();
    if (!query.trim() || searching || disabled) return;
    setSearching(true);
    setError(null);
    setLastResult(null);
    // Clear the previous run's trace/evidence/badges before the request starts —
    // live search takes 5-15s, so stale output would otherwise sit on screen.
    if (onSearchStart) onSearchStart();
    const sessionId = `live-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    try {
      const data = await triggerLiveSearch(query.trim(), sessionId);
      setLastResult(data);
      if (data.status === 'started') {
        onStarted(sessionId, data);
      }
    } catch (err) {
      setError(err.message || 'Live search failed — use a canned scenario instead.');
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="w-full">
      <form onSubmit={submit} className="flex items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">
          Live search:
        </span>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Paste a real headline or query, e.g. 'Taiwan Strait tensions semiconductor shipping'"
          disabled={searching || disabled}
          className="w-full max-w-xl rounded-md border border-slate-600 bg-slate-800 px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={searching || disabled || !query.trim()}
          className="whitespace-nowrap rounded-md border border-sky-500 bg-sky-600/20 px-3 py-1.5 text-xs font-medium text-sky-300 transition hover:bg-sky-600/40 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {searching ? 'Searching the live web…' : 'Search & Analyze'}
        </button>
      </form>

      {searching && (
        <p className="mt-1 flex items-center gap-2 text-[11px] text-sky-400">
          <span className="h-2 w-2 animate-pulse rounded-full bg-sky-400" />
          Searching the live web and extracting a structured event — this takes
          5–15s before the agents start.
        </p>
      )}

      {error && (
        <p className="mt-1 text-[11px] text-red-400">
          {error} The canned scenario buttons above still work as a fallback.
        </p>
      )}

      {lastResult && lastResult.status === 'no_impact' && (
        <div className="mt-2 max-w-2xl rounded-md border border-amber-600 bg-amber-500/10 px-3 py-2">
          <p className="text-xs font-semibold text-amber-300">
            No material supply-chain impact identified
          </p>
          {lastResult.event?.name && (
            <p className="mt-1 text-[11px] font-medium text-slate-200">
              {lastResult.event.name}
            </p>
          )}
          {lastResult.event?.description && (
            <p className="mt-1 text-[11px] text-slate-300">
              {lastResult.event.description}
            </p>
          )}
          <p className="mt-1 text-[11px] italic text-amber-200">
            Monitoring Agent: {lastResult.reasoning}
          </p>
          <p className="mt-1 text-[10px] text-slate-400">
            Risk, Planning, Finance and Ops were not run — there is nothing in
            the supply network for them to evaluate.
          </p>
        </div>
      )}

      {lastResult && lastResult.status === 'started' && (
        <p className="mt-1 text-[11px] text-emerald-400">
          Connection found: {lastResult.reasoning}
        </p>
      )}
    </div>
  );
}
