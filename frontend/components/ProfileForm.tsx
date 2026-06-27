"use client";
import { useState } from "react";
import type { UserProfile } from "@/lib/types";

interface ProfileFormProps {
  onSubmit: (profile: UserProfile) => void;
  loading?: boolean;
}

const defaultProfile: UserProfile = {
  age: 30,
  gender: "male",
  citizenship_status: "sc",
  employment_status: "employed",
  annual_income: undefined,
  dependents: 0,
  smoker: false,
  employer_group_coverage: {
    has_group_coverage: false,
  },
  medical: {
    pre_existing_conditions: [],
    medications: [],
    family_history: [],
    occupation_risk: "low",
    high_risk_activities: [],
  },
};

function splitInput(value: string): string[] {
  return value.split(",").map(s => s.trim()).filter(Boolean);
}

export function ProfileForm({ onSubmit, loading }: ProfileFormProps) {
  const [profile, setProfile] = useState<UserProfile>(defaultProfile);
  const [conditions, setConditions] = useState("");
  const [familyHistory, setFamilyHistory] = useState("");
  const [highRisk, setHighRisk] = useState("");
  const [groupHospital, setGroupHospital] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const finalProfile: UserProfile = {
      ...profile,
      medical: {
        ...profile.medical,
        pre_existing_conditions: splitInput(conditions),
        family_history: splitInput(familyHistory),
        high_risk_activities: splitInput(highRisk),
      },
      employer_group_coverage: {
        ...profile.employer_group_coverage,
        estimated_group_hospital_tier: groupHospital || undefined,
      },
    };
    onSubmit(finalProfile);
  }

  const needsIncome = !["retired", "student", "unemployed"].includes(profile.employment_status);

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Age */}
        <div>
          <label className="label">Age</label>
          <input
            type="number" min={18} max={100}
            className="input"
            value={profile.age}
            onChange={e => setProfile(p => ({ ...p, age: +e.target.value }))}
            required
          />
        </div>

        {/* Gender */}
        <div>
          <label className="label">Gender</label>
          <select className="input" value={profile.gender}
            onChange={e => setProfile(p => ({ ...p, gender: e.target.value as UserProfile["gender"] }))}>
            <option value="male">Male</option>
            <option value="female">Female</option>
            <option value="other">Other / Prefer not to say</option>
          </select>
        </div>

        {/* Citizenship */}
        <div>
          <label className="label">Citizenship / Residency status</label>
          <select className="input" value={profile.citizenship_status}
            onChange={e => setProfile(p => ({ ...p, citizenship_status: e.target.value as UserProfile["citizenship_status"] }))}>
            <option value="sc">Singapore Citizen (SC)</option>
            <option value="pr">Permanent Resident (PR)</option>
            <option value="ep_holder">Employment Pass (EP) holder</option>
            <option value="other_foreigner">Other foreigner</option>
          </select>
          <p className="help-text">This determines whether you're automatically enrolled in MediShield Life and CareShield Life.</p>
        </div>

        {/* Employment */}
        <div>
          <label className="label">Employment status</label>
          <select className="input" value={profile.employment_status}
            onChange={e => setProfile(p => ({ ...p, employment_status: e.target.value as UserProfile["employment_status"] }))}>
            <option value="employed">Employed (salaried)</option>
            <option value="self_employed">Self-employed</option>
            <option value="unemployed">Unemployed</option>
            <option value="retired">Retired</option>
            <option value="student">Student</option>
          </select>
          {!needsIncome && <p className="help-text">Income is optional for retired and student status.</p>}
        </div>

        {/* Annual income */}
        <div>
          <label className="label">Annual income (SGD) {needsIncome ? "" : "(optional)"}</label>
          <div className="relative">
            <span className="absolute left-3 top-2.5 text-slate-400 text-sm">$</span>
            <input
              type="number" min={1} step={1000}
              className="input pl-7"
              placeholder="e.g. 72000"
              value={profile.annual_income || ""}
              onChange={e => setProfile(p => ({ ...p, annual_income: e.target.value ? +e.target.value : undefined }))}
              required={needsIncome}
            />
          </div>
          <p className="help-text">Used only to calculate recommended coverage amounts. Not stored.</p>
        </div>

        {/* Dependents */}
        <div>
          <label className="label">Number of dependents</label>
          <input type="number" min={0} max={20} className="input"
            value={profile.dependents}
            onChange={e => setProfile(p => ({ ...p, dependents: +e.target.value }))} />
          <p className="help-text">Include spouse, children, or elderly parents you financially support.</p>
        </div>
      </div>

      {/* Smoker */}
      <div className="flex items-center gap-3 p-4 rounded-xl bg-slate-50 border border-slate-200">
        <input type="checkbox" id="smoker" className="h-4 w-4 text-sky-600 rounded"
          checked={profile.smoker}
          onChange={e => setProfile(p => ({ ...p, smoker: e.target.checked }))} />
        <label htmlFor="smoker" className="text-sm font-medium text-slate-700">
          I currently smoke or have smoked in the past 12 months
        </label>
      </div>

      {/* Occupation Risk */}
      <div>
        <label className="label">Occupation risk level</label>
        <select className="input" value={profile.medical.occupation_risk}
          onChange={e => setProfile(p => ({
            ...p, medical: { ...p.medical, occupation_risk: e.target.value as "low" | "medium" | "high" }
          }))}>
          <option value="low">Low — office, professional, teacher, doctor</option>
          <option value="medium">Medium — technician, chef, driver, retail</option>
          <option value="high">High — construction, delivery, oil rig, hazardous work</option>
        </select>
      </div>

      {/* Pre-existing conditions */}
      <div>
        <label className="label">Pre-existing medical conditions</label>
        <input type="text" className="input"
          placeholder="e.g. hypertension, diabetes, asthma"
          value={conditions}
          onChange={e => setConditions(e.target.value)} />
        <p className="help-text">Separate with commas. Include conditions even if currently controlled by medication — insurers check your medical history at the time you applied.</p>
      </div>

      {/* Family history */}
      <div>
        <label className="label">Family history of illness (optional)</label>
        <input type="text" className="input"
          placeholder="e.g. heart disease, cancer, diabetes"
          value={familyHistory}
          onChange={e => setFamilyHistory(e.target.value)} />
        <p className="help-text">Used to identify clauses that may affect claim outcomes based on hereditary risk.</p>
      </div>

      {/* High-risk activities */}
      <div>
        <label className="label">High-risk activities (optional)</label>
        <input type="text" className="input"
          placeholder="e.g. motorcycling, rock climbing, scuba diving"
          value={highRisk}
          onChange={e => setHighRisk(e.target.value)} />
      </div>

      {/* Employer group coverage */}
      <div className="space-y-4 p-4 rounded-xl bg-slate-50 border border-slate-200">
        <div className="flex items-center gap-3">
          <input type="checkbox" id="group" className="h-4 w-4 text-sky-600 rounded"
            checked={profile.employer_group_coverage.has_group_coverage}
            onChange={e => setProfile(p => ({
              ...p, employer_group_coverage: { ...p.employer_group_coverage, has_group_coverage: e.target.checked }
            }))} />
          <label htmlFor="group" className="text-sm font-medium text-slate-700">
            My employer provides group insurance benefits
          </label>
        </div>
        <p className="text-xs text-slate-500 ml-7">Check your employment contract or HR portal. Group benefits often include group term life and group hospitalisation.</p>

        {profile.employer_group_coverage.has_group_coverage && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 ml-7">
            <div>
              <label className="label">Group life coverage (SGD)</label>
              <div className="relative">
                <span className="absolute left-3 top-2.5 text-slate-400 text-sm">$</span>
                <input type="number" className="input pl-7" placeholder="e.g. 200000"
                  value={profile.employer_group_coverage.estimated_group_life_sa || ""}
                  onChange={e => setProfile(p => ({
                    ...p, employer_group_coverage: { ...p.employer_group_coverage, estimated_group_life_sa: e.target.value ? +e.target.value : undefined }
                  }))} />
              </div>
            </div>
            <div>
              <label className="label">Group hospital plan tier</label>
              <select className="input" value={groupHospital}
                onChange={e => setGroupHospital(e.target.value)}>
                <option value="">Unknown / None</option>
                <option value="B2_C">Class B2/C</option>
                <option value="B1">Class B1</option>
                <option value="A">Class A</option>
                <option value="private">Private hospital</option>
              </select>
            </div>
            <div>
              <label className="label">Group CI coverage (SGD)</label>
              <div className="relative">
                <span className="absolute left-3 top-2.5 text-slate-400 text-sm">$</span>
                <input type="number" className="input pl-7" placeholder="e.g. 50000"
                  value={profile.employer_group_coverage.estimated_group_ci_sa || ""}
                  onChange={e => setProfile(p => ({
                    ...p, employer_group_coverage: { ...p.employer_group_coverage, estimated_group_ci_sa: e.target.value ? +e.target.value : undefined }
                  }))} />
              </div>
            </div>
          </div>
        )}
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full bg-sky-600 hover:bg-sky-700 disabled:opacity-60 text-white font-semibold py-3 px-6 rounded-xl transition-colors text-sm"
      >
        {loading ? "Analysing your portfolio…" : "Analyse my portfolio"}
      </button>
    </form>
  );
}
