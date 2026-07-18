import React from 'react';

function barColor(days, reorderPoint) {
  if (days < reorderPoint * 0.7) return 'bg-red-600';
  if (days < reorderPoint) return 'bg-amber-500';
  return 'bg-emerald-600';
}

export default function InventoryStatusBar({ materials }) {
  if (!materials || materials.length === 0) return null;
  const maxDays = 30;

  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800/60 px-4 py-3">
      <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
        Inventory Runway (days)
      </h2>
      <div className="grid grid-cols-2 gap-x-6 gap-y-2 md:grid-cols-3 lg:grid-cols-6">
        {materials.map((material) => {
          const days = material.current_inventory_days;
          const pct = Math.min(100, (days / maxDays) * 100);
          return (
            <div key={material.id}>
              <div className="mb-1 flex items-baseline justify-between">
                <span className="truncate text-[11px] text-slate-300" title={material.name}>
                  {material.name}
                </span>
                <span className={`ml-1 text-[11px] font-semibold ${
                  days < material.reorder_point_days ? 'text-red-400' : 'text-slate-200'
                }`}>
                  {days}d
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded bg-slate-700">
                <div
                  className={`h-full rounded ${barColor(days, material.reorder_point_days)}`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
