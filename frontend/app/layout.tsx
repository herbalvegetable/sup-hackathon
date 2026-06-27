import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "InsureSight",
  description: "Analyse your Singapore insurance policies for coverage gaps, over-insurance, and claim risks.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50">
        <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
          <div className="max-w-2xl mx-auto px-4 py-3 flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-sky-600 flex items-center justify-center flex-shrink-0">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <div>
              <p className="font-semibold text-slate-900 text-sm leading-tight">InsureSight</p>
              <p className="text-xs text-slate-500">Singapore coverage gap analysis · Not financial advice</p>
            </div>
          </div>
        </header>
        <main className="max-w-2xl mx-auto px-4 py-6">
          {children}
        </main>
        <footer className="max-w-2xl mx-auto px-4 py-6 text-xs text-slate-400 text-center border-t border-slate-200 mt-8 space-y-1">
          <p>Educational gap analysis only · Not a licensed financial advisory service</p>
          <p>
            <a href="https://eservices.mas.gov.sg/rr" target="_blank" rel="noopener noreferrer" className="underline hover:text-slate-600">Find a MAS-licensed adviser</a>
            <span className="mx-2">·</span>
            <a href="mailto:insuresight@gmail.com" className="underline hover:text-slate-600">insuresight@gmail.com</a>
          </p>
          <p>© {new Date().getFullYear()} InsureSight. All rights reserved.</p>
        </footer>
      </body>
    </html>
  );
}
