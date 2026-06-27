"use client";
import type { PolicyFileState } from "@/lib/types";
import clsx from "clsx";

interface PolicyStatusListProps {
  files: PolicyFileState[];
}

const statusConfig = {
  queued: {
    label: "Queued",
    icon: (
      <div className="h-5 w-5 rounded-full border-2 border-slate-300" />
    ),
    color: "text-slate-500",
  },
  uploading: {
    label: "Uploading…",
    icon: (
      <div className="h-5 w-5 rounded-full border-2 border-sky-500 border-t-transparent animate-spin" />
    ),
    color: "text-sky-600",
  },
  extracting: {
    label: "Reading policy…",
    icon: (
      <div className="h-5 w-5 rounded-full border-2 border-sky-500 border-t-transparent animate-spin" />
    ),
    color: "text-sky-600",
  },
  done: {
    label: "Done",
    icon: (
      <div className="h-5 w-5 rounded-full bg-green-500 flex items-center justify-center">
        <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
        </svg>
      </div>
    ),
    color: "text-green-700",
  },
  failed: {
    label: "Failed",
    icon: (
      <div className="h-5 w-5 rounded-full bg-red-500 flex items-center justify-center">
        <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </div>
    ),
    color: "text-red-700",
  },
};

function policyTypeLabel(type: string): string {
  const map: Record<string, string> = {
    whole_life: "Whole Life",
    term: "Term Life",
    critical_illness: "Critical Illness",
    early_critical_illness: "Early CI",
    hospital: "Hospitalisation / IP",
    disability: "Disability Income",
    careshield_supplement: "CareShield Supplement",
    personal_accident: "Personal Accident",
    unknown: "Unknown type",
  };
  return map[type] || type;
}

export function PolicyStatusList({ files }: PolicyStatusListProps) {
  if (files.length === 0) return null;

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-slate-700">Uploaded policies</h3>
      <div className="divide-y divide-slate-100 rounded-xl border border-slate-200 overflow-hidden">
        {files.map((f, i) => {
          const cfg = statusConfig[f.status];
          return (
            <div key={i} className="flex items-center gap-3 px-4 py-3 bg-white">
              {cfg.icon}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-800 truncate">{f.file.name}</p>
                {f.status === "done" && f.policy && (
                  <p className="text-xs text-slate-500">
                    {f.policy.insurer ? `${f.policy.insurer} · ` : ""}
                    {policyTypeLabel(f.policy.policy_type)}
                    {f.policy.sum_assured ? ` · $${f.policy.sum_assured.toLocaleString()}` : ""}
                  </p>
                )}
                {f.status === "failed" && f.error && (
                  <p className="text-xs text-red-600">{f.error}</p>
                )}
              </div>
              <span className={clsx("text-xs font-medium", cfg.color)}>{cfg.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
