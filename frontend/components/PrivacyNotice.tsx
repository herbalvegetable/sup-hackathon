"use client";
import { useState } from "react";

interface PrivacyNoticeProps {
  onAccept: () => void;
}

export function PrivacyNotice({ onAccept }: PrivacyNoticeProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="h-10 w-10 rounded-full bg-sky-100 flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5 text-sky-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Before you upload</h2>
            <p className="text-sm text-slate-500">Privacy notice (PDPA)</p>
          </div>
        </div>

        <div className="space-y-3 text-sm text-slate-700">
          <p>This tool processes your insurance documents to identify coverage gaps. Here is how your data is handled:</p>
          <ul className="space-y-2">
            {[
              "Your PDFs and profile inputs are processed in-memory only — nothing is saved to a database or disk.",
              "Uploaded PDFs are deleted from memory immediately after text extraction.",
              "Your session expires automatically after 30 minutes.",
              "No third-party analytics scripts are loaded on this page.",
            ].map((item, i) => (
              <li key={i} className="flex items-start gap-2">
                <svg className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                {item}
              </li>
            ))}
          </ul>

          <button
            className="text-sky-600 text-xs underline"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? "Show less" : "What data is collected?"}
          </button>

          {expanded && (
            <div className="bg-slate-50 rounded-lg p-3 text-xs text-slate-600 space-y-1">
              <p><strong>Collected:</strong> Insurance policy PDF text, age, income, citizenship status, medical history you enter.</p>
              <p><strong>Not collected:</strong> Name, NRIC, email, or any identifying information not in the PDF.</p>
              <p><strong>Data queries:</strong> Contact us at <a href="mailto:insuresight@gmail.com" className="underline text-sky-600">insuresight@gmail.com</a></p>
            </div>
          )}
        </div>

        <div className="mt-5 flex gap-3">
          <button
            onClick={onAccept}
            className="flex-1 bg-sky-600 hover:bg-sky-700 text-white font-semibold py-2.5 px-4 rounded-xl transition-colors"
          >
            I understand — continue
          </button>
        </div>

        <p className="mt-3 text-xs text-center text-slate-400">
          By continuing, you consent to in-memory processing of your documents.
        </p>
      </div>
    </div>
  );
}
