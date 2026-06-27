import type { RecommendationResult } from "@/lib/types";
import { GlossaryTooltip } from "./GlossaryTooltip";

interface RecommendationCardProps {
  recommendation: RecommendationResult;
}

const actionConfig = {
  add_base: {
    label: "Add coverage",
    icon: "＋",
    color: "text-sky-700 bg-sky-100",
  },
  add_rider: {
    label: "Add a rider",
    icon: "＋",
    color: "text-indigo-700 bg-indigo-100",
  },
  increase: {
    label: "Increase coverage",
    icon: "↑",
    color: "text-amber-700 bg-amber-100",
  },
  reduce: {
    label: "Consider reducing",
    icon: "↓",
    color: "text-green-700 bg-green-100",
  },
};

const genericTypeLabels: Record<string, { label: string; glossaryTerm?: string }> = {
  term_life: { label: "Term life policy", glossaryTerm: undefined },
  whole_life: { label: "Whole life policy", glossaryTerm: undefined },
  critical_illness: { label: "Critical Illness cover", glossaryTerm: "Critical Illness" },
  early_ci: { label: "Early Critical Illness cover", glossaryTerm: "Early Critical Illness" },
  tpd: { label: "Total Permanent Disability cover", glossaryTerm: "TPD" },
  hospital_plan: { label: "Integrated Shield Plan", glossaryTerm: "Integrated Shield Plan" },
  hospital_rider: { label: "IP rider", glossaryTerm: "IP" },
  disability_income: { label: "Disability income policy", glossaryTerm: undefined },
  careshield_supplement: { label: "CareShield Life supplement", glossaryTerm: "CareShield Life" },
  personal_accident: { label: "Personal accident plan", glossaryTerm: undefined },
};

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 bg-slate-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-sky-500 rounded-full"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-slate-400">{pct}% confidence</span>
    </div>
  );
}

export function RecommendationCard({ recommendation }: RecommendationCardProps) {
  if (recommendation.items.length === 0 && !recommendation.premium_burden_warning) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-xl p-4 text-sm text-green-800">
        Your coverage appears well-balanced. No structural changes are recommended at this time.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Premium burden warning */}
      {recommendation.premium_burden_warning && (
        <div className="bg-amber-50 border border-amber-300 rounded-xl px-4 py-3 text-sm text-amber-900">
          <p className="font-semibold mb-1">⚠ Premium burden warning</p>
          <p>{recommendation.premium_burden_warning}</p>
        </div>
      )}

      {/* Recommendation items */}
      {recommendation.items.map((item, i) => {
        const action = actionConfig[item.action];
        const typeInfo = genericTypeLabels[item.generic_type];
        const label = typeInfo?.label || item.generic_type.replace(/_/g, " ");

        return (
          <div key={i} className="bg-white border border-slate-200 rounded-xl p-4 space-y-3">
            <div className="flex items-start gap-3">
              <span className={`text-sm font-bold px-2 py-1 rounded-lg ${action.color}`}>
                {action.icon} {action.label}
              </span>
            </div>
            <div>
              <p className="font-semibold text-slate-800 text-sm">
                {typeInfo?.glossaryTerm ? (
                  <GlossaryTooltip term={typeInfo.glossaryTerm}>{label}</GlossaryTooltip>
                ) : label}
              </p>
              <p className="text-sm text-slate-600 mt-1">{item.reason}</p>
            </div>
            <ConfidenceBar value={item.confidence} />
          </div>
        );
      })}

      {/* Notes */}
      {recommendation.notes.map((note, i) => (
        <p key={i} className="text-xs text-slate-500 italic">{note}</p>
      ))}
    </div>
  );
}
