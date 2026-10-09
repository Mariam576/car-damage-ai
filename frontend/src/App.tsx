import { useEffect, useState } from "react";
import { api } from "./api";
import type { Health, Report } from "./types";
import { Estimate } from "./components/Estimate";
import { PriceList } from "./components/PriceList";
import { ReportsList } from "./components/ReportsList";
import { ReportView } from "./components/ReportView";

type Route = { page: "estimate" } | { page: "reports" } | { page: "report"; id: string } | { page: "prices" };

function parse(hash: string): Route {
  const path = hash.replace(/^#/, "");
  const match = path.match(/^\/reports\/(.+)$/);
  if (match) return { page: "report", id: decodeURIComponent(match[1]) };
  if (path === "/reports") return { page: "reports" };
  if (path === "/prices") return { page: "prices" };
  return { page: "estimate" };
}

function useRoute(): Route {
  const [route, setRoute] = useState(() => parse(window.location.hash));
  useEffect(() => {
    const onChange = () => {
      setRoute(parse(window.location.hash));
      window.scrollTo(0, 0);
    };
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return route;
}

function SavedReport({ id }: { id: string }) {
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    setReport(null);
    setError(null);
    api.report(id).then(setReport, (e: Error) => setError(e.message));
  }, [id]);
  if (error) return <p className="alert" role="alert">{error}</p>;
  if (!report) return <p className="muted">Loading report…</p>;
  return <ReportView report={report} />;
}

export default function App() {
  const route = useRoute();
  const [health, setHealth] = useState<Health | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);

  useEffect(() => {
    api.health().then(setHealth, (e: Error) => setHealthError(e.message));
  }, []);

  const tab = route.page === "report" ? "reports" : route.page;
  const nav = [
    { id: "estimate", href: "#/", label: "New estimate" },
    { id: "reports", href: "#/reports", label: "Saved reports" },
    { id: "prices", href: "#/prices", label: "UK price list" },
  ];

  return (
    <>
      <a className="skip" href="#main">
        Skip to content
      </a>
      <header className="masthead no-print">
        <a className="brand" href="#/">
          <span className="brand-name">Car Damage AI</span>
          <span className="brand-sub">Repair-cost estimates from a photo, priced for the UK</span>
        </a>
        <nav aria-label="Main">
          {nav.map((n) => (
            <a key={n.id} href={n.href} aria-current={tab === n.id ? "page" : undefined}>
              {n.label}
            </a>
          ))}
        </nav>
      </header>

      <main id="main">
        {healthError && (
          <p className="alert" role="alert">
            {healthError}
          </p>
        )}
        <div hidden={route.page !== "estimate"}>
          <Estimate health={health} />
        </div>
        {route.page === "reports" && (
          <>
            <h1 className="page-title">Saved reports</h1>
            <ReportsList />
          </>
        )}
        {route.page === "report" && (
          <>
            <a className="back no-print" href="#/reports">
              All saved reports
            </a>
            <SavedReport id={route.id} />
          </>
        )}
        {route.page === "prices" && (
          <>
            <h1 className="page-title">UK repair-cost database</h1>
            <PriceList />
          </>
        )}
      </main>

      <footer className="footer no-print">
        {health ? (
          <span>
            {health.model.loaded ? `Model ${health.model.model_file.split(/[\\/]/).pop()} loaded` : "Model not loaded"}.{" "}
            {health.database.repair_methods} repair prices from {health.database.sources} UK sources, in SQLite.
          </span>
        ) : (
          <span>Connecting to the API…</span>
        )}
      </footer>
    </>
  );
}
