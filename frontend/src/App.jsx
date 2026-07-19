import React, { useCallback, useEffect, useState } from 'react';
import AgentTracePanel from './components/AgentTracePanel';
import DigitalTwinGraph from './components/DigitalTwinGraph';
import DisruptionEventBadge from './components/DisruptionEventBadge';
import EvidenceChainCard from './components/EvidenceChainCard';
import HITLModal from './components/HITLModal';
import InventoryStatusBar from './components/InventoryStatusBar';
import LiveSearchInput from './components/LiveSearchInput';
import ScenarioSelector from './components/ScenarioSelector';
import useAgentStream from './hooks/useAgentStream';
import useDigitalTwin from './hooks/useDigitalTwin';
import { fetchScenarios, submitDecision, triggerScenario } from './lib/api';

export default function App() {
  const [scenarios, setScenarios] = useState([]);
  const [activeScenarioId, setActiveScenarioId] = useState(null);
  const [sessionId, setSessionId] = useState(null);

  const { twin, refresh } = useDigitalTwin();
  const { messages, isStreaming, isHITLRequired, finalRecommendation, clearHITL } =
    useAgentStream(sessionId);

  useEffect(() => {
    fetchScenarios().then(setScenarios).catch(() => setScenarios([]));
  }, []);

  const handleScenarioSelect = useCallback(async (scenarioId) => {
    const newSessionId = `session-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    setActiveScenarioId(scenarioId);
    await triggerScenario(scenarioId, newSessionId);
    setSessionId(newSessionId);
  }, []);

  const handleLiveSearchStarted = useCallback((newSessionId) => {
    setActiveScenarioId(null);
    setSessionId(newSessionId);
  }, []);

  const handleDecision = useCallback(
    async (decision, notes) => {
      if (!sessionId) return;
      await submitDecision(sessionId, decision, notes);
      clearHITL();
      refresh();
    },
    [sessionId, clearHITL, refresh]
  );

  return (
    <div className="flex min-h-screen flex-col gap-3 bg-slate-900 p-4">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-bold text-white">
            SupplyChainAI Control Tower
            <span className="ml-2 text-xs font-normal text-slate-400">
              Orbital Manufacturing Pte Ltd · Singapore
            </span>
          </h1>
          <ScenarioSelector
            scenarios={scenarios}
            activeScenarioId={activeScenarioId}
            disabled={isStreaming}
            onSelect={handleScenarioSelect}
          />
          <div className="mt-2">
            <LiveSearchInput disabled={isStreaming} onStarted={handleLiveSearchStarted} />
          </div>
        </div>
        <DisruptionEventBadge events={twin?.events} />
      </header>

      <main className="grid flex-1 grid-cols-1 gap-3 lg:grid-cols-2">
        <div className="min-h-[420px] lg:min-h-[560px]">
          <DigitalTwinGraph twin={twin} />
        </div>
        <div className="flex flex-col gap-3">
          <div className="min-h-[280px] flex-1">
            <AgentTracePanel messages={messages} isStreaming={isStreaming} />
          </div>
          <EvidenceChainCard recommendation={finalRecommendation} />
        </div>
      </main>

      <InventoryStatusBar materials={twin?.materials} />

      <HITLModal
        open={isHITLRequired}
        recommendation={finalRecommendation}
        onDecision={handleDecision}
      />
    </div>
  );
}
