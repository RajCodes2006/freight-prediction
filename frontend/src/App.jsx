import { useState } from "react";
import {
  Anchor,
  ArrowDown,
  ArrowUp,
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

const FORECAST_DATA = [
  { horizon: "Current", value: 1189, change: 0 },
  { horizon: "7D", value: 1186.79, change: -0.19 },
  { horizon: "30D", value: 1328.4, change: 11.72 },
  { horizon: "60D", value: 1280.71, change: 7.71 },
  { horizon: "90D", value: 1921.14, change: 61.58 },
];

const VESSEL_DATA = [
  {
    vessel: "Handysize",
    status: "Not Feasible",
    cost: null,
    costMt: null,
    reason: "Insufficient cargo capacity",
  },
  {
    vessel: "Supramax",
    status: "Feasible",
    cost: 1382200,
    costMt: 23.04,
    reason: "Higher estimated voyage cost",
  },
  {
    vessel: "Panamax",
    status: "Recommended",
    cost: 1309000,
    costMt: 21.82,
    reason: "Lowest estimated feasible voyage cost",
  },
  {
    vessel: "Capesize",
    status: "Not Feasible",
    cost: null,
    costMt: null,
    reason: "Loading berth constraint",
  },
];

function formatMoney(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatCompactMoney(value) {
  if (value >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(2)}M`;
  }

  if (value >= 1_000) {
    return `$${(value / 1_000).toFixed(0)}K`;
  }

  return formatMoney(value);
}

function StatCard({ icon: Icon, label, value, subtext, positive }) {
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
  const [originPort, setOriginPort] = useState(ORIGIN_PORTS.Australia[0]);
  const [destinationPort, setDestinationPort] = useState("Paradip");
  const [duration, setDuration] = useState("6");
  const [voyages, setVoyages] = useState("6");
  const [analyzed, setAnalyzed] = useState(false);

  const availableOriginPorts = ORIGIN_PORTS[originCountry];

  const handleCountryChange = (country) => {
    setOriginCountry(country);
    setOriginPort(ORIGIN_PORTS[country][0]);
  };

  const handleAnalyze = () => {
    setAnalyzed(true);

    setTimeout(() => {
      document
        .getElementById("results")
        ?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 50);
  };

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
            <span className="eyebrow">GLOBAL ORIGIN → EAST COAST INDIA</span>
            <h2>Freight Intelligence Dashboard</h2>
          </div>

          <div className="system-status">
            <span className="status-dot" />
            <span>SYSTEM READY</span>
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
              Forecast dry-bulk market conditions, compare vessel economics,
              evaluate port constraints and assess contract risk before fixing
              your next voyage.
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
              <span className="section-kicker">VOYAGE SCENARIO</span>
              <h3>Build your procurement scenario</h3>
            </div>

            <div className="scenario-status">
              <span className="status-dot" />
              Prototype model ready
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
              onChange={setOriginPort}
              options={availableOriginPorts}
              icon={Navigation}
            />

            <SelectField
              label="Indian Destination"
              value={destinationPort}
              onChange={setDestinationPort}
              options={DESTINATION_PORTS}
              icon={MapPin}
            />

            <label className="field">
              <span className="field-label">Contract Duration</span>

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
              <span className="field-label">Planned Voyages</span>

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

            <button className="analyze-btn" onClick={handleAnalyze}>
              <Sparkles size={16} />
              Analyze Strategy
            </button>
          </div>
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
                  Analysis complete
                </span>
              </div>

              <span className="confidence-pill">
                <span />
                MEDIUM CONFIDENCE
              </span>
            </div>

            <div className="decision-main">
              <div>
                <span className="label-small">RECOMMENDED VESSEL</span>
                <h3>Panamax</h3>

                <div className="route-summary">
                  <span>{originCountry}</span>
                  <ArrowRight />
                  <span>{originPort}</span>
                  <ArrowRight />
                  <span>{destinationPort}</span>
                </div>

                <p>
                  Panamax provides the lowest estimated feasible voyage cost
                  under the current prototype assumptions.
                </p>
              </div>

              <div className="decision-vessel-icon">
                <Container size={44} strokeWidth={1.4} />
              </div>
            </div>

            <div className="decision-metrics">
              <div>
                <span>VOYAGE COST</span>
                <strong>$1.309M</strong>
              </div>

              <div>
                <span>COST / MT</span>
                <strong>$21.82</strong>
              </div>

              <div>
                <span>30D OUTLOOK</span>
                <strong className="lime">+11.72%</strong>
              </div>
            </div>

            <div className="action-banner">
              <div>
                <span>RECOMMENDED ACTION</span>
                <strong>CONSIDER CONTRACT</strong>
              </div>

              <Navigation size={18} />
            </div>
          </div>

          <div className="quick-stats">
            <StatCard
              icon={TrendingUp}
              label="Current PI Index"
              value="1,189"
              subtext="+11.72% projected in 30D"
              positive
            />

            <StatCard
              icon={BarChart3}
              label="Forecast Rate"
              value="$20.11/MT"
              subtext="30-day market scenario"
              positive
            />

            <StatCard
              icon={Clock3}
              label="Port Queue"
              value="2.5 days"
              subtext="Medium congestion"
            />

            <StatCard
              icon={ShieldCheck}
              label="Expected Savings"
              value="$639K"
              subtext="9.32% vs expected spot"
              positive
            />
          </div>
        </section>

        <section id="forecast" className="content-grid">
          <div className="panel chart-panel">
            <div className="panel-header">
              <div>
                <span className="section-kicker">MARKET FORECAST</span>
                <h3>Panamax Index Outlook</h3>
                <p className="panel-description">
                  Model-based vessel-class market projection
                </p>
              </div>

              <span className="chart-tag">PI · BALTIC INDEX</span>
            </div>

            <div className="chart-area">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={FORECAST_DATA}>
                  <defs>
                    <linearGradient
                      id="forecastFill"
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop offset="0%" stopOpacity={0.3} />
                      <stop offset="100%" stopOpacity={0} />
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
                    domain={["dataMin - 50", "dataMax + 100"]}
                  />

                  <Tooltip
                    formatter={(value) => [
                      Number(value).toFixed(2),
                      "Index",
                    ]}
                    labelFormatter={(label) => `${label} outlook`}
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
              {FORECAST_DATA.slice(1).map((point) => (
                <div className="forecast-item" key={point.horizon}>
                  <span>{point.horizon}</span>
                  <strong>{point.value.toFixed(2)}</strong>

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

                    {point.change >= 0 ? "+" : ""}
                    {point.change.toFixed(2)}%
                  </small>
                </div>
              ))}
            </div>
          </div>

          <div id="ports" className="panel port-panel">
            <div className="panel-header">
              <div>
                <span className="section-kicker">PORT INTELLIGENCE</span>
                <h3>Destination risk</h3>
                <p className="panel-description">
                  Current prototype queue assessment
                </p>
              </div>

              <span className="risk-badge">MEDIUM</span>
            </div>

            <div className="port-route-card">
              <div className="route-place">
                <div className="route-marker origin-marker">
                  <Globe2 size={15} />
                </div>

                <div>
                  <span>ORIGIN</span>
                  <strong>{originPort}</strong>
                  <small>{originCountry}</small>
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
                  <strong>{destinationPort}</strong>
                  <small>East Coast India</small>
                </div>
              </div>
            </div>

            <div className="queue-list">
              <div>
                <span>Loading / origin queue</span>
                <strong>1.0 day</strong>
              </div>

              <div>
                <span>Destination queue</span>
                <strong>1.5 days</strong>
              </div>

              <div>
                <span>Total queue exposure</span>
                <strong>2.5 days</strong>
              </div>

              <div>
                <span>Data source</span>
                <strong className="muted-value">Prototype fallback</strong>
              </div>
            </div>

            <div className="warning-box">
              <Clock3 size={16} />

              <p>
                Real port congestion observations are not connected yet.
                Current queue figures remain prototype assumptions.
              </p>
            </div>
          </div>
        </section>

        <section id="vessels" className="panel vessel-panel">
          <div className="panel-header">
            <div>
              <span className="section-kicker">VESSEL ECONOMICS</span>
              <h3>Feasibility & cost comparison</h3>
              <p className="panel-description">
                Prototype voyage economics for the selected cargo scenario
              </p>
            </div>

            <span className="table-route">
              {cargo || "60,000"} MT · {destinationPort}
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
                {VESSEL_DATA.map((row) => (
                  <tr
                    key={row.vessel}
                    className={
                      row.status === "Recommended"
                        ? "selected-row"
                        : ""
                    }
                  >
                    <td>
                      <div className="vessel-name">
                        <div className="mini-vessel">
                          <Container size={15} />
                        </div>

                        <strong>{row.vessel}</strong>
                      </div>
                    </td>

                    <td>
                      <span
                        className={`table-status ${
                          row.status === "Recommended"
                            ? "recommended"
                            : row.status === "Feasible"
                            ? "feasible"
                            : "not-feasible"
                        }`}
                      >
                        {row.status}
                      </span>
                    </td>

                    <td>
                      {row.cost
                        ? formatCompactMoney(row.cost)
                        : "—"}
                    </td>

                    <td>
                      {row.costMt
                        ? `$${row.costMt.toFixed(2)}`
                        : "—"}
                    </td>

                    <td className="analysis-cell">
                      {row.reason}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section id="contract" className="content-grid bottom-grid">
          <div className="panel contract-panel">
            <div className="panel-header">
              <div>
                <span className="section-kicker">CONTRACT STRATEGY</span>
                <h3>Spot vs fixed contract</h3>
                <p className="panel-description">
                  Six-month procurement scenario
                </p>
              </div>

              <span className="savings-pill">9.32% SAVINGS</span>
            </div>

            <div className="contract-grid">
              <div className="contract-item">
                <span>CURRENT SPOT</span>
                <strong>$18.00</strong>
                <small>/MT</small>
              </div>

              <div className="contract-item forecast-price">
                <span>FORECAST</span>
                <strong>$20.11</strong>
                <small>/MT</small>
              </div>

              <div className="contract-item fixed-price">
                <span>FIXED CONTRACT</span>
                <strong>$17.28</strong>
                <small>/MT</small>
              </div>
            </div>

            <div className="savings-panel">
              <div>
                <span>EXPECTED CONTRACT SAVINGS</span>
                <strong>$639,000</strong>
              </div>

              <div className="savings-progress">
                <div />
              </div>

              <small>
                Based on current prototype contract assumptions
              </small>
            </div>
          </div>

          <div className="panel risk-panel">
            <div className="panel-header">
              <div>
                <span className="section-kicker">RISK ANALYSIS</span>
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
                  <strong>$16.20 / MT</strong>
                </div>
              </div>

              <div className="scenario-row">
                <span className="scenario-icon current">
                  <Gauge size={14} />
                </span>

                <div>
                  <span>Current</span>
                  <strong>$18.00 / MT</strong>
                </div>
              </div>

              <div className="scenario-row">
                <span className="scenario-icon up">
                  <ArrowUp size={14} />
                </span>

                <div>
                  <span>Upside</span>
                  <strong>$19.80 / MT</strong>
                </div>
              </div>
            </div>

            <div className="risk-summary">
              <ShieldCheck size={16} />

              <p>
                Positive market direction and a discounted fixed contract
                currently support <strong>CONSIDER CONTRACT</strong>.
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
              The ML layer currently forecasts a Baltic vessel-class market
              index. Freight USD/MT, bunker costs, port charges, sailing time,
              and queue time shown in this prototype are assumptions and are
              not live route-specific commercial quotations.
            </p>
          </div>
        </section>

        <footer className="footer">
          <div>
            <strong>Freight Prediction</strong>
            <span>AI-powered bulk chartering decision support</span>
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

      {analyzed && (
        <div className="toast">
          <CheckCircle2 size={15} />
          Scenario analyzed successfully
        </div>
      )}
    </div>
  );
}

function ArrowRight() {
  return <span className="route-arrow">→</span>;
}

export default App;