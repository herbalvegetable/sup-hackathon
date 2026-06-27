"use client";

interface CoverageSliderProps {
  youHave: number | null | undefined;
  recommendedLow: number | null | undefined;
  recommendedHigh: number | null | undefined;
  status: string;
  compact?: boolean;
}

export function CoverageSlider({
  youHave,
  recommendedLow,
  recommendedHigh,
  status,
  compact = false,
}: CoverageSliderProps) {
  if (
    recommendedLow == null ||
    recommendedHigh == null ||
    status === "not_assessable"
  ) {
    return null;
  }

  // Define the scale:
  // 0 → 0% (left edge)
  // recommendedLow → 40% (start of green zone)
  // recommendedHigh → 70% (end of green zone)
  // rightEdge → 100%
  const rightEdge = Math.max(
    (youHave ?? 0) * 1.5,
    recommendedHigh * 1.6,
    recommendedHigh + 10000
  );

  const toPercent = (v: number) =>
    Math.min(100, Math.max(0, (v / rightEdge) * 100));

  const greenStart = toPercent(recommendedLow);
  const greenEnd = toPercent(recommendedHigh);

  let markerPct: number;
  if (youHave == null || youHave === 0) {
    markerPct = 1; // Far left
  } else {
    markerPct = toPercent(youHave);
  }

  const markerColor =
    status === "underinsured"
      ? "#ef4444"
      : status === "oversold" || status === "redundant"
      ? "#f59e0b"
      : "#22c55e";

  const labelSize = compact ? "text-[10px]" : "text-xs";
  const trackH = compact ? "h-3" : "h-4";

  return (
    <div className="w-full space-y-1.5">
      {/* Zone labels */}
      <div className={`flex justify-between ${labelSize} text-slate-500 font-medium`}>
        <span>Underprotected</span>
        <span>Adequate</span>
        <span>Over-insured</span>
      </div>

      {/* Track */}
      <div className={`relative w-full ${trackH} rounded-full overflow-visible bg-slate-100`}>
        {/* Red zone: 0% → greenStart */}
        <div
          className="absolute top-0 left-0 h-full rounded-l-full bg-red-200"
          style={{ width: `${greenStart}%` }}
        />
        {/* Green zone: greenStart → greenEnd */}
        <div
          className="absolute top-0 h-full bg-green-300"
          style={{ left: `${greenStart}%`, width: `${greenEnd - greenStart}%` }}
        />
        {/* Amber zone: greenEnd → 100% */}
        <div
          className="absolute top-0 right-0 h-full rounded-r-full bg-amber-200"
          style={{ width: `${100 - greenEnd}%` }}
        />

        {/* Recommended range bracket lines */}
        <div
          className="absolute top-0 h-full w-0.5 bg-green-600 opacity-60"
          style={{ left: `${greenStart}%` }}
        />
        <div
          className="absolute top-0 h-full w-0.5 bg-green-600 opacity-60"
          style={{ left: `${greenEnd}%` }}
        />

        {/* Marker */}
        <div
          className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 z-10"
          style={{ left: `${markerPct}%` }}
        >
          <div
            className="w-3.5 h-3.5 rounded-full border-2 border-white shadow-md"
            style={{ backgroundColor: markerColor }}
          />
        </div>
      </div>
    </div>
  );
}
