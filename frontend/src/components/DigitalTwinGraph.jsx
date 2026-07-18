import React, { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';
import fcose from 'cytoscape-fcose';
import { cytoscapeLayout, cytoscapeStylesheet } from '../lib/cytoscapeConfig';

cytoscape.use(fcose);

function buildElements(twin) {
  if (!twin) return [];
  const elements = [];

  if (twin.company) {
    elements.push({
      data: { id: twin.company.id, label: twin.company.name, type: 'Company' },
    });
  }

  (twin.factories || []).forEach((f) =>
    elements.push({ data: { id: f.id, label: f.name, type: 'Factory' } })
  );
  (twin.warehouses || []).forEach((w) =>
    elements.push({ data: { id: w.id, label: w.name, type: 'Warehouse' } })
  );
  (twin.ports || []).forEach((p) =>
    elements.push({
      data: {
        id: p.id,
        label: p.name,
        type: 'Port',
        disrupted: String(Boolean(p.is_disrupted)),
      },
    })
  );
  (twin.suppliers || []).forEach((s) =>
    elements.push({
      data: {
        id: s.id,
        label: s.name,
        type: 'Supplier',
        available: String(Boolean(s.is_available)),
        risk: s.reliability_score < 0.5 && s.is_available ? 'HIGH' : 'NORMAL',
      },
    })
  );

  const nodeIds = new Set(elements.map((e) => e.data.id));
  const pushEdge = (edge) => {
    if (nodeIds.has(edge.data.source) && nodeIds.has(edge.data.target)) {
      elements.push(edge);
    }
  };

  if (twin.company) {
    (twin.factories || []).forEach((f) =>
      pushEdge({ data: { id: `op-${f.id}`, source: twin.company.id, target: f.id, type: 'OPERATES', routeStatus: 'active' } })
    );
    (twin.warehouses || []).forEach((w) =>
      pushEdge({ data: { id: `op-${w.id}`, source: twin.company.id, target: w.id, type: 'OPERATES', routeStatus: 'active' } })
    );
  }

  (twin.suppliers || []).forEach((s) => {
    if (s.primary_port_id) {
      pushEdge({
        data: { id: `sv-${s.id}`, source: s.id, target: s.primary_port_id, type: 'SUPPLIES' },
      });
    }
  });

  (twin.routes || []).forEach((r) => {
    let routeStatus = 'active';
    if (r.disruption_type === 'BLOCKED') routeStatus = 'blocked';
    else if (r.disruption_type === 'REROUTED') routeStatus = 'rerouted';
    pushEdge({
      data: {
        id: r.id,
        source: r.origin_port_id,
        target: r.destination_port_id,
        type: 'ROUTE_TO',
        routeStatus,
      },
    });
  });

  return elements;
}

export default function DigitalTwinGraph({ twin }) {
  const containerRef = useRef(null);
  const cyRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return undefined;
    cyRef.current = cytoscape({
      container: containerRef.current,
      elements: buildElements(twin),
      style: cytoscapeStylesheet,
      layout: cytoscapeLayout,
      wheelSensitivity: 0.2,
    });
    return () => {
      if (cyRef.current) cyRef.current.destroy();
    };
  }, []);

  useEffect(() => {
    const cy = cyRef.current;
    if (!cy || !twin) return;
    cy.elements().remove();
    cy.add(buildElements(twin));
    cy.layout(cytoscapeLayout).run();
  }, [twin]);

  return (
    <div className="h-full w-full rounded-lg border border-slate-700 bg-slate-800/60">
      <div className="flex items-center justify-between border-b border-slate-700 px-4 py-2">
        <h2 className="text-sm font-semibold text-slate-200">Digital Twin — Supply Network</h2>
        <div className="flex gap-3 text-[10px] text-slate-400">
          <span><span className="mr-1 inline-block h-2 w-2 rounded-full bg-green-600" />available</span>
          <span><span className="mr-1 inline-block h-2 w-2 rounded-full bg-red-600" />disrupted</span>
          <span><span className="mr-1 inline-block h-2 w-2 rounded-full bg-amber-500" />rerouted</span>
        </div>
      </div>
      <div ref={containerRef} className="h-[calc(100%-2.5rem)] w-full" />
    </div>
  );
}
