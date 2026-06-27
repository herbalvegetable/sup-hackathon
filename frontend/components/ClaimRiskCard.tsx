import type { ClaimRisk } from "@/lib/types";
import clsx from "clsx";

interface ClaimRiskCardProps {
  risk: ClaimRisk;
  index: number;
}

const riskConfig = {
  high: {
    badge: "bg-red-600 text-white",
    border: "border-red-200",
    bg: "bg-red-50",
  },
  medium: {
    badge: "bg-amber-500 text-white",
    border: "border-amber-200",
    bg: "bg-amber-50",
  },
  low: {
    badge: "bg-slate-400 text-white",
    border: "border-slate-200",
    bg: "bg-slate-50",
  },
};

export function ClaimRiskCard({ risk }: ClaimRiskCardProps) {
  const cfg = riskConfig[risk.risk_level];

  return (
    <div className={clsx("rounded-xl border p-4 space-y-3", cfg.bg, cfg.border)}>
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-xs text-slate-500 mb-1">
            {risk.source_filename}{risk.insurer ? ` · ${risk.insurer}` : ""}
            {risk.clause_page ? ` · Page ${risk.clause_page}` : ""}
          </p>
          <span className={clsx("text-xs font-bold px-2 py-0.5 rounded-full uppercase tracking-wide", cfg.badge)}>
            {risk.risk_level} risk
          </span>
        </div>
      </div>

      {/* Verbatim clause */}
      <div className="bg-white/80 rounded-lg px-3 py-2 border border-slate-200 text-xs text-slate-700 italic leading-relaxed">
        &ldquo;{risk.clause_text}&rdquo;
      </div>

      {/* Plain English */}
      <div className="space-y-1">
        <p className="text-xs font-semibold text-slate-600 uppercase tracking-wide">What this means</p>
        <p className="text-sm text-slate-700">{risk.plain_english_meaning}</p>
      </div>

      {/* Why it affects you */}
      <div className="space-y-1">
        <p className="text-xs font-semibold text-slate-600 uppercase tracking-wide">Why this may affect you</p>
        <p className="text-sm text-slate-700">{risk.reason}</p>
        <p className="text-xs text-slate-500">Triggered by: <span className="font-medium">{risk.matched_data_point}</span></p>
      </div>

      {/* What to do */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg px-3 py-2.5 space-y-1">
        <p className="text-xs font-semibold text-blue-700 uppercase tracking-wide">What you should do</p>
        <p className="text-sm text-blue-800">{risk.recommendation}</p>
      </div>
    </div>
  );
}
