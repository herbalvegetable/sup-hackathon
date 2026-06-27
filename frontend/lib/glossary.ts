export const glossary: Record<string, string> = {
  "Sum Assured": "The maximum amount this policy will pay out when you make a claim.",
  "Sum Insured": "The maximum amount this policy will pay out when you make a claim.",
  "Rider": "An add-on benefit attached to a base insurance policy, usually for additional coverage at extra cost.",
  "Critical Illness": "Pays a lump sum when diagnosed with a serious illness such as cancer or heart attack (at late stage).",
  "CI": "Pays a lump sum when diagnosed with a serious illness such as cancer or heart attack (at late stage).",
  "Early Critical Illness": "Like CI cover, but pays out at early detection rather than late stage — giving you funds sooner when treatment is still effective.",
  "Early CI": "Like CI cover, but pays out at early detection rather than late stage — giving you funds sooner when treatment is still effective.",
  "TPD": "Total Permanent Disability — pays out if you become permanently and totally unable to perform any work.",
  "Total Permanent Disability": "Pays out if you become permanently and totally unable to perform any work.",
  "Waiting Period": "A period at the start of a policy during which certain types of claims cannot be made. Typically 30–90 days for CI or disability claims.",
  "MediShield Life": "Singapore's basic national health insurance scheme, automatically covering all Singapore Citizens and Permanent Residents.",
  "Integrated Shield Plan": "A private insurer's upgrade on top of MediShield Life, providing coverage for higher ward classes at public or private hospitals.",
  "IP": "Integrated Shield Plan — a private insurer's upgrade on top of MediShield Life for better hospital coverage.",
  "CareShield Life": "Singapore's national severe disability insurance, automatically enrolling all residents born in 1980 or later.",
  "ElderShield": "The predecessor to CareShield Life — a severe disability insurance scheme for older Singaporeans.",
  "Premium": "The regular payment you make to keep your insurance policy active — can be monthly, quarterly, or annual.",
  "Exclusion": "A specific condition, situation, or event that your insurance policy will NOT cover. Read these carefully.",
  "Pre-existing Condition": "A health condition you had before taking out the insurance policy. Often excluded or subject to loading.",
  "Loading": "An extra premium charge by the insurer because of your medical history or risk profile.",
  "Death Benefit": "The amount paid to your beneficiaries (family) when you pass away.",
  "Maturity Age": "The age at which your policy coverage ends. After this age, the policy no longer provides protection.",
  "Ward Class": "The type of hospital ward your hospitalisation plan covers — from basic (B2/C) to Class A or private hospital.",
  "Co-insurance": "The portion of a hospital bill you pay yourself after the deductible — typically 10% under MediShield Life.",
  "Deductible": "The amount you must pay out-of-pocket first before your insurance kicks in for a hospital claim.",
  "MediSave": "A mandatory savings account for Singaporeans and PRs to pay for medical expenses and insurance premiums.",
};

export function getTooltip(term: string): string | undefined {
  // Exact match first
  if (glossary[term]) return glossary[term];
  // Case-insensitive match
  const lower = term.toLowerCase();
  for (const [key, value] of Object.entries(glossary)) {
    if (key.toLowerCase() === lower) return value;
  }
  return undefined;
}
