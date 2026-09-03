import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  Anchor,
  ArrowDown,
  ArrowUp,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  ChevronDown,
  Clock3,
  Container,
  Gauge,
  Globe2,
  Menu,
  MapPin,
  Navigation,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  X,
} from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import "./App.css";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const ORIGIN_COUNTRIES = [
  "Australia",
  "Indonesia",
  "United States",
  "Mozambique",
  "Russia",
];

const ORIGIN_PORTS = {
  Australia: [
    "Newcastle",
    "Hay Point",
    "Gladstone",
    "Abbot Point",
  ],
  Indonesia: [
    "Samarinda",
    "Taboneo",
    "Balikpapan",
    "Muara Berau",
  ],
  "United States": [
    "New Orleans",
    "Houston",
    "Mobile",
  ],
  Mozambique: [
    "Nacala",
    "Maputo",
    "Beira",
  ],
  Russia: [
    "Taman",
    "Novorossiysk",
    "Vostochny",
  ],
};

const DESTINATION_PORTS = [
  "Paradip",
  "Visakhapatnam",
  "Gangavaram",
  "Gopalpur",
  "Dhamra",
  "Sagar",
  "Sandheads",
  "Haldia",
];

const DEFAULT_FORECAST = [
  {
    horizon: "Current",
    value: 1189,
    change: 0,
  },
  {
    horizon: "7D",
    value: 1186.79,
    change: -0.19,
  },
  {
    horizon: "30D",
    value: 1328.4,
    change: 11.72,
  },
  {
    horizon: "60D",
    value: 1280.71,
    change: 7.71,
  },
  {
    horizon: "90D",
    value: 1921.14,
    change: 61.58,
  },
];

function formatMoney(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "—";
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(Number(value));
}

function formatCompactMoney(value) {
  if (
    value === null ||
    value === undefined ||
    Number.isNaN(Number(value))
  ) {
    return "—";
  }

  const amount = Number(value);

  if (amount >= 1_000_000) {
    return `$${(amount / 1_000_000).toFixed(2)}M`;
  }

  if (amount >= 1_000) {
    return `$${(amount / 1_000).toFixed(0)}K`;
  }

  return formatMoney(amount);
}

