import axios from "axios";
import type {
  ExtractionResult,
  GapReport,
  UserProfile,
  GuidanceBrief,
  GuidanceAnswers,
} from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120000, // 2 minutes — LLM calls can be slow
});

export async function uploadPolicies(files: File[]): Promise<ExtractionResult> {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }
  // Do NOT manually set Content-Type — the browser must set it automatically
  // so that the correct multipart boundary is included in the header.
  const response = await api.post<ExtractionResult>("/upload", formData);
  return response.data;
}

export async function analyzePortfolio(
  sessionId: string,
  profile: UserProfile,
  guidance?: GuidanceBrief
): Promise<GapReport> {
  const response = await api.post<GapReport>("/analyze", {
    session_id: sessionId,
    profile,
    guidance,
  });
  return response.data;
}

export async function normalizeGuidance(
  answers: GuidanceAnswers
): Promise<GuidanceBrief> {
  const response = await api.post<GuidanceBrief>("/normalize-guidance", answers);
  return response.data;
}

export async function deleteSession(sessionId: string): Promise<void> {
  await api.delete(`/session/${sessionId}`);
}

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.detail || error.message || "An error occurred.";
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "An unexpected error occurred.";
}
