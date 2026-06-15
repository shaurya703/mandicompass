import type { ArbitrageResult, Commodity, Market } from "./types";

async function req<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try {
      const b = await res.json();
      if (b?.error?.message) msg = b.error.message;
    } catch {
      /* keep generic */
    }
    throw new Error(msg);
  }
  return res.json();
}

export const getCommodities = () => req<{ commodities: Commodity[] }>("/api/commodities");
export const getMarkets = () => req<{ markets: Market[] }>("/api/markets");
export const getMeta = () => req<{ disclaimer: string; transport_rate_default: number }>("/api/meta");

export const getArbitrage = (commodity: string, origin: string, maxDistance: number) =>
  req<ArbitrageResult>(
    `/api/arbitrage?commodity=${commodity}&origin=${origin}&max_distance=${maxDistance}`,
  );
