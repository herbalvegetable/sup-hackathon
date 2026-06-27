"use client";
import { useState, useRef } from "react";
import { getTooltip } from "@/lib/glossary";

interface GlossaryTooltipProps {
  term: string;
  children: React.ReactNode;
}

export function GlossaryTooltip({ term, children }: GlossaryTooltipProps) {
  const definition = getTooltip(term);
  const [visible, setVisible] = useState(false);
  const ref = useRef<HTMLSpanElement>(null);

  if (!definition) return <>{children}</>;

  return (
    <span className="relative inline-block">
      <span
        ref={ref}
        className="underline decoration-dotted decoration-sky-500 cursor-help text-sky-700 font-medium"
        onMouseEnter={() => setVisible(true)}
        onMouseLeave={() => setVisible(false)}
        onFocus={() => setVisible(true)}
        onBlur={() => setVisible(false)}
        tabIndex={0}
        aria-describedby={`tooltip-${term.replace(/\s+/g, "-")}`}
      >
        {children}
      </span>
      {visible && (
        <span
          id={`tooltip-${term.replace(/\s+/g, "-")}`}
          role="tooltip"
          className="absolute z-50 left-0 bottom-full mb-2 w-72 rounded-lg bg-slate-900 px-3 py-2 text-xs text-white shadow-xl"
        >
          <span className="font-semibold text-sky-300">{term}</span>
          <br />
          {definition}
          <span className="absolute left-4 top-full -mt-px border-4 border-transparent border-t-slate-900" />
        </span>
      )}
    </span>
  );
}
