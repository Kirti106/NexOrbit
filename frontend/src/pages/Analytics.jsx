import { useMemo } from "react";
import {
  ResponsiveContainer,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
} from "recharts";

import {
  Activity,
  Satellite,
  Orbit,
  AlertTriangle,
  TrendingUp,
} from "lucide-react";

import { ApiError } from "../components/ApiState";
import { useApi } from "../hooks/useApi";
import { getAnomalies, getLiveSatellites, getStats } from "../api/client";
import { ORBIT_COLORS, classifyOrbit, fmtInt, fmtUtc } from "../utils/format";
import "./Analytics.css";

const TYPE_COLORS = ["#65b9ff", "#b794f6", "#ffca72", "#7fd6a4", "#f08a8a"];
const tooltipStyle = { background: "#101a28", border: "1px solid #344b64", borderRadius: 8 };

function Analytics() {
  const stats = useApi(getStats, [], { intervalMs: 60000 });
  const live = useApi(() => getLiveSatellites(500), []);
  const anomalies = useApi(() => getAnomalies(10), []);

  const typeData = useMemo(
    () =>
      Object.entries(stats.data?.satellites_by_object_type || {}).map(([name, value], index) => ({
        name,
        value,
        color: TYPE_COLORS[index % TYPE_COLORS.length],
      })),
    [stats.data]
  );
  const typeTotal = typeData.reduce((sum, item) => sum + item.value, 0);

  const regimeData = useMemo(() => {
    const counts = { LEO: 0, MEO: 0, GEO: 0 };
    (live.data?.items || []).forEach((item) => {
      counts[classifyOrbit(item.altitude_km)] += 1;
    });
    return Object.entries(counts).map(([name, objects]) => ({ name, objects }));
  }, [live.data]);
  const sampleSize = live.data?.items.length || 0;

  const anomalyData = (anomalies.data?.items || []).map((item) => ({
    name: item.name || String(item.norad_id),
    score: Number(item.score.toFixed(1)),
  }));

  const value = (n) => (stats.data ? fmtInt(n) : "…");
  const types = stats.data?.satellites_by_object_type || {};

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <div>
          <p className="section-eyebrow">MISSION CONTROL / DATA INTELLIGENCE</p>
          <h1>Orbital Analytics</h1>
          <p>Explore orbital population, distribution and activity patterns.</p>
        </div>

        <span className="analytics-demo-badge">
          {stats.data ? `LIVE · ELEMENTS AS OF ${fmtUtc(stats.data.gp_freshest_at).toUpperCase()}` : stats.error ? "BACKEND OFFLINE" : "LOADING..."}
        </span>
      </div>

      <ApiError message={stats.error} title="Could not load statistics" />

      <div className="analytics-stats">
        <div className="analytics-stat-card">
          <Satellite />
          <span>TRACKED OBJECTS</span>
          <h2>{value(stats.data?.tracked_satellites)}</h2>
          <small><TrendingUp size={13} /> Catalogue size</small>
        </div>

        <div className="analytics-stat-card">
          <Orbit />
          <span>PAYLOADS</span>
          <h2>{value(types.PAYLOAD)}</h2>
          <small>Catalogued payload objects</small>
        </div>

        <div className="analytics-stat-card">
          <AlertTriangle />
          <span>PREDICTED EVENTS</span>
          <h2>{value(stats.data?.conjunctions)}</h2>
          <small>SOCRATES rows stored (incl. repeats)</small>
        </div>

        <div className="analytics-stat-card">
          <Activity />
          <span>HIGH-TIER EVENTS</span>
          <h2>{value(stats.data?.high_risk_conjunctions)}</h2>
          <small>Derived tier, not observed</small>
        </div>
      </div>

      <div className="analytics-main-grid">
        <section className="analytics-chart-card population-chart">
          <div className="analytics-card-heading">
            <div>
              <h3>ORBIT REGIME DISTRIBUTION</h3>
              <p>{sampleSize} objects in the live sample</p>
            </div>
            <Activity size={19} />
          </div>

          <div className="chart-area">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={regimeData}>
                <CartesianGrid stroke="#26384b" strokeDasharray="3 3" />
                <XAxis dataKey="name" stroke="#8494a8" fontSize={10} />
                <YAxis stroke="#8494a8" fontSize={10} allowDecimals={false} />
                <Tooltip contentStyle={tooltipStyle} />
                <Bar dataKey="objects" radius={[5, 5, 0, 0]}>
                  {regimeData.map((entry) => (
                    <Cell key={entry.name} fill={ORBIT_COLORS[entry.name]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="analytics-legend">
            <span><i className="leo-color" /> LEO</span>
            <span><i className="meo-color" /> MEO</span>
            <span><i className="geo-color" /> GEO</span>
          </div>
        </section>

        <section className="analytics-chart-card distribution-chart">
          <div className="analytics-card-heading">
            <div>
              <h3>OBJECT TYPES</h3>
              <p>Catalogue share by object type</p>
            </div>
            <Orbit size={19} />
          </div>

          <div className="donut-chart">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={typeData}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={65}
                  outerRadius={95}
                  paddingAngle={4}
                  stroke="none"
                >
                  {typeData.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} />
              </PieChart>
            </ResponsiveContainer>
            <div className="donut-center">
              <strong>{fmtInt(typeTotal)}</strong>
              <span>OBJECTS</span>
            </div>
          </div>

          <div className="distribution-legend">
            {typeData.map((item) => (
              <div key={item.name}>
                <span><i style={{ background: item.color }} /> {item.name}</span>
                <strong>{typeTotal ? ((item.value / typeTotal) * 100).toFixed(1) : 0}%</strong>
              </div>
            ))}
          </div>
        </section>

        <section className="analytics-chart-card activity-chart">
          <div className="analytics-card-heading">
            <div>
              <h3>UNUSUAL ORBIT PROFILES</h3>
              <p>Top 10 outlier scores (not maneuver detection)</p>
            </div>
            <TrendingUp size={19} />
          </div>

          <div className="chart-area">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={anomalyData}>
                <CartesianGrid stroke="#26384b" strokeDasharray="3 3" />
                <XAxis dataKey="name" stroke="#8494a8" fontSize={9} interval={0} angle={-25} textAnchor="end" height={60} />
                <YAxis stroke="#8494a8" fontSize={10} />
                <Tooltip contentStyle={tooltipStyle} />
                <Bar dataKey="score" fill="#65b9ff" radius={[5, 5, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="analytics-insight-card">
          <p className="section-eyebrow">ORBITAL INSIGHT</p>
          <h3>Understanding Earth's orbital environment</h3>
          <p>
            Figures come from the NexOrbit ML service: CelesTrak catalogue and
            element sets, plus SOCRATES close-approach predictions. The regime
            chart uses a sample of up to 500 objects, not the full catalogue.
          </p>
          <div className="insight-footer">
            <Activity size={17} />
            LIVE DATA · ML SERVICE
          </div>
        </section>
      </div>

      <p className="analytics-disclaimer">
        Conjunction figures are SOCRATES-derived predictions, not observed events.
        Outlier scores describe unusual element profiles within one snapshot and do
        not indicate maneuvers or failures.
      </p>
    </div>
  );
}

export default Analytics;
