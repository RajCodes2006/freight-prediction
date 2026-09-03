import { useMemo, useState } from "react";
import {
  Anchor,
  ArrowDown,
  ArrowUp,
  BarChart3,
  Clock3,
  Container,
  Gauge,
  MapPin,
  Menu,
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

const forecastData = [
  { horizon: "Current", value: 1189, change: 0 },
  { horizon: "7D", value: 1186.79, change: -0.19 },
  { horizon: "30D", value: 1328.4, change: 11.72 },
  { horizon: "60D", value: 1280.71, change: 7.71 },
  { horizon: "90D", value: 1921.14, change: 61.58 },
];

const vesselData = [
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
    reason: "No feasible loading berth found",
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
        <Icon size={19} />
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

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [cargo, setCargo] = useState("60000");
  const [origin, setOrigin] = useState("Paradip");
  const [destination, setDestination] = useState("Visakhapatnam");
  const [duration, setDuration] = useState("6");
  const [voyages, setVoyages] = useState("6");
  const [analyzed, setAnalyzed] = useState(false);

  const cargoValue = Number(cargo) || 0;

  const recommendation = useMemo(() => {
    if (cargoValue >= 80000) {
      return {
        vessel: "Panamax",
        voyageCost: 1685400,
        costMt: 21.07,
        confidence: "MEDIUM",
      };
    }

    if (cargoValue >= 30000) {
      return {
        vessel: "Panamax",
        voyageCost: 744600,
        costMt: 24.82,
        confidence: "MEDIUM",
      };
    }

    return {
      vessel: "Handysize",
      voyageCost: 520000,
      costMt: 24.5,
      confidence: "MEDIUM",
    };
  }, [cargoValue]);

  const displayedVessels = useMemo(() => {
    if (cargoValue >= 80000) {
      return [
        {
          vessel: "Handysize",
          status: "Not Feasible",
          cost: null,
          costMt: null,
          reason: "Insufficient cargo capacity",
        },
        {
          vessel: "Supramax",
          status: "Not Feasible",
          cost: null,
          costMt: null,
          reason: "Insufficient cargo capacity",
        },
        {
          vessel: "Panamax",
          status: "Recommended",
          cost: 1685400,
          costMt: 21.07,
          reason: "Lowest feasible option",
        },
        {
          vessel: "Capesize",
          status: "Not Feasible",
          cost: null,
          costMt: null,
          reason: "No feasible loading berth found",
        },
      ];
    }

    if (cargoValue >= 30000) {
      return vesselData;
    }

    return [
      {
        vessel: "Handysize",
        status: "Recommended",
        cost: 520000,
        costMt: 24.5,
        reason: "Lowest feasible option",
      },
      {
        vessel: "Supramax",
        status: "Feasible",
        cost: 540000,
        costMt: 25.4,
        reason: "Higher voyage cost",
      },
      {
        vessel: "Panamax",
        status: "Feasible",
        cost: 570000,
        costMt: 26.2,
        reason: "Higher voyage cost",
      },
      {
        vessel: "Capesize",
        status: "Not Feasible",
        cost: null,
        costMt: null,
        reason: "No feasible loading berth found",
      },
    ];
  }, [cargoValue]);

  const handleAnalyze = () => {
    setAnalyzed(true);
    document
      .getElementById("results")
      ?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <div className="app-shell">
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
          <a className="active" href="#overview" onClick={() => setSidebarOpen(false)}>
            <Gauge size={18} />
            Overview
          </a>
          <a href="#forecast" onClick={() => setSidebarOpen(false)}>
            <TrendingUp size={18} />
            Forecast
          </a>
          <a href="#vessels" onClick={() => setSidebarOpen(false)}>
            <Container size={18} />
            Vessels
          </a>
          <a href="#ports" onClick={() => setSidebarOpen(false)}>
            <MapPin size={18} />
            Ports
          </a>
          <a href="#contract" onClick={() => setSidebarOpen(false)}>
            <BarChart3 size={18} />
            Contract
          </a>
        </nav>

        <div className="sidebar-note">
          <ShieldCheck size={17} />
          <div>
            <strong>Decision Support</strong>
            <span>Confidence-aware recommendations</span>
          </div>
        </div>
      </aside>

      {sidebarOpen && (
        <button
          className="mobile-overlay"
          aria-label="Close menu"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <main className="main-content">
        <header className="topbar">
          <button
            className="menu-btn"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open menu"
          >
            <Menu size={21} />
          </button>

          <div>
            <span className="eyebrow">EAST COAST INDIA</span>
            <h2>Freight Intelligence Dashboard</h2>
          </div>

          <div className="api-status">
            <span className="status-dot" />
            API ONLINE
          </div>
        </header>

        <section id="overview" className="hero-section">
          <div>
            <span className="section-kicker">
              <Sparkles size={15} />
              AI-POWERED CHARTERING
            </span>
            <h3>Make the next freight decision with confidence.</h3>
            <p>
              Forecast market direction, compare vessel economics, evaluate port
              risk, and identify the most attractive contracting strategy.
            </p>
          </div>

          <div className="hero-meta">
            <div>
              <span>MODEL</span>
              <strong>Multi-Horizon Ensemble</strong>
            </div>
            <div>
              <span>MARKET</span>
              <strong>Dry Bulk · Baltic Index</strong>
            </div>
          </div>
        </section>

        <section className="input-card">
          <div className="card-heading">
            <div>
              <span className="section-kicker">VOYAGE INPUT</span>
              <h3>Define your cargo requirement</h3>
            </div>
            <span className="input-badge">Live analysis</span>
          </div>

          <div className="form-grid">
            <label>
              Cargo Quantity
              <div className="input-wrap">
                <input
                  type="number"
                  min="1000"
                  value={cargo}
                  onChange={(e) => setCargo(e.target.value)}
                />
                <span>MT</span>
              </div>
            </label>

            <label>
              Origin Port
              <div className="input-wrap select-wrap">
                <select value={origin} onChange={(e) => setOrigin(e.target.value)}>
                  <option>Paradip</option>
                  <option>Dhamra</option>
                  <option>Gopalpur</option>
                  <option>Haldia</option>
                </select>
              </div>
            </label>

            <label>
              Destination
              <div className="input-wrap select-wrap">
                <select
                  value={destination}
                  onChange={(e) => setDestination(e.target.value)}
                >
                  <option>Visakhapatnam</option>
                  <option>Gangavaram</option>
                  <option>Gopalpur</option>
                  <option>Haldia</option>
                </select>
              </div>
            </label>

            <label>
              Contract Duration
              <div className="input-wrap">
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

            <label>
              Planned Voyages
              <div className="input-wrap">
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
              Analyze Voyage
              <Navigation size={17} />
            </button>
          </div>
        </section>

        <section id="results" className="dashboard-grid">
          <div className="recommendation-card">
            <div className="recommendation-top">
              <span className="section-kicker">RECOMMENDATION</span>
              <span className="confidence-pill">
                <span />
                {recommendation.confidence} CONFIDENCE
              </span>
            </div>

            <div className="recommendation-main">
              <div>
                <span className="label-small">RECOMMENDED VESSEL</span>
                <h3>{recommendation.vessel}</h3>
                <p>
                  Lowest estimated complete voyage cost under current prototype
                  assumptions.
                </p>
              </div>

              <div className="vessel-symbol">
                <Container size={42} strokeWidth={1.5} />
              </div>
            </div>

            <div className="recommendation-stats">
              <div>
                <span>Voyage Cost</span>
                <strong>{formatMoney(recommendation.voyageCost)}</strong>
              </div>
              <div>
                <span>Cost / MT</span>
                <strong>${recommendation.costMt.toFixed(2)}</strong>
              </div>
              <div>
                <span>30D Outlook</span>
                <strong className="green-text">+11.72%</strong>
              </div>
            </div>

            <div className="decision-strip">
              <div>
                <span>ACTION</span>
                <strong>CONSIDER CONTRACT</strong>
              </div>
              <div className="decision-arrow">→</div>
            </div>
          </div>

          <div className="stat-grid">
            <StatCard
              icon={TrendingUp}
              label="Current PI Index"
              value="1189"
              subtext="+11.72% projected in 30D"
              positive
            />
            <StatCard
              icon={BarChart3}
              label="Forecast Rate"
              value="$20.11/MT"
              subtext="30-day outlook"
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
              </div>
              <span className="chart-tag">PI · INDEX</span>
            </div>

            <div className="chart-area">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={forecastData}>
                  <defs>
                    <linearGradient id="forecastFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopOpacity={0.28} />
                      <stop offset="100%" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis
                    dataKey="horizon"
                    axisLine={false}
                    tickLine={false}
                    padding={{ left: 12, right: 12 }}
                  />
                  <YAxis
                    axisLine={false}
                    tickLine={false}
                    domain={["dataMin - 50", "dataMax + 100"]}
                    width={50}
                  />
                  <Tooltip
                    formatter={(value) => [`${Number(value).toFixed(2)}`, "Index"]}
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

            <div className="forecast-row">
              {forecastData.slice(1).map((point) => (
                <div className="forecast-point" key={point.horizon}>
                  <span>{point.horizon}</span>
                  <strong>{point.value.toFixed(2)}</strong>
                  <small
                    className={
                      point.change >= 0 ? "change positive" : "change negative"
                    }
                  >
                    {point.change >= 0 ? <ArrowUp size={12} /> : <ArrowDown size={12} />}
                    {point.change >= 0 ? "+" : ""}
                    {point.change.toFixed(2)}%
                  </small>
                </div>
              ))}
            </div>
          </div>

          <div id="ports" className="panel congestion-panel">
            <div className="panel-header">
              <div>
                <span className="section-kicker">PORT RISK</span>
                <h3>Congestion Monitor</h3>
              </div>
              <span className="risk-badge">MEDIUM</span>
            </div>

            <div className="route-visual">
              <div className="route-node">
                <div className="port-dot" />
                <div>
                  <span>ORIGIN</span>
                  <strong>{origin}</strong>
                </div>
              </div>

              <div className="route-line">
                <span>2.5 days total queue</span>
              </div>

              <div className="route-node">
                <div className="port-dot destination-dot" />
                <div>
                  <span>DESTINATION</span>
                  <strong>{destination}</strong>
                </div>
              </div>
            </div>

            <div className="queue-list">
              <div>
                <span>Loading queue</span>
                <strong>1.0 day</strong>
              </div>
              <div>
                <span>Discharge queue</span>
                <strong>1.5 days</strong>
              </div>
              <div>
                <span>Data status</span>
                <strong className="muted-value">Prototype fallback</strong>
              </div>
            </div>

            <div className="warning-box">
              <Clock3 size={17} />
              <span>
                Real port congestion observations are not connected yet. Current
                queue values are prototype assumptions.
              </span>
            </div>
          </div>
        </section>

        <section id="vessels" className="panel vessel-panel">
          <div className="panel-header">
            <div>
              <span className="section-kicker">VESSEL ECONOMICS</span>
              <h3>Feasibility & Cost Comparison</h3>
            </div>
            <span className="table-route">
              {origin} → {destination}
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
                  <th>Analysis</th>
                </tr>
              </thead>
              <tbody>
                {displayedVessels.map((row) => (
                  <tr key={row.vessel} className={row.status === "Recommended" ? "selected-row" : ""}>
                    <td>
                      <div className="vessel-name">
                        <div className="mini-vessel">
                          <Container size={16} />
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
                      {row.cost ? formatCompactMoney(row.cost) : "—"}
                    </td>
                    <td>
                      {row.costMt ? `$${row.costMt.toFixed(2)}` : "—"}
                    </td>
                    <td className="analysis-cell">{row.reason}</td>
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
                <span className="section-kicker">CONTRACT ECONOMICS</span>
                <h3>Spot vs Fixed Contract</h3>
              </div>
              <span className="savings-pill">9.32% SAVINGS</span>
            </div>

            <div className="contract-grid">
              <div className="contract-item">
                <span>Current Spot</span>
                <strong>$18.00<span>/MT</span></strong>
              </div>
              <div className="contract-item forecast">
                <span>Forecast</span>
                <strong>$20.11<span>/MT</span></strong>
              </div>
              <div className="contract-item contract-price">
                <span>Fixed Contract</span>
                <strong>$17.28<span>/MT</span></strong>
              </div>
            </div>

            <div className="savings-bar">
              <div className="savings-marker" />
              <div className="savings-text">
                <span>Expected contract savings</span>
                <strong>$639,000</strong>
              </div>
            </div>
          </div>

          <div className="panel risk-panel">
            <div className="panel-header">
              <div>
                <span className="section-kicker">RISK VIEW</span>
                <h3>Market Scenarios</h3>
              </div>
            </div>

            <div className="scenario-list">
              <div>
                <span className="scenario-icon down">
                  <ArrowDown size={15} />
                </span>
                <div>
                  <span>Downside</span>
                  <strong>$16.20/MT</strong>
                </div>
              </div>

              <div>
                <span className="scenario-icon current">
                  <Gauge size={15} />
                </span>
                <div>
                  <span>Current</span>
                  <strong>$18.00/MT</strong>
                </div>
              </div>

              <div>
                <span className="scenario-icon up">
                  <ArrowUp size={15} />
                </span>
                <div>
                  <span>Upside</span>
                  <strong>$19.80/MT</strong>
                </div>
              </div>
            </div>

            <p className="risk-footer">
              Positive forecast direction combined with a fixed-rate discount
              supports considering the contract.
            </p>
          </div>
        </section>

        <footer className="footer">
          <div>
            <strong>Freight Prediction</strong>
            <span>Intelligent Bulk Vessel Chartering</span>
          </div>
          <span>
            Prototype — Baltic vessel-class index forecasts and assumed voyage
            economics
          </span>
        </footer>
      </main>

      {sidebarOpen && (
        <button
          className="close-menu"
          onClick={() => setSidebarOpen(false)}
          aria-label="Close menu"
        >
          <X size={20} />
        </button>
      )}

      {analyzed && (
        <div className="toast">
          <Sparkles size={16} />
          Voyage analysis refreshed
        </div>
      )}
    </div>
  );
}

export default App;