function formatNumber(value, digits = 0) {
  if (
    value === null ||
    value === undefined ||
    Number.isNaN(Number(value))
  ) {
    return "—";
  }

  return Number(value).toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function formatPercentage(value) {
  if (
    value === null ||
    value === undefined ||
    Number.isNaN(Number(value))
  ) {
    return "—";
  }

  const number = Number(value);

  return `${number >= 0 ? "+" : ""}${number.toFixed(2)}%`;
}


function formatDecisionText(value) {
  if (!value) return "—";

  const labels = {
    FIX_CONTRACT: "Fix Contract",
    CONSIDER_CONTRACT: "Consider Contract",
    MONITOR: "Monitor",
    SPOT_OR_WAIT: "Spot / Wait",
    CHANGE_DESTINATION_OR_CARGO_OR_REVIEW_VESSEL_CONSTRAINTS:
      "Change destination, cargo, or review vessel constraints",
    NO_ECONOMICALLY_FEASIBLE_VESSEL:
      "No economically feasible vessel",
  };

  return (
    labels[value] ||
    String(value)
      .replaceAll("_", " ")
      .toLowerCase()
      .replace(/\b\w/g, (char) => char.toUpperCase())
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  subtext,
  positive,
}) {
  return (
    <div className="stat-card">
      <div className="stat-icon">
        <Icon size={18} />
      </div>

      <div>
        <span className="stat-label">{label}</span>
        <strong>{value}</strong>

        {subtext && (
          <span className={positive ? "stat-subtext positive" : "stat-subtext"}>
            {subtext}
          </span>
        )}
      </div>
    </div>
  );
}

function SelectField({
  label,
  value,
  onChange,
  options,
  icon: Icon = ChevronDown,
}) {
  return (
    <label className="field">
      <span className="field-label">{label}</span>

      <div className="select-control">
        <select value={value} onChange={(e) => onChange(e.target.value)}>
          {options.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>

        <Icon size={15} />
      </div>
    </label>
  );
}

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const [commodity, setCommodity] = useState("Coal");
  const [cargo, setCargo] = useState("60000");

  const [originCountry, setOriginCountry] = useState("Australia");
  const [originPort, setOriginPort] = useState(
    ORIGIN_PORTS.Australia[0]
  );

  const [destinationPort, setDestinationPort] =
    useState("Paradip");

  const [duration, setDuration] = useState("6");
  const [voyages, setVoyages] = useState("6");

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [analyzed, setAnalyzed] = useState(false);
  const [error, setError] = useState("");

  const availableOriginPorts = ORIGIN_PORTS[originCountry];

  useEffect(() => {
    if (!availableOriginPorts.includes(originPort)) {
      setOriginPort(availableOriginPorts[0]);
    }
  }, [originCountry, availableOriginPorts, originPort]);

  const forecast = result?.forecast;
  const vesselDecision = result?.vessel_decision;
  const contractDecision = result?.contract_decision;
  const riskAnalysis = contractDecision?.risk_analysis;
  const recommendation = result?.final_recommendation;
  const congestion = result?.congestion;
  const noFeasibleVessel =
    result?.status === "NO_ECONOMICALLY_FEASIBLE_VESSEL";
  const diagnosticAction =
    result?.diagnostic?.recommended_action;

  const forecastData = useMemo(() => {
    const horizons = forecast?.all_horizons;

    if (!horizons) {
      return result ? [] : DEFAULT_FORECAST;
    }

    const currentIndex =
      forecast.current_index ??
      horizons["30"]?.current_index ??
      1189;

    return [
      {
        horizon: "Current",
        value: Number(currentIndex),
        change: 0,
      },
      ...["7", "30", "60", "90"].map((key) => ({
        horizon: `${key}D`,
        value: Number(
          horizons[key]?.predicted_index ?? currentIndex
        ),
        change: Number(
          horizons[key]?.change_percent ?? 0
        ),
      })),
    ];
  }, [forecast, result]);

  const vesselComparison = useMemo(() => {
    if (result?.vessel_comparison) {
      return result.vessel_comparison;
    }

    return [
      {
        vessel_type: "Handysize",
        feasible: false,
        reason: "No result available",
      },
      {
        vessel_type: "Supramax",
        feasible: false,
        reason: "No result available",
      },
      {
        vessel_type: "Panamax",
        feasible: false,
        reason: "No result available",
      },
      {
        vessel_type: "Capesize",
        feasible: false,
        reason: "No result available",
      },
    ];
  }, [result]);

  const currentIndex =
    forecast?.current_index ??
    (result ? null : forecastData[0]?.value ?? 1189);

  const predicted30 =
    forecast?.predicted_30d_index ??
    forecastData.find((item) => item.horizon === "30D")?.value ??
    null;

  const change30 =
    forecast?.change_percent_30d ??
    (result
      ? null
      : forecastData.find((item) => item.horizon === "30D")?.change ?? 0);

  const confidence30 =
    forecast?.confidence_30d ??
    "—";

  const selectedVessel =
    vesselDecision?.recommended_vessel ??
    recommendation?.recommended_vessel ??
    "—";

  const action =
    recommendation?.action ??
    "—";

  const displayAction = noFeasibleVessel
    ? formatDecisionText(
        diagnosticAction || "REVIEW_SCENARIO_CONSTRAINTS"
      )
    : formatDecisionText(action);

  const voyageCost =
    vesselDecision?.recommended_voyage_cost_usd ??
    null;

  const costPerMt =
    vesselDecision?.cost_per_mt_usd ??
    null;

  const currentRate =
    contractDecision?.current_rate_usd_per_mt ??
    null;

  const forecastRate =
    contractDecision?.forecast_rate_usd_per_mt ??
    null;

  const contractRate =
    contractDecision?.contract_rate_usd_per_mt ??
    null;

  const expectedSavings =
    riskAnalysis?.expected_savings_from_contract_usd ??
    null;

  const expectedSavingsPercent =
    riskAnalysis?.expected_savings_percent ??
    null;

  const loadingQueue =
    congestion?.loading?.queue_days ?? null;

  const dischargeQueue =
    congestion?.discharge?.queue_days ?? null;

  const totalQueue =
    congestion?.total_queue_days ?? null;

  const riskLevel =
    congestion?.risk_level ?? "—";

  const realDataUsed =
    congestion?.real_data_used ?? false;

  const selected30Forecast =
    forecast?.all_horizons?.["30"];

  const handleCountryChange = (country) => {
    setOriginCountry(country);
    setOriginPort(ORIGIN_PORTS[country][0]);
    setResult(null);
    setAnalyzed(false);
    setError("");
  };

  const handleAnalyze = async () => {
    if (loading) return;
  
    setLoading(true);
    setError("");
    setResult(null);
    setAnalyzed(false);
  
    try {
      const payload = {
        commodity: commodity.trim() || "Bulk Cargo",
        quantity_mt: Number(cargo),
        origin_country: originCountry,
        origin_port: originPort,
        destination_port: destinationPort,
        contract_duration_months: Number(duration),
        planned_voyages: Number(voyages),
      };
  
      if (!payload.quantity_mt || payload.quantity_mt <= 0) {
        throw new Error("Cargo quantity must be greater than 0.");
      }
  
      if (!payload.contract_duration_months || payload.contract_duration_months <= 0) {
        throw new Error("Contract duration must be at least 1 month.");
      }
  
      if (!payload.planned_voyages || payload.planned_voyages <= 0) {
        throw new Error("Planned voyages must be at least 1.");
      }
  
      const response = await axios.post(
        `${API_BASE_URL}/api/forecast`,
        payload,
        {
          timeout: 120000,
        }
      );
  
      console.log("FULL API RESPONSE:", response.data);
  
      const apiResult = response.data;
  
      setResult(apiResult);
  
      if (apiResult?.status === "SUCCESS") {
        setAnalyzed(true);
  
        setTimeout(() => {
          document.getElementById("results")?.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
        }, 100);
      } else {
        setAnalyzed(false);
  
        setTimeout(() => {
          document.getElementById("results")?.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
        }, 100);
      }
    } catch (err) {
      console.error("Analysis error:", err);
  
      const message =
        err?.response?.data?.detail ||
        err?.message ||
        "Unable to complete analysis.";
  
      setError(message);
      setResult(null);
      setAnalyzed(false);
    } finally {
      setLoading(false);
    }
  };
  
  const scenarioOrigin =
    result?.trade_context?.origin_port ??
    originPort;

  const scenarioDestination =
    result?.trade_context?.destination_port ??
    destinationPort;

  const scenarioCountry =
    result?.trade_context?.origin_country ??
    originCountry;

  return (
    <div className="app-shell">
      {sidebarOpen && (
        <button
          className="mobile-overlay"
          aria-label="Close navigation"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}>
        <div className="brand">
          <div className="brand-mark">
            <Anchor size={20} />
          </div>

          <div>
            <h1>Freight AI</h1>
            <span>Chartering Intelligence</span>
          </div>
        </div>

        <nav>
          <a
            className="active"
            href="#overview"
            onClick={() => setSidebarOpen(false)}
          >
            <Gauge size={17} />
            Overview
          </a>

          <a
            href="#forecast"
            onClick={() => setSidebarOpen(false)}
          >
            <TrendingUp size={17} />
            Market Forecast
          </a>

          <a
            href="#vessels"
            onClick={() => setSidebarOpen(false)}
          >
            <Container size={17} />
            Vessel Economics
          </a>

          <a
            href="#ports"
            onClick={() => setSidebarOpen(false)}
          >
            <MapPin size={17} />
            Port Intelligence
          </a>

          <a
            href="#contract"
            onClick={() => setSidebarOpen(false)}
          >
            <BarChart3 size={17} />
            Contract Strategy
          </a>
        </nav>

        <div className="sidebar-note">
          <ShieldCheck size={17} />

          <div>
            <strong>Decision Support</strong>
            <span>
              Forecasts, vessel economics and operational risk in one view.
            </span>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <button
            className="menu-btn"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open navigation"
          >
            <Menu size={20} />
          </button>

          <div className="topbar-title">
            <span className="eyebrow">
              GLOBAL ORIGIN → EAST COAST INDIA
            </span>

            <h2>Freight Intelligence Dashboard</h2>
          </div>

          <div className="system-status">
            <span className="status-dot" />
            <span>{loading ? "ANALYZING" : "SYSTEM READY"}</span>
          </div>
        </header>

        <section id="overview" className="hero-section">
          <div className="hero-copy">
            <span className="section-kicker hero-kicker">
              <Sparkles size={14} />
              AI CHARTERING DECISION SUPPORT
            </span>

            <h3>
              From international cargo sourcing
              <br />
              to the right Indian port strategy.
            </h3>

            <p>
              Forecast dry-bulk market conditions, compare vessel
              economics, evaluate port constraints and assess
              contract risk before fixing your next voyage.
            </p>

            <div className="hero-route">
              <div>
                <Globe2 size={16} />
                <span>INTERNATIONAL ORIGIN</span>
              </div>

              <div className="hero-route-line" />

              <div>
                <MapPin size={16} />
                <span>EAST COAST INDIA</span>
              </div>
            </div>
          </div>

          <div className="hero-side">
            <div className="hero-stat">
              <span>FORECAST HORIZONS</span>
              <strong>7D · 30D · 60D · 90D</strong>
            </div>

            <div className="hero-stat">
              <span>VESSEL CLASSES</span>
              <strong>HSI · SI · PI · CI</strong>
            </div>

            <div className="hero-stat">
              <span>DECISION OUTPUT</span>
              <strong>VESSEL + CONTRACT + RISK</strong>
            </div>
          </div>
        </section>

        <section className="scenario-card">
          <div className="section-heading-row">
            <div>
              <span className="section-kicker">
                VOYAGE SCENARIO
              </span>

              <h3>Build your procurement scenario</h3>
            </div>

            <div className="scenario-status">
              <span className="status-dot" />
              {loading ? "Analyzing scenario..." : "API decision engine"}
            </div>
          </div>

          <div className="scenario-grid">
            <label className="field">
              <span className="field-label">Commodity</span>

              <div className="input-control">
                <input
                  value={commodity}
                  onChange={(e) => setCommodity(e.target.value)}
                  placeholder="Coal, iron ore..."
                />
              </div>
            </label>

            <label className="field">
              <span className="field-label">Cargo Quantity</span>

              <div className="input-control">
                <input
                  type="number"
                  min="1000"
                  value={cargo}
                  onChange={(e) => setCargo(e.target.value)}
                />

                <span>MT</span>
              </div>
            </label>

            <SelectField
              label="Origin Country"
              value={originCountry}
              onChange={handleCountryChange}
              options={ORIGIN_COUNTRIES}
              icon={Globe2}
            />

            <SelectField
              label="Origin Port"
              value={originPort}
              onChange={(value) => {
                setOriginPort(value);
                setResult(null);
                setAnalyzed(false);
              }}
              options={availableOriginPorts}
              icon={Navigation}
            />

            <SelectField
              label="Indian Destination"
              value={destinationPort}
              onChange={(value) => {
                setDestinationPort(value);
                setResult(null);
                setAnalyzed(false);
              }}
              options={DESTINATION_PORTS}
              icon={MapPin}
            />

            <label className="field">
              <span className="field-label">
                Contract Duration
              </span>

              <div className="input-control">
                <input
                  type="number"
                  min="1"
                  max="12"
                  value={duration}
                  onChange={(e) => setDuration(e.target.value)}
                />

                <span>MONTHS</span>
              </div>
            </label>

            <label className="field">
              <span className="field-label">
                Planned Voyages
              </span>

              <div className="input-control">
                <input
                  type="number"
                  min="1"
                  max="24"
                  value={voyages}
                  onChange={(e) => setVoyages(e.target.value)}
                />

                <span>VOYAGES</span>
              </div>
            </label>

            <button
              type="button"
              className="analyze-btn"
              onClick={handleAnalyze}
              disabled={loading}
            >
              {loading ? (
                <>
                  <Gauge size={16} />
                  Analyzing...
                </>
              ) : (
                <>
                  <Sparkles size={16} />
                  Analyze Strategy
                </>
              )}
            </button>
          </div>

          {error && (
            <div className="warning-box api-error">
              <X size={16} />

              <p>
                <strong>Analysis error:</strong> {error}
              </p>
            </div>
          )}
        </section>

        <section id="results" className="decision-layout">
          <div className="decision-card">
            <div className="decision-card-header">
              <div>
                <span className="section-kicker light-kicker">
                  AI RECOMMENDATION
                </span>

                <span className="recommendation-status">
                  <CheckCircle2 size={13} />
                  {result ? "Analysis complete" : "Awaiting analysis"}
                </span>
              </div>

              <span className="confidence-pill">
                <span />
                {confidence30 !== "—"
                  ? `${confidence30} CONFIDENCE`
                  : "NO RESULT"}
              </span>
            </div>

            <div className="decision-main">
              <div>
                <span className="label-small">
                  RECOMMENDED VESSEL
                </span>

                <h3>
                  {noFeasibleVessel
                    ? "No feasible vessel"
                    : selectedVessel}
                </h3>

                <div className="route-summary">
                  <span>{scenarioCountry}</span>
                  <ArrowRight />
                  <span>{scenarioOrigin}</span>
                  <ArrowRight />
                  <span>{scenarioDestination}</span>
                </div>

                <p>
                  {noFeasibleVessel
                    ? result?.message ||
                      "No vessel can complete the voyage under the current assumptions."
                    : recommendation?.reason ||
                      "Run the analysis to receive the vessel, market and contract recommendation from the decision engine."}
                </p>
              </div>

              <div className="decision-vessel-icon">
                <Container size={44} strokeWidth={1.4} />
              </div>
            </div>

            <div className="decision-metrics">
              <div>
                <span>VOYAGE COST</span>
                <strong>
                  {formatCompactMoney(voyageCost)}
                </strong>
              </div>

              <div>
                <span>COST / MT</span>
                <strong>
                  {costPerMt !== null
                    ? `$${Number(costPerMt).toFixed(2)}`
                    : "—"}
                </strong>
              </div>

              <div>
                <span>30D OUTLOOK</span>
                <strong
                  className={
                    Number(change30) >= 0
                      ? "lime"
                      : "negative"
                  }
                >
                  {formatPercentage(change30)}
                </strong>
              </div>
            </div>

            <div className="action-banner">
              <div>
                <span>{noFeasibleVessel ? "NEXT BEST ACTION" : "RECOMMENDED ACTION"}</span>
                <strong>{displayAction}</strong>
              </div>

              <Navigation size={18} />
            </div>
          </div>

          <div className="quick-stats">
            <StatCard
              icon={TrendingUp}
              label="Current PI Index"
              value={formatNumber(currentIndex, 0)}
              subtext={
                forecast
                  ? `${formatPercentage(change30)} projected in 30D`
                  : result
                    ? "Not generated for this scenario"
                    : "Awaiting API result"
              }
              positive={Number(change30) >= 0}
            />

            <StatCard
              icon={BarChart3}
              label="Forecast Rate"
              value={
                forecastRate !== null
                  ? `$${Number(forecastRate).toFixed(2)}/MT`
                  : "—"
              }
              subtext="30-day market scenario"
              positive={Number(change30) >= 0}
            />

            <StatCard
              icon={Clock3}
              label="Port Queue"
              value={
                totalQueue !== null
                  ? `${Number(totalQueue).toFixed(1)} days`
                  : "—"
              }
              subtext={
                riskLevel !== "—"
                  ? `${riskLevel} congestion`
                  : "Awaiting API result"
              }
            />

            <StatCard
              icon={ShieldCheck}
              label="Expected Savings"
              value={formatCompactMoney(expectedSavings)}
              subtext={
                expectedSavingsPercent !== null
                  ? `${Number(expectedSavingsPercent).toFixed(2)}% vs expected spot`
                  : "Awaiting contract analysis"
              }
              positive={Number(expectedSavings) > 0}
            />
          </div>
        </section>

        <section id="forecast" className="content-grid">
          <div className="panel chart-panel">
            <div className="panel-header">
              <div>
                <span className="section-kicker">
                  MARKET FORECAST
                </span>

                <h3>
                  {forecast?.vessel_class
                    ? `${forecast.vessel_class} Index Outlook`
                    : "Vessel-Class Index Outlook"}
                </h3>

                <p className="panel-description">
                  Model-based vessel-class market projection
                </p>
              </div>

              <span className="chart-tag">
                {forecast?.vessel_class || "BALTIC"} · INDEX
              </span>
            </div>

            <div className="chart-area">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={forecastData}>
                  <defs>
                    <linearGradient
                      id="forecastFill"
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop
                        offset="0%"
                        stopOpacity={0.3}
                      />
                      <stop
                        offset="100%"
                        stopOpacity={0}
                      />
                    </linearGradient>
                  </defs>

                  <CartesianGrid
                    strokeDasharray="3 3"
                    vertical={false}
                  />

                  <XAxis
                    dataKey="horizon"
                    axisLine={false}
                    tickLine={false}
                  />

                  <YAxis
                    axisLine={false}
                    tickLine={false}
                    width={50}
                    domain={[
                      "dataMin - 50",
                      "dataMax + 100",
                    ]}
                  />

                  <Tooltip
                    formatter={(value) => [
                      Number(value).toFixed(2),
                      "Index",
                    ]}
                    labelFormatter={(label) =>
                      `${label} outlook`
                    }
                  />

                  <Area
                    type="monotone"
                    dataKey="value"
                    strokeWidth={3}
                    fill="url(#forecastFill)"
                    dot={{ r: 4 }}
                    activeDot={{ r: 6 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div className="forecast-cards">
              {forecastData.slice(1).map((point) => {
                const horizonKey = point.horizon.replace(
                  "D",
                  ""
                );

                const horizonResult =
                  forecast?.all_horizons?.[horizonKey];

                return (
                  <div
                    className="forecast-item"
                    key={point.horizon}
                  >
                    <span>{point.horizon}</span>

                    <strong>
                      {Number(point.value).toFixed(2)}
                    </strong>

                    <small
                      className={
                        point.change >= 0
                          ? "change positive"
                          : "change negative"
                      }
                    >
                      {point.change >= 0 ? (
                        <ArrowUp size={11} />
                      ) : (
                        <ArrowDown size={11} />
                      )}

                      {formatPercentage(point.change)}
                    </small>

                    {horizonResult?.confidence && (
                      <span className="forecast-confidence">
                        {horizonResult.confidence}
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          <div id="ports" className="panel port-panel">
            <div className="panel-header">
              <div>
                <span className="section-kicker">
                  PORT INTELLIGENCE
                </span>

                <h3>Destination risk</h3>

                <p className="panel-description">
                  Current prototype queue assessment
                </p>
              </div>

              <span className="risk-badge">
                {riskLevel}
              </span>
            </div>

            <div className="port-route-card">
              <div className="route-place">
                <div className="route-marker origin-marker">
                  <Globe2 size={15} />
                </div>

                <div>
                  <span>ORIGIN</span>
                  <strong>{scenarioOrigin}</strong>
                  <small>{scenarioCountry}</small>
                </div>
              </div>

              <div className="route-connector">
                <span>INTERNATIONAL BULK TRADE</span>
                <div />
              </div>

              <div className="route-place">
                <div className="route-marker destination-marker">
                  <MapPin size={15} />
                </div>

                <div>
                  <span>DESTINATION</span>
                  <strong>{scenarioDestination}</strong>
                  <small>East Coast India</small>
                </div>
              </div>
            </div>

            <div className="queue-list">
              <div>
                <span>Loading / origin queue</span>
                <strong>
                  {loadingQueue !== null
                    ? `${Number(loadingQueue).toFixed(1)} day`
                    : "—"}
                </strong>
              </div>

              <div>
                <span>Destination queue</span>
                <strong>
                  {dischargeQueue !== null
                    ? `${Number(dischargeQueue).toFixed(1)} days`
                    : "—"}
                </strong>
              </div>

              <div>
                <span>Total queue exposure</span>
                <strong>
                  {totalQueue !== null
                    ? `${Number(totalQueue).toFixed(1)} days`
                    : "—"}
                </strong>
              </div>

              <div>
                <span>Data source</span>
                <strong className="muted-value">
                  {realDataUsed
                    ? "Real observations"
                    : "Prototype fallback"}
                </strong>
              </div>
            </div>

            {!realDataUsed && (
              <div className="warning-box">
                <Clock3 size={16} />

                <p>
                  Real port congestion observations are not
                  connected yet. Current queue figures remain
                  prototype assumptions.
                </p>
              </div>
            )}
          </div>
        </section>

        <section id="vessels" className="panel vessel-panel">
          <div className="panel-header">
            <div>
              <span className="section-kicker">
                VESSEL ECONOMICS
              </span>

              <h3>Feasibility & cost comparison</h3>

              <p className="panel-description">
                Results returned by the vessel optimization engine
              </p>
            </div>

            <span className="table-route">
              {formatNumber(Number(cargo) || 0, 0)} MT ·{" "}
              {destinationPort}
            </span>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Vessel</th>
                  <th>Status</th>
                  <th>Voyage Cost</th>
                  <th>Cost / MT</th>
                  <th>Why</th>
                </tr>
              </thead>

              <tbody>
                {vesselComparison.map((row) => {
                  const isRecommended =
                    row.vessel_type === selectedVessel;

                  const isFeasible =
                    row.feasible === true;

                  const hasCost =
                    row.total_voyage_cost_usd !==
                      null &&
                    row.total_voyage_cost_usd !==
                      undefined;

                  return (
                    <tr
                      key={row.vessel_type}
                      className={
                        isRecommended
                          ? "selected-row"
                          : ""
                      }
                    >
                      <td>
                        <div className="vessel-name">
                          <div className="mini-vessel">
                            <Container size={15} />
                          </div>

                          <strong>
                            {row.vessel_type}
                          </strong>
                        </div>
                      </td>

                      <td>
                        <span
                          className={`table-status ${
                            isRecommended
                              ? "recommended"
                              : isFeasible
                              ? "feasible"
                              : "not-feasible"
                          }`}
                        >
                          {isRecommended
                            ? "Recommended"
                            : isFeasible
                            ? "Feasible"
                            : "Not Feasible"}
                        </span>
                      </td>

                      <td>
                        {hasCost
                          ? formatCompactMoney(
                              row.total_voyage_cost_usd
                            )
                          : "—"}
                      </td>

                      <td>
                        {row.cost_per_mt_usd !==
                          undefined &&
                        row.cost_per_mt_usd !==
                          null
                          ? `$${Number(
                              row.cost_per_mt_usd
                            ).toFixed(2)}`
                          : "—"}
                      </td>

                      <td className="analysis-cell">
                        {row.reason ||
                          row.reasons?.join(", ") ||
                          (isFeasible
                            ? "Feasible under current assumptions"
                            : "Not feasible")}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>

        <section
          id="contract"
          className="content-grid bottom-grid"
        >
          <div className="panel contract-panel">
            <div className="panel-header">
              <div>
                <span className="section-kicker">
                  CONTRACT STRATEGY
                </span>

                <h3>Spot vs fixed contract</h3>

                <p className="panel-description">
                  {duration}-month procurement scenario ·{" "}
                  {voyages} planned voyages
                </p>
              </div>

              <span className="savings-pill">
                {expectedSavingsPercent !== null
                  ? `${Number(
                      expectedSavingsPercent
                    ).toFixed(2)}% SAVINGS`
                  : "NO RESULT"}
              </span>
            </div>

            <div className="contract-grid">
              <div className="contract-item">
                <span>CURRENT SPOT</span>
                <strong>
                  {currentRate !== null
                    ? `$${Number(currentRate).toFixed(2)}`
                    : "—"}
                </strong>
                <small>/MT</small>
              </div>

              <div className="contract-item forecast-price">
                <span>FORECAST</span>
                <strong>
                  {forecastRate !== null
                    ? `$${Number(forecastRate).toFixed(2)}`
                    : "—"}
                </strong>
                <small>/MT</small>
              </div>

              <div className="contract-item fixed-price">
                <span>FIXED CONTRACT</span>
                <strong>
                  {contractRate !== null
                    ? `$${Number(contractRate).toFixed(2)}`
                    : "—"}
                </strong>
                <small>/MT</small>
              </div>
            </div>

            <div className="savings-panel">
              <div>
                <span>EXPECTED CONTRACT SAVINGS</span>

                <strong>
                  {formatMoney(expectedSavings)}
                </strong>
              </div>

              <div className="savings-progress">
                <div
                  style={{
                    width: `${Math.min(
                      Math.max(
                        Number(expectedSavingsPercent) || 0,
                        0
                      ),
                      100
                    )}%`,
                  }}
                />
              </div>

              <small>
                Based on the decision engine's current contract
                and risk assumptions
              </small>
            </div>
          </div>

          <div className="panel risk-panel">
            <div className="panel-header">
              <div>
                <span className="section-kicker">
                  RISK ANALYSIS
                </span>

                <h3>Market scenarios</h3>
              </div>
            </div>

            <div className="scenario-list">
              <div className="scenario-row">
                <span className="scenario-icon down">
                  <ArrowDown size={14} />
                </span>

                <div>
                  <span>Downside</span>
                  <strong>
                    {riskAnalysis?.downside_rate_usd_per_mt !==
                    undefined
                      ? `$${Number(
                          riskAnalysis.downside_rate_usd_per_mt
                        ).toFixed(2)} / MT`
                      : "—"}
                  </strong>
                </div>
              </div>

              <div className="scenario-row">
                <span className="scenario-icon current">
                  <Gauge size={14} />
                </span>

                <div>
                  <span>Current</span>
                  <strong>
                    {currentRate !== null
                      ? `$${Number(
                          currentRate
                        ).toFixed(2)} / MT`
                      : "—"}
                  </strong>
                </div>
              </div>

              <div className="scenario-row">
                <span className="scenario-icon up">
                  <ArrowUp size={14} />
                </span>

                <div>
                  <span>Upside</span>
                  <strong>
                    {riskAnalysis?.upside_rate_usd_per_mt !==
                    undefined
                      ? `$${Number(
                          riskAnalysis.upside_rate_usd_per_mt
                        ).toFixed(2)} / MT`
                      : "—"}
                  </strong>
                </div>
              </div>
            </div>

            <div className="risk-summary">
              <ShieldCheck size={16} />

              <p>
                {recommendation?.reason ||
                  "Run the analysis to receive the decision engine's risk-aware recommendation."}
              </p>
            </div>
          </div>
        </section>

        <section className="data-note">
          <div className="data-note-icon">
            <ShieldCheck size={17} />
          </div>

          <div>
            <strong>Prototype data transparency</strong>

            <p>
              The ML layer currently forecasts a Baltic vessel-class
              market index. Freight USD/MT, bunker costs, port
              charges, sailing time and queue time shown in this
              prototype are assumptions and are not live
              route-specific commercial quotations.
            </p>
          </div>
        </section>

        <footer className="footer">
          <div>
            <strong>Freight Prediction</strong>
            <span>
              AI-powered bulk chartering decision support
            </span>
          </div>

          <span>
            International origins → India's East Coast
          </span>
        </footer>
      </main>

      {sidebarOpen && (
        <button
          className="close-menu"
          onClick={() => setSidebarOpen(false)}
          aria-label="Close navigation"
        >
          <X size={20} />
        </button>
      )}

      {analyzed && !error && (
        <div className="toast">
          <CheckCircle2 size={15} />
          Strategy analyzed successfully
        </div>
      )}
    </div>
  );
}

export default App;