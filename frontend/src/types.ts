export interface Commodity { id: string; name: string; category: string; msp: number | null; msp_season: string | null; unit: string; }
export interface Market { id: string; name: string; district: string; state: string; lat: number; lon: number; }
export interface MarketQuote {
  market_id: string; market_name: string; district: string; distance_km: number;
  modal_price: number; min_price: number; max_price: number;
  transport_cost_per_quintal: number; net_price: number;
  vs_msp: number | null; below_msp: boolean; is_origin: boolean; arrival_date: string;
}
export interface ArbitrageResult {
  commodity: string; commodity_name: string; unit: string;
  msp: number | null; msp_season: string | null;
  origin_market: string; origin_market_name: string;
  max_distance_km: number; transport_rate_per_km_per_quintal: number;
  quotes: MarketQuote[]; best_market_id: string; recommendation: string;
  extra_per_quintal: number; below_msp_count: number; msp_alert: string | null; disclaimer: string;
}
