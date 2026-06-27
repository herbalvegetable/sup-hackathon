"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import type { GapReport } from "@/lib/types";
import { ReportDashboard } from "@/components/ReportDashboard";

export default function ReportPage() {
  const router = useRouter();
  const [report, setReport] = useState<GapReport | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const raw = sessionStorage.getItem("gap_report");
    if (!raw) {
      setError("No report found. Please upload your policies and complete the analysis first.");
      return;
    }
    try {
      setReport(JSON.parse(raw));
    } catch {
      setError("Could not load report. Please try again.");
    }
  }, []);

  if (error) {
    return (
      <div className="space-y-4">
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-800">
          {error}
        </div>
        <button
          onClick={() => router.push("/")}
          className="text-sky-600 text-sm underline"
        >
          Start a new analysis
        </button>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 rounded-full border-4 border-sky-500 border-t-transparent animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-slate-900">Your coverage report</h1>
        <button
          onClick={() => {
            sessionStorage.removeItem("gap_report");
            router.push("/");
          }}
          className="text-xs text-slate-500 hover:text-slate-700 underline"
        >
          Start new analysis
        </button>
      </div>
      <ReportDashboard report={report} />
    </div>
  );
}
