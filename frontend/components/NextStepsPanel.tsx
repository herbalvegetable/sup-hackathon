interface NextStepsPanelProps {
  steps: string[];
  disclaimers: string[];
}

export function NextStepsPanel({ steps, disclaimers }: NextStepsPanelProps) {
  return (
    <div className="space-y-4">
      {/* Next steps */}
      <div className="bg-sky-50 border border-sky-200 rounded-xl p-4 space-y-2">
        <h3 className="font-semibold text-sky-900 text-sm">Recommended next steps</h3>
        <ol className="space-y-2">
          {steps.map((step, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-sky-800">
              <span className="h-5 w-5 rounded-full bg-sky-200 text-sky-800 text-xs flex items-center justify-center font-bold flex-shrink-0 mt-0.5">
                {i + 1}
              </span>
              {step.startsWith("http") ? (
                <a href={step} target="_blank" rel="noopener noreferrer" className="underline hover:text-sky-600">
                  {step}
                </a>
              ) : (
                <span>{step}</span>
              )}
            </li>
          ))}
        </ol>
      </div>

      {/* Disclaimers */}
      <div className="space-y-2">
        {disclaimers.map((d, i) => (
          <p key={i} className="text-xs text-slate-500 leading-relaxed">
            {d.includes("https://") ? (
              <>
                {d.split("https://")[0]}
                <a
                  href={`https://${d.split("https://")[1]}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sky-600 underline"
                >
                  https://{d.split("https://")[1]}
                </a>
              </>
            ) : d}
          </p>
        ))}
      </div>
    </div>
  );
}
