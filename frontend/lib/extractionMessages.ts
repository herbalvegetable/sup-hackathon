const FIELD_LABELS: Record<string, string> = {
  sum_assured: "sum assured",
  tpd_sum_assured: "TPD sum assured",
  annual_premium: "annual premium",
  monthly_premium: "monthly premium",
  coverage_start: "coverage start date",
  coverage_end: "coverage end date",
  maturity_age: "maturity age",
  waiting_period_days: "waiting period",
  policy_number: "policy number",
  insurer: "insurer name",
  ip_ward_tier: "hospital ward class",
};

function humanizeField(field: string): string {
  return FIELD_LABELS[field] ?? field.replace(/_/g, " ");
}

/** Turn backend extraction flag strings into plain-English notes. */
export function formatExtractionFlag(flag: string): string {
  const colonIdx = flag.indexOf(": ");
  if (colonIdx === -1) return flag;

  const filename = flag.slice(0, colonIdx);
  const message = flag.slice(colonIdx + 2);

  const missingMatch = message.match(/^missing (.+)$/i);
  if (missingMatch) {
    const fields = missingMatch[1]
      .split(", ")
      .map((f) => humanizeField(f.trim()));
    const fieldList =
      fields.length === 1
        ? fields[0]
        : `${fields.slice(0, -1).join(", ")} and ${fields[fields.length - 1]}`;
    return `From ${filename}, we couldn't find the ${fieldList}. The rest of the policy was still analysed.`;
  }

  if (message.startsWith("extraction error")) {
    return `We couldn't read ${filename}. Please check that it's a digital policy PDF and try again.`;
  }

  if (message.toLowerCase().includes("scanned")) {
    return `${filename} looks like a scanned document. Please upload the digital version from your insurer's portal instead.`;
  }

  if (message.includes("must be a PDF") || message.includes("not appear to be a valid PDF")) {
    return `${filename} doesn't appear to be a valid PDF. Please upload a PDF file from your insurer.`;
  }

  if (message.includes("Maximum allowed is 20 MB") || message.includes("MB.")) {
    return `${filename} is too large. Each policy file must be 20 MB or smaller.`;
  }

  if (message.includes("Maximum") && message.includes("policies per session")) {
    return "You can upload up to 10 policy files at a time. Please remove some files and try again.";
  }

  // Strip redundant quoted filename from validation messages
  const cleaned = message.replace(new RegExp(`File '${filename.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}'`), "This file");
  if (cleaned !== message) {
    return `${filename}: ${cleaned}`;
  }

  return `${filename}: ${message}`;
}
