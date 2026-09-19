import { useEffect, useMemo, useState } from "react";
import NotFound from "./NotFound";
import axios from "axios";
import {
  Anchor,
  ArrowDown,
  ArrowUp,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  ChevronDown,
  CloudRain,
  Clock3,
  Container,
  Gauge,
  Globe2,
  Menu,
  MapPin,
  Moon,
  Navigation,
  Sun,
  ShieldCheck,
  Waves,
  Wind,
  Sparkles,
  TrendingUp,
  X,
} from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  ReferenceLine,
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

const formatRoutePointName = (point) =>
  point
    .toLowerCase()
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");

const VESSEL_CLASS_NAMES = {
  HSI: "Handysize",
  SI: "Supramax",
  PI: "Panamax",
  CI: "Capesize",
};

const formatWeatherValue = (value, suffix = "") => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return null;
  }
  return String(Number(value)) + suffix;
};

const formatUpdatedTime = (value) => {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
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
  disabled = false,
}) {
  return (
    <label className="field">
      <span className="field-label">{label}</span>

      <div className="select-control">
        <select
          value={value}
          disabled={disabled}
          onChange={(e) => onChange(e.target.value)}
        >
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
  const [theme, setTheme] = useState(() => {
    const savedTheme = localStorage.getItem("freight-theme");
    const initialTheme = savedTheme === "light" ? "light" : "dark";

    document.documentElement.dataset.theme = initialTheme;

    return initialTheme;
  });

  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("freight-theme", theme);
  }, [theme]);

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
  const [scenarioDirty, setScenarioDirty] = useState(false);
  const [loadingStage, setLoadingStage] = useState("Preparing analysis");
  const [activeSection, setActiveSection] = useState("overview");

  const availableOriginPorts = ORIGIN_PORTS[originCountry];

  useEffect(() => {
    if (!availableOriginPorts.includes(originPort)) {
      setOriginPort(availableOriginPorts[0]);
    }
  }, [originCountry, availableOriginPorts, originPort]);

  useEffect(() => {
    if (!loading) {
      setLoadingStage("Preparing analysis");
      return undefined;
    }

    const stages = [
      "Validating scenario",
      "Fetching market context",
      "Sampling route weather",
      "Optimizing vessel economics",
      "Building forecast and risk view",
    ];

    let index = 0;
    setLoadingStage(stages[index]);

    const intervalId = window.setInterval(() => {
      index = (index + 1) % stages.length;
      setLoadingStage(stages[index]);
    }, 1800);

    return () => window.clearInterval(intervalId);
  }, [loading]);

  useEffect(() => {
    const ids = ["overview", "forecast", "vessels", "ports", "weather", "contract"];
    const sections = ids
      .map((id) => document.getElementById(id))
      .filter(Boolean);

    if (!sections.length) return undefined;

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio);

        if (visible[0]?.target?.id) {
          setActiveSection(visible[0].target.id);
        }
      },
      {
        rootMargin: "-15% 0px -65% 0px",
        threshold: [0.05, 0.2, 0.5],
      }
    );

    sections.forEach((section) => observer.observe(section));
    return () => observer.disconnect();
  }, []);

  const forecast = result?.forecast;
  const vesselDecision = result?.vessel_decision;
  const contractDecision = result?.contract_decision;
  const riskAnalysis = contractDecision?.risk_analysis;
  const recommendation = result?.final_recommendation;
  const congestion = result?.congestion;
  const weather = result?.weather;
  const noFeasibleVessel =
    result?.status === "NO_ECONOMICALLY_FEASIBLE_VESSEL";
  const diagnosticAction =
    result?.diagnostic?.recommended_action;

  const forecastClass = forecast?.vessel_class || null;
  const forecastClassName =
    VESSEL_CLASS_NAMES[forecastClass] || "Vessel-Class";
  const forecastHeader = forecastClass
    ? forecastClass + " · " + forecastClassName + " Index"
    : "Awaiting analysis";
  const forecastStatLabel = forecastClass
    ? "Current " + forecastClass + " Index"
    : "Current Vessel Index";

  const weatherSourceStatus = weather?.source_status || {};
  const missingWeatherSources = [
    weatherSourceStatus.marine !== "AVAILABLE" ? "marine" : null,
    weatherSourceStatus.atmospheric !== "AVAILABLE" ? "atmospheric" : null,
  ].filter(Boolean);
  const weatherWarningText =
    missingWeatherSources.length === 0
      ? ""
      : "Missing " +
        missingWeatherSources.join(" and ") +
        " weather data. The weather risk score is calculated from the conditions that were returned.";
  const weatherUpdatedAt = formatUpdatedTime(
    weather?.data_fetched_at_utc
  );

  const loadingDataUsed = congestion?.loading_data_used === true;
  const dischargeDataUsed = congestion?.discharge_data_used === true;
  const allPortDataUsed = congestion?.all_ports_have_real_data === true;
  const anyPortDataUsed = loadingDataUsed || dischargeDataUsed;
  const portDataState = allPortDataUsed
    ? "VERIFIED"
    : anyPortDataUsed
      ? "MIXED"
      : "PROTOTYPE";
  const portWarningText =
    portDataState === "VERIFIED"
      ? ""
      : portDataState === "MIXED"
        ? "One side of the route uses verified observations; the other side still uses prototype fallback values."
        : "No verified congestion observation is available for this route. Queue figures remain prototype assumptions.";

  const forecastData = useMemo(() => {
    const horizons = forecast?.all_horizons;

    if (!horizons) {
      return [];
    }

    const currentIndex =
      forecast?.current_index ??
      horizons["30"]?.current_index ??
      null;

    if (currentIndex === null || currentIndex === undefined) {
      return [];
    }

    return [
      {
        horizon: "Current",
        value: Number(currentIndex),
        change: 0,
      },
      ...["7", "30", "60", "90"]
        .filter(
          (key) =>
            horizons[key] &&
            horizons[key]?.predicted_index !== null &&
            horizons[key]?.predicted_index !== undefined
        )
        .map((key) => ({
          horizon: `${key}D`,
          value: Number(horizons[key].predicted_index),
          change: Number(horizons[key]?.change_percent ?? 0),
        })),
    ];
  }, [forecast]);

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
    forecast?.current_index ?? null;

  const change30 =
    forecast?.change_percent_30d ?? null;

  const predicted30Value =
    forecast?.predicted_30d_index ?? null;

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

  const invalidateAnalysis = () => {
    setResult(null);
    setAnalyzed(false);
    setError("");
    setScenarioDirty(true);
  };

  const handleCountryChange = (country) => {
    setOriginCountry(country);
    setOriginPort(ORIGIN_PORTS[country][0]);
    invalidateAnalysis();
  };

  const handleAnalyze = async () => {
    if (loading) return;
  
    setLoading(true);
    setError("");
    setResult(null);
    setAnalyzed(false);
    setScenarioDirty(false);
  
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
  
      const apiResult = response.data;
  
      setResult(apiResult);
  
      if (apiResult?.status === "SUCCESS") {
        setAnalyzed(true);
        setScenarioDirty(false);
  
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
      setScenarioDirty(false);
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

  const systemStatus = loading
    ? loadingStage
    : error
      ? "Analysis error"
      : scenarioDirty
        ? "Scenario modified"
        : result
          ? "Result ready"
          : "Ready to analyze";

  const systemStatusClass = loading
    ? "loading"
    : error
      ? "error"
      : scenarioDirty
        ? "warning"
        : result
          ? "success"
          : "ready";

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
            className={activeSection === "overview" ? "active" : ""}
            href="#overview"
            onClick={() => setSidebarOpen(false)}
          >
            <Gauge size={17} />
            Overview
          </a>

          <a
            className={activeSection === "forecast" ? "active" : ""}
            href="#forecast"
            onClick={() => setSidebarOpen(false)}
          >
            <TrendingUp size={17} />
            Market Forecast
          </a>

          <a
            className={activeSection === "vessels" ? "active" : ""}
            href="#vessels"
            onClick={() => setSidebarOpen(false)}
          >
            <Container size={17} />
            Vessel Economics
          </a>

          <a
            className={activeSection === "ports" ? "active" : ""}
            href="#ports"
            onClick={() => setSidebarOpen(false)}
          >
            <MapPin size={17} />
            Port Intelligence
          </a>

          <a
            className={activeSection === "weather" ? "active" : ""}
            href="#weather"
            onClick={() => setSidebarOpen(false)}
          >
            <CloudRain size={17} />
            Weather Intelligence
          </a>

          <a
            className={activeSection === "contract" ? "active" : ""}
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

          <div className="topbar-actions">
            <button
              type="button"
              className="theme-toggle"
              onClick={() =>
                setTheme((currentTheme) =>
                  currentTheme === "dark" ? "light" : "dark"
                )
              }
              aria-label={`Switch to ${
                theme === "dark" ? "light" : "dark"
              } mode`}
              title={`Switch to ${
                theme === "dark" ? "light" : "dark"
              } mode`}
            >
              {theme === "dark" ? (
                <Sun size={17} />
              ) : (
                <Moon size={17} />
              )}
              <span>
                {theme === "dark" ? "LIGHT" : "DARK"}
              </span>
            </button>

            <div
              className={`system-status ${systemStatusClass}`}
              aria-live="polite"
            >
              <span className={`status-dot ${systemStatusClass}`} />
              <span>{systemStatus}</span>
            </div>
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

            <div className="scenario-status" aria-live="polite">
              <span className={`status-dot ${systemStatusClass}`} />
              {loading
                ? loadingStage
                : scenarioDirty
                  ? "Scenario changed · analyze again"
                  : result
                    ? "Analysis complete"
                    : "Ready to analyze"}
            </div>
          </div>

          <div className="scenario-grid">
            <label className="field">
              <span className="field-label">Commodity</span>

              <div className="input-control">
                <input
                  value={commodity}
                  disabled={loading}
                  onChange={(e) => {
                    setCommodity(e.target.value);
                    invalidateAnalysis();
                  }}
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
                  disabled={loading}
                  onChange={(e) => {
                    setCargo(e.target.value);
                    invalidateAnalysis();
                  }}
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
              disabled={loading}
            />

            <SelectField
              label="Origin Port"
              value={originPort}
              onChange={(value) => {
                setOriginPort(value);
                invalidateAnalysis();
              }}
              options={availableOriginPorts}
              icon={Navigation}
              disabled={loading}
            />

            <SelectField
              label="Indian Destination"
              value={destinationPort}
              onChange={(value) => {
                setDestinationPort(value);
                invalidateAnalysis();
              }}
              options={DESTINATION_PORTS}
              icon={MapPin}
              disabled={loading}
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
                  disabled={loading}
                  onChange={(e) => {
                    setDuration(e.target.value);
                    invalidateAnalysis();
                  }}
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
                  disabled={loading}
                  onChange={(e) => {
                    setVoyages(e.target.value);
                    invalidateAnalysis();
                  }}
                />

                <span>VOYAGES</span>
              </div>
            </label>

            <button
              type="button"
              className="analyze-btn"
              onClick={handleAnalyze}
              disabled={loading}
              aria-busy={loading}
            >
              {loading ? (
                <>
                  <Gauge size={16} />
                  {loadingStage}...
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

                {!noFeasibleVessel && (
                  <span className="decision-action-label">
                    {displayAction}
                  </span>
                )}

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
              label={forecastStatLabel}
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
              label="30D Forecast Rate"
              value={
                forecastRate !== null
                  ? `$${Number(forecastRate).toFixed(2)}/MT`
                  : "—"
              }
              subtext={
                forecast
                  ? forecastClass + " · " + forecastClassName + " market outlook"
                  : "Awaiting forecast"
              }
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
                  {forecast ? forecastHeader : "Vessel-Class Index Outlook"}
                </h3>

                <p className="panel-description">
                  Model-based vessel-class market projection
                </p>
              </div>

              <span className="chart-tag">
                {forecast
                  ? forecastClass + " · " + forecastClassName
                  : "AWAITING ANALYSIS"}
              </span>
            </div>

            <div className="chart-area">
              {forecastData.length === 0 ? (
                <div className="chart-empty-state">
                  <TrendingUp size={24} />
                  <strong>
                    {result
                      ? "Forecast unavailable for this scenario"
                      : "Forecast appears after analysis"}
                  </strong>
                  <span>
                    {result
                      ? "No model forecast is available in this response."
                      : "Run Analyze Strategy to load the model-generated 7D, 30D and 60D outlook."}
                  </span>
                </div>
              ) : (
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
                        stopColor="#dbe92f"
                        stopOpacity={0.22}
                      />
                      <stop
                        offset="100%"
                        stopColor="#dbe92f"
                        stopOpacity={0}
                      />
                    </linearGradient>
                  </defs>

                  <CartesianGrid
                    strokeDasharray="3 4"
                    vertical={false}
                    stroke="var(--chart-grid)"
                  />

                  <XAxis
                    dataKey="horizon"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: "var(--chart-text)", fontSize: 11 }}
                    padding={{ left: 8, right: 8 }}
                  />

                  <YAxis
                    axisLine={false}
                    tickLine={false}
                    width={58}
                    tick={{ fill: "var(--chart-text)", fontSize: 10 }}
                    domain={["auto", "auto"]}
                    tickFormatter={(value) =>
                      Number(value).toLocaleString("en-US", {
                        maximumFractionDigits: 0,
                      })
                    }
                  />

                  <ReferenceLine
                    x="Current"
                    stroke="var(--chart-reference)"
                    strokeDasharray="4 4"
                  />

                  <Tooltip
                    cursor={{
                      stroke: "var(--chart-reference)",
                      strokeDasharray: "4 4",
                    }}
                    formatter={(value) => [
                      Number(value).toFixed(2),
                      `${forecast?.vessel_class || "Vessel"} Index`,
                    ]}
                    labelFormatter={(label) =>
                      `${label} outlook`
                    }
                    contentStyle={{
                      background: "var(--tooltip-bg)",
                      border: "1px solid var(--tooltip-border)",
                      borderRadius: "8px",
                      color: "var(--tooltip-text)",
                    }}
                    labelStyle={{
                      color: "var(--tooltip-label)",
                      marginBottom: "4px",
                    }}
                    itemStyle={{
                      color: "#dbe92f",
                    }}
                  />

                  <Area
                    type="monotone"
                    dataKey="value"
                    stroke="#dbe92f"
                    strokeWidth={2.5}
                    fill="url(#forecastFill)"
                    dot={{
                      r: 4,
                      fill: "#dbe92f",
                      stroke: "#0f171d",
                      strokeWidth: 2,
                    }}
                    activeDot={{
                      r: 6,
                      fill: "#dbe92f",
                      stroke: "#ffffff",
                      strokeWidth: 2,
                    }}
                  />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>

            {forecastData.length > 0 && (
              <>
                <div className="forecast-summary-strip">
                  <div><span>CURRENT INDEX</span><strong>{formatNumber(currentIndex, 0)}</strong></div>
                  <div><span>30D FORECAST</span><strong>{predicted30Value !== null ? Number(predicted30Value).toFixed(2) : "—"}</strong></div>
                  <div><span>30D CHANGE</span><strong className={Number(change30) >= 0 ? "lime" : "negative"}>{formatPercentage(change30)}</strong></div>
                </div>
                <div className="forecast-cards">
                  {forecastData.slice(1).map((point) => {
                    const horizonKey = point.horizon.replace("D", "");
                    const horizonResult = forecast?.all_horizons?.[horizonKey];
                    return (
                      <div className="forecast-item" key={point.horizon}>
                        <span>{point.horizon}</span>
                        <strong>{Number(point.value).toFixed(2)}</strong>
                        <small className={point.change >= 0 ? "change positive" : "change negative"}>
                          {point.change >= 0 ? <ArrowUp size={11} /> : <ArrowDown size={11} />}
                          {formatPercentage(point.change)}
                        </small>
                        {horizonResult?.confidence && (
                          <span className="forecast-confidence" title="Historical validation strength for this forecast horizon">
                            {horizonResult.confidence}
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
                <div className="forecast-confidence-note">
                  Confidence reflects historical validation strength for each vessel-class forecast horizon.
                </div>
              </>
            )}
          </div>

          <div id="ports" className="panel port-panel">
            <div className="panel-header">
              <div>
                <span className="section-kicker">PORT INTELLIGENCE</span>
                <h3>Port congestion</h3>
                <p className="panel-description">Current queue exposure and data coverage</p>
              </div>
              <span className="risk-badge">{riskLevel === "—" ? "AWAITING ANALYSIS" : riskLevel + " CONGESTION"}</span>
            </div>

            <div className="port-route-card">
              <div className="route-place"><div className="route-marker origin-marker"><Globe2 size={15} /></div><div><span>ORIGIN</span><strong>{scenarioOrigin}</strong><small>{scenarioCountry}</small></div></div>
              <div className="route-connector"><span>INTERNATIONAL BULK TRADE</span><div /></div>
              <div className="route-place"><div className="route-marker destination-marker"><MapPin size={15} /></div><div><span>DESTINATION</span><strong>{scenarioDestination}</strong><small>East Coast India</small></div></div>
            </div>

            <div className="queue-list">
              <div><span>Origin queue</span><strong>{loadingQueue !== null ? `${Number(loadingQueue).toFixed(1)} days` : "—"}</strong></div>
              <div><span>Destination queue</span><strong>{dischargeQueue !== null ? `${Number(dischargeQueue).toFixed(1)} days` : "—"}</strong></div>
              <div><span>Total queue exposure</span><strong>{totalQueue !== null ? `${Number(totalQueue).toFixed(1)} days` : "—"}</strong></div>
              <div><span>Data coverage</span><strong className="muted-value">{congestion ? portDataState : "AWAITING"}</strong></div>
            </div>

            {congestion && (
              <div className="port-source-grid">
                <div className="port-source-item"><div><span>Origin</span><small>{congestion.loading?.source_name || "Queue source"}</small></div><strong className={loadingDataUsed ? "source-available" : "source-unavailable"}>{loadingDataUsed ? "Verified" : "Prototype"}</strong></div>
                <div className="port-source-item"><div><span>Destination</span><small>{congestion.discharge?.source_name || "Queue source"}</small></div><strong className={dischargeDataUsed ? "source-available" : "source-unavailable"}>{dischargeDataUsed ? "Verified" : "Prototype"}</strong></div>
              </div>
            )}

            {congestion?.discharge?.observation_date && (
              <div className="port-source-meta"><span>DESTINATION OBSERVATION</span><strong>{congestion.discharge.source_name || "Verified source"}</strong><small>Observed {congestion.discharge.observation_date}</small></div>
            )}

            {congestion && portWarningText && (
              <div className="warning-box">
                <Clock3 size={16} />
                <p>{portWarningText}</p>
              </div>
            )}
          </div>

        </section>

        <section id="weather" className="panel weather-panel">
          <div className="panel-header">
            <div>
              <span className="section-kicker">WEATHER INTELLIGENCE</span>
              <h3>Route weather impact</h3>
              <p className="panel-description">
                {weather
                  ? weather.status === "PARTIAL"
                    ? "Seven-day route-sampled forecast · partial source coverage"
                    : "Seven-day route-sampled marine and atmospheric forecast"
                  : "Seven-day route-sampled marine and atmospheric forecast"}
              </p>
            </div>
            <span className={`weather-status-badge ${weather?.status === "AVAILABLE" ? "available" : weather?.status === "PARTIAL" ? "partial" : "unavailable"}`}>
              {weather?.status === "AVAILABLE"
                ? `${weather.risk_level} RISK`
                : weather?.status === "PARTIAL"
                  ? `PARTIAL · ${weather.risk_level} RISK`
                  : result
                    ? "UNAVAILABLE"
                    : "AWAITING ANALYSIS"}
            </span>
          </div>

          {!weather || !["AVAILABLE", "PARTIAL"].includes(weather.status) ? (
            <div className="weather-empty-state">
              <CloudRain size={26} />
              <strong>
                {result ? "Weather data unavailable" : "Weather impact appears after analysis"}
              </strong>
              <span>
                {result
                  ? "The decision engine kept the base route estimate because no usable weather data was returned."
                  : "Run Analyze Strategy to fetch route weather and calculate its effect on sailing time and bunker cost."}
              </span>
            </div>
          ) : (
            <>
              <div className="weather-metrics">
                <div className="weather-metric weather-risk-metric">
                  <CloudRain size={18} />
                  <span title="Composite score from the available route-sampled weather variables">Weather risk score</span>
                  <strong>{weather.weather_risk_score}/100</strong>
                  <small>{weather.risk_level} risk</small>
                  <div className="weather-risk-scale">
                    <div style={{ width: String(Math.max(0, Math.min(100, Number(weather.weather_risk_score) || 0))) + "%" }} />
                  </div>
                </div>
                <div className="weather-metric"><Waves size={18} /><span title="90th percentile of sampled hourly wave height">90th percentile wave</span><strong>{formatWeatherValue(weather.p90_wave_height_m, " m") || <span className="weather-unavailable">Unavailable</span>}</strong></div>
                <div className="weather-metric"><Wind size={18} /><span title="90th percentile of sampled hourly wind speed">90th percentile wind</span><strong>{formatWeatherValue(weather.p90_wind_speed_knots, " kn") || <span className="weather-unavailable">Unavailable</span>}</strong></div>
                <div className="weather-metric"><Wind size={18} /><span title="90th percentile of sampled hourly wind gusts">90th percentile gust</span><strong>{formatWeatherValue(weather.p90_wind_gust_knots, " kn") || <span className="weather-unavailable">Unavailable</span>}</strong></div>
                <div className="weather-metric"><Waves size={18} /><span title="90th percentile of sampled hourly swell height">90th percentile swell</span><strong>{formatWeatherValue(weather.p90_swell_height_m, " m") || <span className="weather-unavailable">Unavailable</span>}</strong></div>
                <div className="weather-metric"><Navigation size={18} /><span title="90th percentile of sampled hourly ocean current velocity">90th percentile current</span><strong>{formatWeatherValue(weather.p90_ocean_current_ms, " m/s") || <span className="weather-unavailable">Unavailable</span>}</strong></div>
              </div>

              <div className="weather-impact-row">
                <div><span>Base sailing time</span><strong>{weather.base_sailing_days} days</strong></div>
                <ArrowRight size={16} />
                <div><span>Weather-adjusted</span><strong>{weather.adjusted_sailing_days} days</strong></div>
                <div><span>Weather delay</span><strong>+{weather.weather_delay_days} days</strong></div>
                <div><span>Bunker impact</span><strong>+{Math.max(0, (Number(weather.bunker_cost_multiplier) - 1) * 100).toFixed(1)}%</strong><small>{Number(weather.bunker_cost_multiplier).toFixed(2)}× baseline</small></div>
              </div>

              <div className="weather-route">
                <span>ROUTE SAMPLED</span>
                <div className="weather-route-points">
                  {(weather.route_points || []).map((point, index) => (
                    <div
                      className={index > 0 && index < (weather.route_points || []).length - 1 ? "weather-route-point waypoint" : "weather-route-point"}
                      key={String(point) + "-" + String(index)}
                    >
                      <strong>{formatRoutePointName(point)}</strong>
                      {index < (weather.route_points || []).length - 1 && <ArrowRight size={13} />}
                    </div>
                  ))}
                </div>
              </div>

              <div className="weather-source-grid">
                <div className="weather-source-item">
                  <div><span>Marine</span><small>Waves · swell · current</small></div>
                  <strong className={weather.source_status?.marine === "AVAILABLE" ? "source-available" : "source-unavailable"}>{weather.source_status?.marine || "UNKNOWN"}</strong>
                </div>
                <div className="weather-source-item">
                  <div><span>Atmospheric</span><small>Wind · gust · visibility</small></div>
                  <strong className={weather.source_status?.atmospheric === "AVAILABLE" ? "source-available" : "source-unavailable"}>{weather.source_status?.atmospheric || "UNKNOWN"}</strong>
                </div>
              </div>

              {weather.status === "PARTIAL" && (
                <div className="weather-warning">
                  <CloudRain size={15} />
                  <p>{weatherWarningText}</p>
                </div>
              )}

              {weatherUpdatedAt && (
                <div className="weather-freshness">
                  <span>Forecast updated</span>
                  <strong>{weatherUpdatedAt}</strong>
                  <span>· {weather.forecast_days || 7}-day window</span>
                </div>
              )}

              <div className="weather-note">
                <CloudRain size={15} />
                <div>
                  <p>{weather.note}</p>
                  <small>Weather source: Open-Meteo{weather.status === "PARTIAL" ? " · partial coverage" : " · full source coverage"}</small>
                </div>
              </div>
            </>
          )}
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
              The ML layer forecasts a Baltic vessel-class market index.
              The voyage engine also samples Open-Meteo marine and atmospheric
              forecasts over the prototype route to adjust sailing time and
              bunker cost for the first 7 forecast days. Weather impact
              calculations, freight USD/MT, port charges and some queue inputs
              remain prototype assumptions and are not live route-specific
              commercial quotations.
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

function AppWithNotFound() {
  if (window.location.pathname !== "/") {
    return <NotFound />;
  }

  return <App />;
}

export default AppWithNotFound;