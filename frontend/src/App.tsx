import {
  Compass,
  MapPin,
  Sprout,
  TrendingUp,
  Truck,
  TriangleAlert,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { getArbitrage, getCommodities, getMarkets, getMeta } from "./api";
import type { ArbitrageResult, Commodity, Market, MarketQuote } from "./types";

const inr = (n: number) => "₹" + n.toLocaleString("en-IN");

export default function App() {
  const [commodities, setCommodities] = useState<Commodity[]>([]);
  const [markets, setMarkets] = useState<Market[]>([]);
  const [commodity, setCommodity] = useState("tomato");
  const [origin, setOrigin] = useState("kolar");
  const [maxDistance, setMaxDistance] = useState(200);
  const [result, setResult] = useState<ArbitrageResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [disclaimer, setDisclaimer] = useState("");

  useEffect(() => {
    getCommodities().then((r) => setCommodities(r.commodities)).catch(() => {});
    getMarkets().then((r) => setMarkets(r.markets)).catch(() => {});
    getMeta().then((m) => setDisclaimer(m.disclaimer)).catch(() => {});
  }, []);

  async function run(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      setResult(await getArbitrage(commodity, origin, maxDistance));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  const commodityName = useMemo(
    () => commodities.find((c) => c.id === commodity)?.name ?? commodity,
    [commodities, commodity],
  );

  return (
    <div className="min-h-screen bg-stone-50 text-slate-900">
      <header className="border-b border-stone-200 bg-white">
        <div className="mx-auto flex max-w-4xl items-center gap-2 px-4 py-3 font-display text-lg font-bold">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-primary text-white">
            <Compass className="h-4.5 w-4.5" aria-hidden="true" />
          </span>
          MandiCompass
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-4 pb-24">
        <div className="py-10">
          <div className="mx-auto max-w-2xl text-center">
            <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">
              Where should you <span className="text-primary">sell your crop?</span>
            </h1>
            <p className="mt-3 text-slate-700">
              The highest price isn't the best sale. A mandi that pays more but sits
              100 km away can earn you less after transport. MandiCompass ranks nearby
              mandis by <strong>what you actually take home</strong> — and warns you
              when prices fall below MSP.
            </p>
          </div>

          <form onSubmit={run} className="mx-auto mt-8 max-w-2xl rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="block">
                <span className="text-sm font-semibold text-slate-700">Your crop</span>
                <div className="relative mt-1">
                  <Sprout className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
                  <select value={commodity} onChange={(e) => setCommodity(e.target.value)}
                    className="w-full cursor-pointer rounded-xl border border-slate-300 bg-white p-3 pl-9 text-base focus:outline-none focus-visible:ring-2 focus-visible:ring-primary">
                    {commodities.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </div>
              </label>
              <label className="block">
                <span className="text-sm font-semibold text-slate-700">Your home mandi</span>
                <div className="relative mt-1">
                  <MapPin className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
                  <select value={origin} onChange={(e) => setOrigin(e.target.value)}
                    className="w-full cursor-pointer rounded-xl border border-slate-300 bg-white p-3 pl-9 text-base focus:outline-none focus-visible:ring-2 focus-visible:ring-primary">
                    {markets.map((m) => <option key={m.id} value={m.id}>{m.name} ({m.district})</option>)}
                  </select>
                </div>
              </label>
            </div>
            <label className="mt-4 block">
              <span className="text-sm font-semibold text-slate-700">How far will you travel? <span className="font-normal text-slate-500">{maxDistance} km</span></span>
              <input type="range" min={25} max={400} step={25} value={maxDistance}
                onChange={(e) => setMaxDistance(Number(e.target.value))}
                className="mt-2 w-full accent-primary" />
            </label>
            <button type="submit" disabled={loading}
              className="mt-4 w-full rounded-xl bg-primary py-3 font-semibold text-white transition-colors duration-200 hover:bg-primary-dark focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:opacity-50 motion-reduce:transition-none">
              {loading ? "Comparing mandis…" : "Find the best mandi"}
            </button>
            {error && <p className="mt-3 text-center text-sm text-rose-600">{error}</p>}
          </form>

          {result && <Result result={result} commodityName={commodityName} />}
        </div>
      </main>

      <footer className="border-t border-stone-200 bg-white py-6 text-center text-sm text-slate-600">
        <p className="mx-auto max-w-2xl px-4">{disclaimer}</p>
      </footer>
    </div>
  );
}

function Result({ result, commodityName }: { result: ArbitrageResult; commodityName: string }) {
  const beatsLocal = result.extra_per_quintal > 0;
  return (
    <div className="mx-auto mt-8 max-w-2xl">
      <div className={`rounded-2xl border p-5 ${beatsLocal ? "border-emerald-300 bg-emerald-50" : "border-sky-300 bg-sky-50"}`}>
        <div className="flex items-start gap-3">
          <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-full text-white ${beatsLocal ? "bg-emerald-600" : "bg-sky-600"}`}>
            <TrendingUp className="h-5 w-5" aria-hidden="true" />
          </span>
          <p className="text-sm font-medium text-slate-800">{result.recommendation}</p>
        </div>
      </div>

      {result.msp_alert && (
        <div className="mt-3 flex items-start gap-2 rounded-xl border border-amber-300 bg-amber-50 p-3.5 text-sm text-amber-900">
          <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          <span>{result.msp_alert}</span>
        </div>
      )}

      <div className="mt-4 flex items-center justify-between text-sm text-slate-600">
        <span>{commodityName} · within {result.max_distance_km} km</span>
        {result.msp != null && <span>MSP: <strong>{inr(result.msp)}</strong>/q ({result.msp_season})</span>}
      </div>

      <div className="mt-2 space-y-2">
        {result.quotes.map((q, i) => <QuoteRow key={q.market_id} q={q} rank={i + 1} best={q.market_id === result.best_market_id} hasMsp={result.msp != null} />)}
      </div>

      <p className="mt-3 text-xs text-slate-500">
        Net = modal price − estimated transport (₹{result.transport_rate_per_km_per_quintal}/quintal per km from your mandi).
        Prices: {result.quotes[0]?.arrival_date}.
      </p>
    </div>
  );
}

function QuoteRow({ q, rank, best, hasMsp }: { q: MarketQuote; rank: number; best: boolean; hasMsp: boolean }) {
  return (
    <div className={`rounded-xl border bg-white p-3 ${best ? "border-emerald-400 ring-1 ring-emerald-200" : "border-slate-200"}`}>
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-slate-100 text-xs font-bold text-slate-600">{rank}</span>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold">{q.market_name}</span>
              {q.is_origin && <span className="rounded-full bg-slate-200 px-2 py-0.5 text-[10px] font-bold uppercase text-slate-600">Your mandi</span>}
              {best && !q.is_origin && <span className="rounded-full bg-emerald-600 px-2 py-0.5 text-[10px] font-bold uppercase text-white">Best</span>}
            </div>
            <div className="mt-0.5 flex items-center gap-2 text-xs text-slate-500">
              <span>{q.district}</span>
              {q.distance_km > 0 && <span className="inline-flex items-center gap-0.5"><Truck className="h-3 w-3" aria-hidden="true" />{Math.round(q.distance_km)} km · −{inr(q.transport_cost_per_quintal)}/q</span>}
            </div>
          </div>
        </div>
        <div className="text-right">
          <div className="font-display text-lg font-bold text-primary">{inr(q.net_price)}</div>
          <div className="text-[11px] text-slate-500">net /quintal</div>
        </div>
      </div>
      {hasMsp && q.vs_msp != null && (
        <div className={`mt-2 rounded-lg px-2 py-1 text-xs font-medium ${q.below_msp ? "bg-rose-50 text-rose-700" : "bg-emerald-50 text-emerald-700"}`}>
          {q.below_msp ? `${inr(-q.vs_msp)}/q below MSP` : `${inr(q.vs_msp)}/q above MSP`}
          <span className="font-normal text-slate-500"> · modal {inr(q.modal_price)}</span>
        </div>
      )}
    </div>
  );
}
