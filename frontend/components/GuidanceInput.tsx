"use client";
import { useState } from "react";
import type { GuidanceAnswers } from "@/lib/types";

interface GuidanceInputProps {
  onChange: (answers: GuidanceAnswers) => void;
  answers: GuidanceAnswers;
}

export function GuidanceInput({ onChange, answers }: GuidanceInputProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <div className="h-6 w-6 rounded-full bg-sky-600 text-white flex items-center justify-center text-xs font-bold flex-shrink-0">?</div>
        <h3 className="font-semibold text-slate-800">Optional: Tell us what you care about most</h3>
      </div>
      <p className="text-sm text-slate-500">Answer these three quick questions to personalise the analysis. All are optional.</p>

      {/* Q1 */}
      <div className="space-y-2">
        <label className="label">Are you the main income earner for your household?</label>
        <div className="flex gap-2 flex-wrap">
          {["Yes, primarily", "Shared with partner", "No"].map(option => (
            <button
              key={option}
              type="button"
              onClick={() => onChange({ ...answers, q1_income_earner: option })}
              className={`px-4 py-2 rounded-xl text-sm font-medium border transition-colors ${
                answers.q1_income_earner === option
                  ? "bg-sky-600 text-white border-sky-600"
                  : "bg-white text-slate-700 border-slate-300 hover:border-sky-400"
              }`}
            >
              {option}
            </button>
          ))}
        </div>
      </div>

      {/* Q2 */}
      <div>
        <label className="label">Is there a condition in your family history you're particularly concerned about? <span className="text-slate-400 font-normal">(optional)</span></label>
        <input
          type="text"
          className="input"
          placeholder="e.g. heart disease, cancer, diabetes"
          value={answers.q2_family_history || ""}
          onChange={e => onChange({ ...answers, q2_family_history: e.target.value })}
        />
      </div>

      {/* Q3 */}
      <div>
        <label className="label">Do you have a specific coverage goal in mind? <span className="text-slate-400 font-normal">(optional)</span></label>
        <input
          type="text"
          className="input"
          placeholder="e.g. I want enough to pay off my mortgage if I can't work"
          value={answers.q3_coverage_goal || ""}
          onChange={e => onChange({ ...answers, q3_coverage_goal: e.target.value })}
        />
      </div>

      {/* Advanced expander */}
      <button
        type="button"
        className="text-xs text-slate-500 underline underline-offset-2 hover:text-sky-600 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? "Hide advanced options" : "Advanced: specify exact coverage targets"}
      </button>
      {expanded && (
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-sm text-slate-600">
          Advanced targeting is coming in a future version. For now, your answers above and the profile form are used to personalise the benchmark analysis.
        </div>
      )}
    </div>
  );
}
