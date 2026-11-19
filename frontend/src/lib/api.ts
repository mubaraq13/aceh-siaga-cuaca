import { StandardAPIEnvelope } from "@/types/api";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

export const BACKEND_ORIGIN = API_BASE_URL.replace(/\/api\/v1\/?$/, "");

export async function fetchFromBackend<T>(endpoint: string): Promise<StandardAPIEnvelope<T>> {
  const url = `${API_BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;
  const response = await fetch(url, {
    method: "GET",
    headers: { Accept: "application/json" },
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) detail = String(errJson.detail);
    } catch {
      // Gunakan kode HTTP standar bila gagal membaca JSON
    }
    throw new Error(`Gangguan komunikasi layanan data (${detail})`);
  }

  return (await response.json()) as StandardAPIEnvelope<T>;
}

export function formatWibTimestamp(isoString: string | undefined | null): string {
  if (!isoString) return "Belum tercatat";
  try {
    const dt = new Date(isoString);
    if (Number.isNaN(dt.getTime())) return isoString;
    return new Intl.DateTimeFormat("id-ID", {
      timeZone: "Asia/Jakarta",
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(dt) + " WIB";
  } catch {
    return isoString;
  }
}
