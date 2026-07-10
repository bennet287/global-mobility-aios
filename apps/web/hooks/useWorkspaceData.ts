"use client";

import { useCallback, useEffect, useState } from "react";
import {
  AgentReviewDashboard,
  ApplicationQueue,
  DashboardSummary,
  DocumentVerificationQueue,
  getAgentReviewDashboard,
  getApplicationQueue,
  getDashboardSummary,
  getDocumentVerificationQueue,
  getTruthResolutionQueue,
  OptionalData,
  TruthResolutionQueue,
} from "../lib/api";

export type LoadStatus = "idle" | "loading" | "ready" | "partial" | "offline";

const emptySummary: DashboardSummary = {
  leads_total: 0,
  leads_new: 0,
  leads_human_review: 0,
  leads_converted: 0,
  truth_queue_pending: 0,
  truth_queue_resolved: 0,
  recent_leads: [],
  recent_truth_audits: [],
};

export function useWorkspaceData(backendOnline: boolean) {
  const [summary, setSummary] = useState<DashboardSummary>(emptySummary);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [truthQueue, setTruthQueue] = useState<OptionalData<TruthResolutionQueue>>({ data: null, error: null });
  const [applicationQueue, setApplicationQueue] = useState<OptionalData<ApplicationQueue>>({ data: null, error: null });
  const [documentQueue, setDocumentQueue] = useState<OptionalData<DocumentVerificationQueue>>({ data: null, error: null });
  const [agentDashboard, setAgentDashboard] = useState<OptionalData<AgentReviewDashboard>>({ data: null, error: null });
  const [loadStatus, setLoadStatus] = useState<LoadStatus>("idle");

  const load = useCallback(async () => {
    setLoadStatus("loading");
    setSummaryError(null);

    const [summaryResult, truthData, applicationData, documentData, agentData] = await Promise.all([
      getDashboardSummary()
        .then((data) => ({ data, error: null }))
        .catch((err) => ({ data: emptySummary, error: err instanceof Error ? err.message : "Failed to load CRM summary" })),
      getTruthResolutionQueue(),
      getApplicationQueue(),
      getDocumentVerificationQueue(),
      getAgentReviewDashboard(),
    ]);

    setSummary(summaryResult.data);
    setSummaryError(summaryResult.error);
    setTruthQueue(truthData);
    setApplicationQueue(applicationData);
    setDocumentQueue(documentData);
    setAgentDashboard(agentData);

    const errors = [summaryResult.error, truthData.error, applicationData.error, documentData.error, agentData.error].filter(Boolean);
    if (!backendOnline) {
      setLoadStatus("offline");
    } else if (errors.length === 0) {
      setLoadStatus("ready");
    } else {
      setLoadStatus("partial");
    }
  }, [backendOnline]);

  useEffect(() => {
    void load();
  }, [load]);

  return {
    summary,
    summaryError,
    truthQueue,
    applicationQueue,
    documentQueue,
    agentDashboard,
    loadStatus,
    load,
  };
}
