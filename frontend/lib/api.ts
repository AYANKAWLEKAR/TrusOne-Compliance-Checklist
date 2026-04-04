import {
  ComplianceReportRequest,
  ComplianceReportResponse,
  GeoIPResponse,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function createComplianceReport(
  payload: ComplianceReportRequest,
): Promise<ComplianceReportResponse> {
  return request("/api/compliance/report", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function resolveGeoIP(): Promise<GeoIPResponse> {
  return request("/api/geoip/resolve", {
    method: "POST",
  });
}
