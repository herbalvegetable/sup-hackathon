"use client";
import { useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { PrivacyNotice } from "@/components/PrivacyNotice";
import { UploadZone } from "@/components/UploadZone";
import { PolicyStatusList } from "@/components/PolicyStatusList";
import { ProfileForm } from "@/components/ProfileForm";
import { GuidanceInput } from "@/components/GuidanceInput";
import type { PolicyFileState, UserProfile, GuidanceAnswers, GuidanceBrief } from "@/lib/types";
import { uploadPolicies, analyzePortfolio, normalizeGuidance, getErrorMessage } from "@/lib/api";
import { formatExtractionFlag } from "@/lib/extractionMessages";

type Step = "upload" | "profile" | "analyzing";

export default function Home() {
  const router = useRouter();
  const [privacyAccepted, setPrivacyAccepted] = useState(false);
  const [step, setStep] = useState<Step>("upload");
  const [files, setFiles] = useState<PolicyFileState[]>([]);
  const [sessionId, setSessionId] = useState<string>("");
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string>("");
  const [guidanceAnswers, setGuidanceAnswers] = useState<GuidanceAnswers>({});
  const [addingMore, setAddingMore] = useState(false);
  const [addMoreUploading, setAddMoreUploading] = useState(false);
  // Keep references to previously uploaded File objects so we can re-upload all together
  const cachedFiles = useRef<File[]>([]);

  const handleFiles = useCallback(async (newFiles: File[]) => {
    setError("");
    setFiles(newFiles.map(f => ({ file: f, status: "uploading" })));
    setUploading(true);

    try {
      const result = await uploadPolicies(newFiles);
      setSessionId(result.session_id);

      setFiles(newFiles.map((f) => {
        const policy = result.policies.find(p => p.source_filename === f.name);
        const flag = result.extraction_flags?.find(fl => fl.startsWith(f.name));
        return {
          file: f,
          status: policy ? "done" : "failed",
          policy,
          error: !policy ? (flag ? formatExtractionFlag(flag) : "We couldn't extract data from this file. Please try a digital PDF from your insurer.") : undefined,
        };
      }));

      // Cache file objects for potential re-upload
      cachedFiles.current = newFiles;

      const anySuccess = result.policies.length > 0;
      if (anySuccess) {
        setStep("profile");
      } else {
        const flagMessages = result.extraction_flags?.map(formatExtractionFlag).join(" ") || "";
        setError(
          flagMessages
            ? `We couldn't extract any policies. ${flagMessages}`
            : "No policies could be extracted. Please check that your PDFs are digital (not scanned) and try again."
        );
      }
    } catch (e) {
      setError(getErrorMessage(e));
      setFiles(f => f.map(pf => ({ ...pf, status: "failed", error: "Upload failed" })));
    } finally {
      setUploading(false);
    }
  }, []);

  const handleAddMoreFiles = useCallback(async (additionalFiles: File[]) => {
    setError("");
    setAddMoreUploading(true);

    // Combine previously uploaded files with the new ones (deduplicate by name)
    const existingNames = new Set(cachedFiles.current.map(f => f.name));
    const deduped = additionalFiles.filter(f => !existingNames.has(f.name));
    const allFiles = [...cachedFiles.current, ...deduped];

    // Mark new files as uploading
    const addedStates: PolicyFileState[] = deduped.map(f => ({ file: f, status: "uploading" }));
    setFiles(prev => [...prev, ...addedStates]);

    try {
      const result = await uploadPolicies(allFiles);
      setSessionId(result.session_id);
      cachedFiles.current = allFiles;

      setFiles(allFiles.map((f) => {
        const policy = result.policies.find(p => p.source_filename === f.name);
        const flag = result.extraction_flags?.find(fl => fl.startsWith(f.name));
        return {
          file: f,
          status: policy ? "done" : "failed",
          policy,
          error: !policy ? (flag ? formatExtractionFlag(flag) : "We couldn't extract data from this file. Please try a digital PDF from your insurer.") : undefined,
        };
      }));

      if (result.policies.length === 0) {
        setError("Could not extract any policies from the new files. Your existing policies are still loaded.");
      } else {
        setAddingMore(false);
      }
    } catch (e) {
      setError(getErrorMessage(e));
    } finally {
      setAddMoreUploading(false);
    }
  }, []);

  const handleProfileSubmit = useCallback(async (profile: UserProfile) => {
    setError("");
    setAnalyzing(true);
    setStep("analyzing");

    try {
      let guidance: GuidanceBrief | undefined;
      const hasGuidance = guidanceAnswers.q1_income_earner ||
        guidanceAnswers.q2_family_history || guidanceAnswers.q3_coverage_goal;

      if (hasGuidance) {
        try {
          guidance = await normalizeGuidance(guidanceAnswers);
        } catch {
          // Guidance normalisation failed — continue without it
        }
      }

      const report = await analyzePortfolio(sessionId, profile, guidance);

      // Store report in sessionStorage for the report page
      sessionStorage.setItem("gap_report", JSON.stringify(report));
      router.push("/report");
    } catch (e) {
      setError(getErrorMessage(e));
      setStep("profile");
    } finally {
      setAnalyzing(false);
    }
  }, [sessionId, guidanceAnswers, router]);

  if (!privacyAccepted) {
    return <PrivacyNotice onAccept={() => setPrivacyAccepted(true)} />;
  }

  return (
    <div className="space-y-6">
      {/* Step indicator */}
      <div className="flex items-center gap-2">
        {[
          { id: "upload", label: "Upload policies" },
          { id: "profile", label: "Your profile" },
          { id: "analyzing", label: "Analysis" },
        ].map((s, i) => {
          const isActive = s.id === step;
          const isDone = (step === "profile" && s.id === "upload") ||
            (step === "analyzing" && (s.id === "upload" || s.id === "profile"));
          return (
            <div key={s.id} className="flex items-center gap-2">
              {i > 0 && <div className="h-px w-6 bg-slate-300" />}
              <div className={`flex items-center gap-1.5 text-xs font-medium ${
                isActive ? "text-sky-700" : isDone ? "text-green-700" : "text-slate-400"
              }`}>
                <div className={`h-5 w-5 rounded-full flex items-center justify-center text-xs font-bold ${
                  isActive ? "bg-sky-600 text-white" : isDone ? "bg-green-500 text-white" : "bg-slate-200 text-slate-500"
                }`}>
                  {isDone ? "✓" : i + 1}
                </div>
                <span className="hidden sm:block">{s.label}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Error display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-800">
          {error}
        </div>
      )}

      {/* Upload step */}
      {step === "upload" && (
        <div className="space-y-6">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 mb-1">Check your insurance coverage</h1>
            <p className="text-slate-500 text-sm">Upload your Singapore insurance policy PDFs to find out if you are under or over-insured, and flag any clauses that could affect your claims.</p>
          </div>
          <UploadZone onFiles={handleFiles} disabled={uploading} />
          {files.length > 0 && <PolicyStatusList files={files} />}
        </div>
      )}

      {/* Profile step */}
      {step === "profile" && (
        <div className="space-y-6">
          <div>
            <h2 className="text-xl font-bold text-slate-900 mb-1">Tell us about yourself</h2>
            <p className="text-slate-500 text-sm">This information is used to calculate personalised coverage recommendations. It is never stored.</p>
          </div>

          <PolicyStatusList files={files} />

          {/* Add more policies */}
          {!addingMore ? (
            <button
              onClick={() => setAddingMore(true)}
              className="w-full flex items-center justify-center gap-2 border border-dashed border-slate-300 rounded-xl py-3 text-sm text-slate-500 hover:text-sky-600 hover:border-sky-400 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Add more policies
            </button>
          ) : (
            <div className="border border-slate-200 rounded-2xl p-4 space-y-3 bg-slate-50">
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold text-slate-700">Add more policy PDFs</p>
                <button
                  onClick={() => setAddingMore(false)}
                  className="text-xs text-slate-400 hover:text-slate-600"
                >
                  Cancel
                </button>
              </div>
              <UploadZone onFiles={handleAddMoreFiles} disabled={addMoreUploading} />
              {addMoreUploading && (
                <p className="text-xs text-slate-500 text-center">Uploading and extracting new policies…</p>
              )}
            </div>
          )}

          <div className="bg-white rounded-2xl border border-slate-200 p-5">
            <GuidanceInput answers={guidanceAnswers} onChange={setGuidanceAnswers} />
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 p-5">
            <h3 className="font-semibold text-slate-800 mb-4">Your profile</h3>
            <ProfileForm onSubmit={handleProfileSubmit} loading={analyzing} />
          </div>
        </div>
      )}

      {/* Analyzing step */}
      {step === "analyzing" && (
        <div className="flex flex-col items-center justify-center py-20 space-y-4">
          <div className="h-16 w-16 rounded-full border-4 border-sky-500 border-t-transparent animate-spin" />
          <h2 className="text-xl font-semibold text-slate-800">Analysing your portfolio…</h2>
          <div className="text-sm text-slate-500 text-center space-y-1">
            <p>Reading your policy documents</p>
            <p>Comparing against Singapore benchmarks</p>
            <p>Checking for claim risk clauses</p>
            <p>Generating your personalised report</p>
          </div>
          <p className="text-xs text-slate-400 mt-4">This may take 30–60 seconds depending on the number of policies.</p>
        </div>
      )}
    </div>
  );
}
