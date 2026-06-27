import type { ReportGap } from "@/lib/types";
import { GlossaryTooltip } from "./GlossaryTooltip";
import { CoverageSlider } from "./CoverageSlider";
import clsx from "clsx";

interface GapCardProps {
  gap: ReportGap;
}

const statusConfig = {
  adequate: {
    label: "Adequate",
    bg: "bg-green-50",
    border: "border-green-200",
    badge: "bg-green-100 text-green-800",
    icon: "✓",
    iconColor: "text-green-600",
  },
  underinsured: {
    label: "Underprotected",
    bg: "bg-red-50",
    border: "border-red-200",
    badge: "bg-red-100 text-red-800",
    icon: "↓",
    iconColor: "text-red-600",
  },
  oversold: {
    label: "Possibly over-insured",
    bg: "bg-amber-50",
    border: "border-amber-200",
    badge: "bg-amber-100 text-amber-800",
    icon: "↑",
    iconColor: "text-amber-600",
  },
  redundant: {
    label: "Redundant coverage",
    bg: "bg-amber-50",
    border: "border-amber-200",
    badge: "bg-amber-100 text-amber-800",
    icon: "⊕",
    iconColor: "text-amber-600",
  },
  not_assessable: {
    label: "Not assessable",
    bg: "bg-slate-50",
    border: "border-slate-200",
    badge: "bg-slate-100 text-slate-600",
    icon: "?",
    iconColor: "text-slate-400",
  },
};

const priorityBadge = {
  urgent: "bg-red-600 text-white",
  high: "bg-orange-100 text-orange-800",
  medium: "bg-yellow-100 text-yellow-800",
  low: "bg-slate-100 text-slate-600",
};

const categoryLabels: Record<string, string> = {
  life: "Life / Death Benefit",
  critical_illness: "Critical Illness",
  early_critical_illness: "Early Critical Illness",
  tpd: "Total Permanent Disability",
  hospital: "Hospitalisation",
  disability_income: "Disability Income",
  careshield_life: "CareShield Life",
  personal_accident: "Personal Accident",
};

const categoryGlossaryTerms: Record<string, string> = {
  critical_illness: "Critical Illness",
  early_critical_illness: "Early Critical Illness",
  tpd: "TPD",
  hospital: "Integrated Shield Plan",
  disability_income: "Disability Income",
};

export function GapCard({ gap }: GapCardProps) {
  const cfg = statusConfig[gap.status];
  const label = categoryLabels[gap.category] || gap.category;
  const glossaryTerm = categoryGlossaryTerms[gap.category];

  return (
    <div className={clsx("rounded-xl border p-4 space-y-3", cfg.bg, cfg.border)}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className={clsx("text-lg font-bold", cfg.iconColor)}>{cfg.icon}</span>
          <h3 className="font-semibold text-slate-800 text-sm">
            {glossaryTerm ? (
              <GlossaryTooltip term={glossaryTerm}>{label}</GlossaryTooltip>
            ) : label}
          </h3>
        </div>
        <div className="flex gap-1.5 flex-shrink-0">
          {gap.status !== "adequate" && gap.status !== "not_assessable" && (
            <span className={clsx("text-xs font-semibold px-2 py-0.5 rounded-full capitalize", priorityBadge[gap.priority])}>
              {gap.priority}
            </span>
          )}
          <span className={clsx("text-xs font-semibold px-2 py-0.5 rounded-full", cfg.badge)}>
            {cfg.label}
          </span>
        </div>
      </div>

      {/* Coverage numbers */}
      {(gap.you_have !== undefined || gap.recommended_low !== undefined) && (
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-xs text-slate-500 mb-0.5">You have</p>
            <p className="font-semibold text-slate-800">
              {gap.you_have != null ? `$${gap.you_have.toLocaleString()}` : "—"}
            </p>
          </div>
          {gap.recommended_low != null && (
            <div>
              <p className="text-xs text-slate-500 mb-0.5">Recommended</p>
              <p className="font-semibold text-slate-800">
                ${gap.recommended_low.toLocaleString()}
                {gap.recommended_high && gap.recommended_high !== gap.recommended_low
                  ? `–$${gap.recommended_high.toLocaleString()}`
                  : ""}
              </p>
            </div>
          )}
          {gap.gap_low != null && gap.status === "underinsured" && (
            <div className="col-span-2">
              <p className="text-xs text-slate-500 mb-0.5">Coverage gap</p>
              <p className="font-semibold text-red-700">
                −${gap.gap_low.toLocaleString()}
                {gap.gap_high && gap.gap_high !== gap.gap_low
                  ? ` to −$${gap.gap_high.toLocaleString()}`
                  : ""}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Coverage slider */}
      {gap.recommended_low != null && gap.recommended_high != null && gap.status !== "not_assessable" && (
        <div className="pt-1 pb-2">
          <CoverageSlider
            youHave={gap.you_have}
            recommendedLow={gap.recommended_low}
            recommendedHigh={gap.recommended_high}
            status={gap.status}
          />
        </div>
      )}

      {/* Explanation */}
      <p className="text-sm text-slate-700 leading-relaxed">{gap.explanation}</p>

      {/* Citation */}
      {gap.citation && (
        <div className="text-xs text-slate-500 bg-white/60 rounded-lg px-3 py-2 border border-slate-200">
          <p className="font-medium text-slate-600 mb-0.5">Source: {gap.citation.source_document.replace(/_/g, " ")}</p>
          <p className="italic">&ldquo;{gap.citation.chunk_text}&rdquo;</p>
        </div>
      )}
    </div>
  );
}
