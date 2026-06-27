"use client";
import { useState } from "react";
import type { GapReport } from "@/lib/types";
import { GapCard } from "./GapCard";
import { ClaimRiskCard } from "./ClaimRiskCard";
import { RecommendationCard } from "./RecommendationCard";
import { NextStepsPanel } from "./NextStepsPanel";
import { formatExtractionFlag } from "@/lib/extractionMessages";

function PortfolioMeter({ gaps }: { gaps: GapReport["gaps"] }) {
  const assessable = gaps.filter(g => g.status !== "not_assessable");
  if (assessable.length === 0) return null;

  const underCount = assessable.filter(g => g.status === "underinsured").length;
  const adequateCount = assessable.filter(g => g.status === "adequate").length;
  const overCount = assessable.filter(g => g.status === "oversold" || g.status === "redundant").length;
  const total = assessable.length;

  // Score 0 = all under, 50 = all adequate, 100 = all over
  const score = (adequateCount * 50 + overCount * 100) / total;
  const markerPct = Math.max(1, Math.min(99, score));

  const markerColor = markerPct < 38 ? "#ef4444" : markerPct > 65 ? "#f59e0b" : "#22c55e";

  return (
    <div className="mt-4 space-y-2">
      <p className="text-xs font-semibold text-sky-200 uppercase tracking-wide">Portfolio protection level</p>
      <div className="relative w-full h-4 rounded-full overflow-visible">
        <div className="absolute inset-0 rounded-full" style={{
          background: "linear-gradient(to right, #fca5a5 0%, #fca5a5 38%, #86efac 38%, #86efac 65%, #fcd34d 65%, #fcd34d 100%)"
        }} />
        <div
          className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 z-10"
          style={{ left: `${markerPct}%` }}
        >
          <div
            className="w-4 h-4 rounded-full border-2 border-white shadow-lg"
            style={{ backgroundColor: markerColor }}
          />
        </div>
      </div>
      <div className="flex justify-between text-[10px] text-sky-300 font-medium">
        <span>Under</span>
        <span>Adequate</span>
        <span>Over</span>
      </div>
      <div className="flex gap-3 text-xs text-sky-200">
        {underCount > 0 && <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-400 inline-block" />{underCount} underprotected</span>}
        {adequateCount > 0 && <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-400 inline-block" />{adequateCount} adequate</span>}
        {overCount > 0 && <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-300 inline-block" />{overCount} over-insured</span>}
      </div>
    </div>
  );
}

interface ReportDashboardProps {
  report: GapReport;
}

type Tab = "gaps" | "risks" | "recommendations" | "next";

export function ReportDashboard({ report }: ReportDashboardProps) {
  const [activeTab, setActiveTab] = useState<Tab>("gaps");

  const highRisks = report.claim_risks.filter(r => r.risk_level === "high");

  const tabs: { id: Tab; label: string; count?: number; urgent?: boolean }[] = [
    { id: "gaps", label: "Coverage gaps", count: report.gaps.filter(g => g.status !== "adequate").length },
    { id: "risks", label: "Claim risks", count: report.claim_risks.length, urgent: highRisks.length > 0 },
    { id: "recommendations", label: "Recommendations", count: report.recommendation.items.length },
    { id: "next", label: "Next steps" },
  ];

  return (
    <div className="space-y-6">
      {/* Summary card */}
      <div className="bg-gradient-to-br from-sky-600 to-sky-800 rounded-2xl p-6 text-white">
        <div className="flex items-center gap-2 mb-3">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          <h2 className="font-semibold">Analysis summary</h2>
        </div>
        <p className="text-sm text-sky-100 leading-relaxed">{report.summary}</p>

        {/* Quick stats */}
        <div className="grid grid-cols-3 gap-3 mt-4">
          <div className="bg-white/10 rounded-xl p-3 text-center">
            <p className="text-2xl font-bold">{report.gaps.filter(g => g.status === "underinsured").length}</p>
            <p className="text-xs text-sky-200 mt-0.5">Underprotected</p>
          </div>
          <div className="bg-white/10 rounded-xl p-3 text-center">
            <p className="text-2xl font-bold">{report.claim_risks.length}</p>
            <p className="text-xs text-sky-200 mt-0.5">Claim risks</p>
          </div>
          <div className="bg-white/10 rounded-xl p-3 text-center">
            <p className="text-2xl font-bold">{report.gaps.filter(g => g.status === "adequate").length}</p>
            <p className="text-xs text-sky-200 mt-0.5">Adequate</p>
          </div>
        </div>

        {/* Portfolio meter */}
        <PortfolioMeter gaps={report.gaps} />

        {/* Extraction flags */}
        {report.extraction_flags.length > 0 && (
          <div className="mt-3 bg-white/10 rounded-xl p-3">
            <p className="text-xs font-semibold text-sky-200 mb-1">Notes from extraction:</p>
            {report.extraction_flags.map((f, i) => (
              <p key={i} className="text-xs text-sky-200">⚠ {formatExtractionFlag(f)}</p>
            ))}
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-slate-100 rounded-xl p-1">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 text-xs font-medium py-2 px-1 rounded-lg transition-colors relative ${
              activeTab === tab.id
                ? "bg-white text-slate-900 shadow-sm"
                : "text-slate-500 hover:text-slate-700"
            }`}
          >
            {tab.label}
            {tab.count !== undefined && tab.count > 0 && (
              <span className={`ml-1 inline-flex items-center justify-center h-4 w-4 rounded-full text-xs font-bold ${
                tab.urgent ? "bg-red-500 text-white" : "bg-slate-200 text-slate-700"
              }`}>
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div>
        {activeTab === "gaps" && (
          <div className="space-y-3">
            {report.gaps.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-8">No coverage data to display.</p>
            ) : (
              report.gaps.map((gap, i) => <GapCard key={i} gap={gap} />)
            )}
          </div>
        )}

        {activeTab === "risks" && (
          <div className="space-y-3">
            {report.claim_risks.length === 0 ? (
              <div className="bg-green-50 border border-green-200 rounded-xl p-6 text-center">
                <p className="text-green-700 font-medium">No significant claim risks identified</p>
                <p className="text-sm text-green-600 mt-1">Based on the clauses in your policies and your profile, no major risk patterns were found.</p>
              </div>
            ) : (
              report.claim_risks.map((risk, i) => <ClaimRiskCard key={i} risk={risk} index={i} />)
            )}
          </div>
        )}

        {activeTab === "recommendations" && (
          <RecommendationCard recommendation={report.recommendation} />
        )}

        {activeTab === "next" && (
          <NextStepsPanel steps={report.next_steps} disclaimers={report.disclaimers} />
        )}
      </div>
    </div>
  );
}
