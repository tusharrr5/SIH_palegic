"use client";
import dynamic from "next/dynamic";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Waves,
  Globe2,
  ShieldCheck,
  SlidersHorizontal,
  ArrowUpRight,
  ArrowRight,
  Radio,
  Satellite,
  Search,
  Plus,
  Play,
  Pause,
  RotateCcw,
  LogOut,
  ChevronDown,
  Database,
  Layers3,
  Clock3,
  LoaderCircle,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import type {
  CaseDetail,
  CaseSummary,
  User,
  Reconstruction,
} from "@/lib/types";
import { api, area, date, utc } from "@/lib/api";
import { LoginDialog, DetectionDialog } from "@/components/Dialogs";
import EvidencePanel from "@/components/EvidencePanel";
import AdminView from "@/components/AdminView";
import ReplayWorkspace from "@/components/ReplayWorkspace";
import ReportModal from "@/components/ReportModal";
const OceanMap = dynamic(() => import("@/components/OceanMap"), {
  ssr: false,
  loading: () => (
    <div className="map-loading">
      <Waves size={28} />
      <span>Loading cached chart…</span>
    </div>
  ),
});
type Replay = {
  positions: {
    id: string;
    position: { lon: number; lat: number; quality: string } | null;
  }[];
};
export default function Home() {
  const [user, setUser] = useState<User | null>(null),
    [view, setView] = useState<"public" | "authority" | "admin" | "replay">(
      "public",
    ),
    [cases, setCases] = useState<CaseSummary[]>([]),
    [selected, setSelected] = useState(""),
    [detail, setDetail] = useState<CaseDetail | null>(null),
    [query, setQuery] = useState(""),
    [filter, setFilter] = useState("all"),
    [tab, setTab] = useState("Evidence"),
    [login, setLogin] = useState(false),
    [detection, setDetection] = useState<"ais" | "sar" | null>(null),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(true),
    [refresh, setRefresh] = useState(0),
    [selectedTrack, setSelectedTrack] = useState<string | null>(null),
    [time, setTime] = useState(0),
    [playing, setPlaying] = useState(false),
    [showTracks, setShowTracks] = useState(true),
    [showSlick, setShowSlick] = useState(true),
    [showFootprint, setShowFootprint] = useState(true),
    [showOrigin, setShowOrigin] = useState(true),
    [showGaps, setShowGaps] = useState(true),
    [speedMultiplier, setSpeedMultiplier] = useState(1),
    [showReport, setShowReport] = useState(false),
    [positions, setPositions] = useState<
      Record<string, { lon: number; lat: number; quality: string } | null>
    >({}),
    [reconstruction, setReconstruction] = useState<Reconstruction | null>(null),
    [driftFrame, setDriftFrame] = useState(6);
  const authority =
    (view !== "public" && !!user && ["authority", "admin"].includes(user.role)) ||
    selected === "SIH-ENNORE-2017" ||
    selected.startsWith("INV-");
  useEffect(() => {
    setFilter("all");
    setPlaying(false);
  }, [view]);
  useEffect(() => {
    api<User | null>("/auth/me")
      .then((u) => {
        setUser(u);
        if (u && u.role !== "public") setView("authority");
      })
      .catch(() => {});
  }, []);
  useEffect(() => {
    let live = true;
    setLoading(true);
    setError("");
    api<CaseSummary[]>(authority ? "/cases" : "/public/cases")
      .then((list) => {
        if (live) {
          setCases(list);
          setSelected((old) =>
            list.some((c) => c.id === old) ? old : list[0]?.id || "",
          );
        }
      })
      .catch((e) => {
        if (live) setError(e.message);
      })
      .finally(() => {
        if (live) setLoading(false);
      });
    return () => {
      live = false;
    };
  }, [authority, refresh]);
  useEffect(() => {
    if (!selected) return;
    let live = true;
    setError("");
    setPlaying(false);
    setReconstruction(null);
    setSelectedTrack(null);
    setPositions({});
    setDetail(null);
    api<CaseDetail>((authority ? "/cases/" : "/public/cases/") + selected)
      .then((d) => {
        if (live) {
          setDetail(d);
          const ts =
            d.tracks?.flatMap((t) =>
              t.points.map((p) => new Date(p.time).getTime()),
            ) || [];
          setTime(ts.length ? Math.min(...ts) : 0);
        }
      })
      .catch((e) => {
        if (live) setError(e.message);
      });
    return () => {
      live = false;
    };
  }, [selected, authority, refresh]);
  const timeRange = useMemo(() => {
    const ts =
      detail?.tracks?.flatMap((t) =>
        t.points.map((p) => new Date(p.time).getTime()),
      ) || [];
    return ts.length ? [Math.min(...ts), Math.max(...ts)] : [0, 0];
  }, [detail]);
  useEffect(() => {
    if (!authority || !detail?.tracks?.length || !time) return;
    let live = true;
    api<Replay>(
      `/cases/${detail.id}/replay?at=${encodeURIComponent(new Date(time).toISOString())}`,
    )
      .then((r) => {
        if (live)
          setPositions(
            Object.fromEntries(r.positions.map((p) => [p.id, p.position])),
          );
      })
      .catch(() => {
        if (live) setPositions({});
      });
    return () => {
      live = false;
    };
  }, [time, detail?.id, authority]);
  useEffect(() => {
    if (!playing) return;
    const delay = Math.max(100, Math.round(700 / speedMultiplier));
    const interval = setInterval(
      () =>
        setTime((t) => {
          if (t + 15 * 60000 >= timeRange[1]) {
            setPlaying(false);
            return timeRange[1];
          }
          return t + 15 * 60000;
        }),
      delay,
    );
    return () => clearInterval(interval);
  }, [playing, timeRange, speedMultiplier]);
  useEffect(() => {
    if (typeof window !== "undefined") {
      const search = window.location.search;
      if (search.includes("demo=true")) {
        handleRunDemo();
      }
    }
  }, []);
  const activeTimelineEvent = useMemo(() => {
    if (!detail?.timeline?.length || !time) return null;
    const past = detail.timeline.filter(
      (e) => new Date(e.timestamp).getTime() <= time,
    );
    return past[past.length - 1] || null;
  }, [detail?.timeline, time]);
  const filtered = cases.filter(
    (c) =>
      (filter === "all" ||
        (filter === "training" ? c.exercise : c.trigger === filter)) &&
      (c.title + " " + c.id).toLowerCase().includes(query.toLowerCase()),
  );
  const history = cases.filter((c) => c.published && !c.exercise);
  const pickTrack = useCallback((id: string) => {
    setSelectedTrack(id);
    setTab("Sources");
  }, []);
  const enterAuthority = async () => {
    if (user && user.role !== "public") {
      setView("authority");
      try {
        const authCases = await api<CaseSummary[]>("/cases");
        setCases(authCases);
      } catch {}
    } else {
      setLogin(true);
    }
  };
  const pickCase = (id: string) => {
    setSelected(id);
    setTab("Evidence");
  };
  const ensureAuthority = async (): Promise<boolean> => {
    if (user && user.role !== "public") return true;
    try {
      const u = await api<User>("/auth/demo", {
        method: "POST",
      });
      setUser(u);
      return true;
    } catch {
      setLogin(true);
      return false;
    }
  };
  const handleRunDemo = async () => {
    const ok = await ensureAuthority();
    if (!ok) return;

    setView("authority");
    try {
      const authCases = await api<CaseSummary[]>("/cases");
      setCases(authCases);
    } catch {}
    setSelected("SIH-ENNORE-2017");
    setTab("Evidence");
  };
  const handleTriggerPath = async (path: "sar" | "ais") => {
    const ok = await ensureAuthority();
    if (!ok) return;
    setView("authority");
    try {
      const authCases = await api<CaseSummary[]>("/cases");
      setCases(authCases);
      if (path === "ais") {
        const aisCase = authCases.find((c) => c.trigger === "ais");
        setSelected(aisCase ? aisCase.id : "INV-6011ADAF");
      } else {
        const sarCase = authCases.find((c) => c.id === "SIH-ENNORE-2017") || authCases[0];
        setSelected(sarCase ? sarCase.id : "SIH-ENNORE-2017");
      }
    } catch {
      if (path === "ais") {
        setSelected("INV-6011ADAF");
      } else {
        setSelected("SIH-ENNORE-2017");
      }
    }
    setTab("Evidence");
  };
  return (
    <div className="app-shell">
      <header className="topbar">
        <a href="/" className="brand" aria-label="PALEGIC home">
          <span className="brand-mark">
            <Waves size={26} strokeWidth={2.2} />
          </span>
          <span>
            <strong>
              PALEGIC<span className="brand-period">.</span>
            </strong>
            <small>MARITIME INTELLIGENCE</small>
          </span>
        </a>
        <nav aria-label="Main navigation">
          <button
            className={view === "public" ? "nav-item active" : "nav-item"}
            onClick={() => setView("public")}
          >
            <Globe2 size={16} />
            Ocean watch
          </button>
          <button
            className={view === "authority" ? "nav-item active" : "nav-item"}
            onClick={enterAuthority}
          >
            <ShieldCheck size={16} />
            Investigations
          </button>
          {user?.role === "admin" && (
            <button
              className={view === "admin" ? "nav-item active" : "nav-item"}
              onClick={() => setView("admin")}
            >
              <SlidersHorizontal size={16} />
              Administration
            </button>
          )}
          {user && user.role !== "public" && (
            <button
              className={view === "replay" ? "nav-item active" : "nav-item"}
              onClick={() => setView("replay")}
            >
              <Play size={16} /> AIS replay
            </button>
          )}
        </nav>
        <div className="header-right">
          <span className="cached-badge">
            <i />
            CACHED DEMO
          </span>
          {user ? (
            <>
              <span className="user-badge">
                <span className="avatar small-avatar">{user.name[0]}</span>
                <span>
                  {user.name}
                  <small>{user.role}</small>
                </span>
              </span>
              <button
                className="icon-button"
                title="Sign out"
                aria-label="Sign out"
                onClick={async () => {
                  try {
                    await api("/auth/logout", { method: "POST" });
                    setUser(null);
                    setView("public");
                  } catch (e) {
                    setError((e as Error).message);
                  }
                }}
              >
                <LogOut size={17} />
              </button>
            </>
          ) : (
            <button className="sign-in" onClick={() => setLogin(true)}>
              Authority sign in <ArrowUpRight size={15} />
            </button>
          )}
        </div>
      </header>
      {view === "admin" && user?.role === "admin" ? (
        <AdminView user={user} />
      ) : view === "replay" && authority ? (
        <ReplayWorkspace />
      ) : (
        <>
          <div className="sih-hero-card" role="region" aria-label="Demo entry point">
            <div className="sih-hero-inner">
              <div className="sih-hero-brand">
                <span className="sih-pill-badge">SIH 2026 · PROBLEM 26143</span>
                <span className="sih-product-name">PALEGIC</span>
              </div>
              <h1 className="sih-hero-title">
                Explainable Oil Spill Investigation &amp; Vessel Attribution
              </h1>
              <div className="sih-capabilities-strip">
                <span>Satellite Imagery</span>
                <span className="sih-bullet">•</span>
                <span>AIS</span>
                <span className="sih-bullet">•</span>
                <span>Drift Reconstruction</span>
                <span className="sih-bullet">•</span>
                <span>Evidence Fusion</span>
              </div>
              <div className="sih-action-group">
                <button
                  id="btn-run-demo"
                  className="sih-primary-btn"
                  onClick={handleRunDemo}
                >
                  <Play size={16} fill="currentColor" />
                  RUN SIH DEMO
                  <ArrowRight size={16} />
                </button>
                <div className="sih-secondary-btns">
                  <button
                    id="btn-sar-first"
                    className="sih-secondary-btn sih-entry-card-btn sar-theme"
                    onClick={() => handleTriggerPath("sar")}
                  >
                    <Satellite size={17} className="entry-card-icon" />
                    <span className="entry-card-text">
                      <strong>SAR FIRST</strong>
                      <small>Follow a detected surface signal</small>
                    </span>
                  </button>
                  <button
                    id="btn-ais-first"
                    className="sih-secondary-btn sih-entry-card-btn ais-theme"
                    onClick={() => handleTriggerPath("ais")}
                  >
                    <Radio size={17} className="entry-card-icon" />
                    <span className="entry-card-text">
                      <strong>AIS FIRST</strong>
                      <small>Follow suspicious vessel behaviour</small>
                    </span>
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div className="workspace-heading">
            <div>
              <div className="breadcrumb">
                {authority
                  ? "OPERATIONS / INVESTIGATIONS"
                  : "OBSERVATORY / HISTORICAL ARCHIVE"}
              </div>
              <p>
                {authority
                  ? "Connect vessel behavior, satellite observations, and the evidence that matters."
                  : "Explore historical surface slicks through open, traceable satellite evidence."}
              </p>
            </div>
            <div className="heading-actions">
              {authority ? (
                <button className="primary" onClick={() => setDetection("ais")}>
                  <Plus size={17} />
                  New investigation
                </button>
              ) : (
                <div className="archive-date">
                  <Clock3 size={17} />
                  <div>
                    <small>ARCHIVE WINDOW</small>
                    <strong>Jan 2017 · May 2010</strong>
                  </div>
                </div>
              )}
            </div>
          </div>
          <div className="overview-strip">
            <div>
              <span className="stat-icon">
                <Satellite size={18} />
              </span>
              <div>
                <strong>{history.length.toString().padStart(2, "0")}</strong>
                <span>Historical observations</span>
              </div>
            </div>
            <div>
              <span className="stat-icon amber">
                <Layers3 size={18} />
              </span>
              <div>
                <strong>
                  {history.reduce((n, c) => n + (c.polygon_count || 0), 0)}
                </strong>
                <span>Archived source polygons</span>
              </div>
            </div>
            <div>
              <span className="stat-icon">
                <Globe2 size={18} />
              </span>
              <div>
                <strong>Bay of Bengal</strong>
                <span>Ennore Oil Spill · 2017</span>
              </div>
            </div>
            <div>
              <span className="stat-icon">
                <Globe2 size={18} />
              </span>
              <div>
                <strong>Gulf of Mexico</strong>
                <span>Deepwater Horizon · 2010</span>
              </div>
            </div>
            <div>
              <span className="stat-icon green">
                <Database size={18} />
              </span>
              <div>
                <strong>Locally cached</strong>
                <span>NOAA / ESA / PALEGIC</span>
              </div>
              <CheckCircle2 size={15} className="green-text" />
            </div>
          </div>
          {error && (
            <div className="global-error" role="alert">
              <AlertCircle size={16} />
              {error}
              <button onClick={() => setRefresh((v) => v + 1)}>Retry</button>
            </div>
          )}
          <main className="workspace">
            <aside className="case-rail">
              <div className="rail-heading">
                <h2>{authority ? "Case files" : "Observations"}</h2>
                <span className="count-tag">{cases.length}</span>
                <SlidersHorizontal size={15} />
              </div>
              <label className="search-box">
                <Search size={16} />
                <input
                  aria-label="Search cases"
                  placeholder="Search observations…"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
                <kbd>⌕</kbd>
              </label>
              {authority ? (
                <div className="filter-tabs">
                  {[
                    ["all", "All"],
                    ["ais", "AIS"],
                    ["sar", "SAR"],
                    ["training", "Training"],
                  ].map(([v, label]) => (
                    <button
                      key={v}
                      className={filter === v ? "selected" : ""}
                      onClick={() => setFilter(v)}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              ) : (
                <div className="archive-filter">
                  <Satellite size={13} />
                  Satellite archive
                  <span>
                    2010
                    <ChevronDown size={12} />
                  </span>
                </div>
              )}
              <div className="case-list">
                {loading ? (
                  <div className="loading-state">
                    <LoaderCircle size={20} className="spin" />
                    Loading case files…
                  </div>
                ) : filtered.length ? (
                  filtered.map((c, i) => (
                    <button
                      key={c.id}
                      className={
                        "case-card " + (selected === c.id ? "selected" : "")
                      }
                      onClick={() => pickCase(c.id)}
                    >
                      <div className="case-card-top">
                        <span className={"trigger-tag " + c.trigger}>
                          {c.trigger === "sar" ? (
                            <Satellite size={12} />
                          ) : (
                            <Radio size={12} />
                          )}{" "}
                          {c.trigger === "sar" ? "SAR FIRST" : "AIS FIRST"}
                        </span>
                        <span className="case-index">
                          {String(i + 1).padStart(2, "0")}
                        </span>
                      </div>
                      <h3>{c.title}</h3>
                      <p>
                        {c.exercise
                          ? "Training exercise"
                          : c.id === "SIH-ENNORE-2017"
                          ? "Ennore Port · Bay of Bengal"
                          : "Northern Gulf of Mexico"}
                      </p>
                      <div className="case-card-bottom">
                        <span>{date(c.observed_at, true)}</span>
                        <strong>
                          {area(c.area_km2)} <small>km²</small>
                        </strong>
                      </div>
                      {selected === c.id && (
                        <div className="case-active">
                          <i />
                          {c.exercise
                            ? "Synthetic AIS · real slick geometry"
                            : c.id === "SIH-ENNORE-2017"
                            ? "Historical validation · Training AIS"
                            : "Historical surface anomaly"}
                          <ArrowRight size={12} />
                        </div>
                      )}
                    </button>
                  ))
                ) : (
                  <div className="empty-state">
                    <Search size={22} />
                    <p>No case files match your search.</p>
                  </div>
                )}
              </div>
              <div className="rail-footer">
                <span className="eyebrow">TWO SIGNALS. ONE INVESTIGATION.</span>
                <button
                  id="rail-ais-first"
                  onClick={() => handleTriggerPath("ais")}
                >
                  <span className="path-icon">
                    <Radio size={17} />
                  </span>
                  <span>
                    <strong>AIS first</strong>
                    <small>Follow suspicious vessel behaviour</small>
                  </span>
                  <ArrowUpRight size={15} />
                </button>
                <button
                  id="rail-sar-first"
                  onClick={() => handleTriggerPath("sar")}
                >
                  <span className="path-icon">
                    <Satellite size={17} />
                  </span>
                  <span>
                    <strong>SAR first</strong>
                    <small>Follow a detected surface signal</small>
                  </span>
                  <ArrowUpRight size={15} />
                </button>
              </div>
            </aside>
            <section
              className="map-column"
              aria-label="Geospatial investigation map"
            >
              <div className="map-toolbar">
                <div className="layer-pills">
                  <button
                    aria-pressed={showSlick}
                    className={showSlick ? "on amber-layer" : ""}
                    onClick={() => setShowSlick(!showSlick)}
                  >
                    <i />
                    Surface slick
                  </button>
                  {authority && (
                    <button
                      aria-pressed={showTracks}
                      className={showTracks ? "on blue-layer" : ""}
                      onClick={() => setShowTracks(!showTracks)}
                    >
                      <i />
                      AIS tracks
                    </button>
                  )}
                  {authority && (
                    <button
                      aria-pressed={showGaps}
                      className={showGaps ? "on red-layer" : ""}
                      onClick={() => setShowGaps(!showGaps)}
                    >
                      <i />
                      AIS gaps
                    </button>
                  )}
                  {detail?.findings?.sar_footprint && (
                    <button
                      aria-pressed={showFootprint}
                      className={showFootprint ? "on cyan-layer" : ""}
                      onClick={() => setShowFootprint(!showFootprint)}
                    >
                      <i />
                      SAR footprint
                    </button>
                  )}
                  {detail?.findings?.collision_site && (
                    <button
                      aria-pressed={showOrigin}
                      className={showOrigin ? "on purple-layer" : ""}
                      onClick={() => setShowOrigin(!showOrigin)}
                    >
                      <i />
                      Collision origin
                    </button>
                  )}
                </div>
                <span className="map-mode">
                  <span className="tiny-dot" />{" "}
                  {reconstruction
                    ? "ILLUSTRATIVE TRANSPORT"
                    : detail?.id === "SIH-ENNORE-2017"
                    ? "CANONICAL SIH INVESTIGATION"
                    : "OBSERVATION VIEW"}
                </span>
              </div>
              <OceanMap
                detail={detail}
                time={time}
                positions={positions}
                showTracks={authority && showTracks}
                showSlick={showSlick}
                showFootprint={showFootprint}
                showOrigin={showOrigin}
                showGaps={showGaps}
                reconstruction={reconstruction}
                driftFrame={driftFrame}
                onSelectTrack={pickTrack}
                selectedTrack={selectedTrack}
              />
              <div className="timeline">
                {authority && detail?.tracks?.length ? (
                  <>
                    <div className="timeline-title">
                      <span>
                        <Radio size={14} />
                        AIS replay{" "}
                        <em>
                          {detail.exercise
                            ? "SYNTHETIC TRAINING DATA"
                            : detail.id === "SIH-ENNORE-2017"
                            ? "TRAINING AIS RECONSTRUCTION"
                            : "OPERATOR-IMPORTED AIS"}
                        </em>
                      </span>
                      {activeTimelineEvent && (
                        <span className="replay-event-chip">
                          <span
                            className={`chip-tag ${activeTimelineEvent.provenance_class.toLowerCase()}`}
                          >
                            {activeTimelineEvent.provenance_class}
                          </span>
                          <strong>{activeTimelineEvent.title}</strong>
                        </span>
                      )}
                      <strong className="mono">
                        {time ? utc(new Date(time).toISOString()) : "—"}
                      </strong>
                    </div>
                    <div className="replay-controls">
                      <button
                        className="play-button"
                        aria-label={playing ? "Pause replay" : "Play replay"}
                        onClick={() => {
                          if (time >= timeRange[1]) setTime(timeRange[0]);
                          setPlaying(!playing);
                        }}
                      >
                        {playing ? (
                          <Pause size={17} />
                        ) : (
                          <Play size={17} fill="currentColor" />
                        )}
                      </button>
                      <button
                        className="icon-button"
                        title="Restart replay"
                        aria-label="Restart replay"
                        onClick={() => {
                          setPlaying(false);
                          setTime(timeRange[0]);
                        }}
                      >
                        <RotateCcw size={16} />
                      </button>
                      <div className="range-wrap">
                        <input
                          aria-label="AIS replay time"
                          type="range"
                          min={timeRange[0]}
                          max={timeRange[1]}
                          step={15 * 60000}
                          value={time}
                          onChange={(e) => {
                            setPlaying(false);
                            setTime(Number(e.target.value));
                          }}
                        />
                        <div className="range-labels">
                          <span>
                            {utc(new Date(timeRange[0]).toISOString())}
                          </span>
                          <span>Gaps &gt;45 min highlighted in red</span>
                          <span>
                            {utc(new Date(timeRange[1]).toISOString())}
                          </span>
                        </div>
                      </div>
                      <div
                        className="speed-toggles"
                        role="group"
                        aria-label="Replay speed"
                      >
                        {[0.5, 1, 2, 4].map((s) => (
                          <button
                            key={s}
                            className={
                              speedMultiplier === s
                                ? "speed-btn active"
                                : "speed-btn"
                            }
                            onClick={() => setSpeedMultiplier(s)}
                            title={`${s}x speed`}
                          >
                            {s}x
                          </button>
                        ))}
                      </div>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="timeline-title">
                      <span>
                        <Clock3 size={14} />
                        Historical observation timeline
                      </span>
                      <span className="mono">DAILY COMPOSITES</span>
                    </div>
                    <div className="history-timeline">
                      <span className="timeline-rule" />
                      {history
                        .sort((a, b) =>
                          (a.observed_at || "").localeCompare(
                            b.observed_at || "",
                          ),
                        )
                        .map((c) => (
                          <button
                            key={c.id}
                            className={selected === c.id ? "selected" : ""}
                            onClick={() => pickCase(c.id)}
                          >
                            <i />
                            <strong>{date(c.observed_at, true)}</strong>
                            <small>{area(c.area_km2)} km²</small>
                          </button>
                        ))}
                    </div>
                  </>
                )}
              </div>
            </section>
            {detail ? (
              <EvidencePanel
                key={detail.id}
                detail={detail}
                authority={authority}
                tab={tab}
                setTab={setTab}
                selectedTrack={selectedTrack}
                onSelectTrack={pickTrack}
                onLogin={() => setLogin(true)}
                onRefresh={() => setRefresh((v) => v + 1)}
                reconstruction={reconstruction}
                onReconstruction={setReconstruction}
                driftFrame={driftFrame}
                setDriftFrame={setDriftFrame}
                onOpenReport={() => setShowReport(true)}
              />
            ) : (
              <aside className="evidence-panel loading-state">
                <LoaderCircle size={24} className="spin" />
                {loading ? "Loading archive…" : "Select an observation"}
              </aside>
            )}
          </main>
          <footer className="app-footer">
            <span>
              <Waves size={13} />
              PALEGIC · SIH PROTOTYPE
            </span>
            <span>
              Observed geometry. Transparent uncertainty. Human review.
            </span>
            <span>
              WGS84 / EPSG:4326 <i />
              UTC
            </span>
          </footer>
        </>
      )}
      {login && (
        <LoginDialog
          onClose={() => setLogin(false)}
          onLogin={(u) => {
            setUser(u);
            setLogin(false);
            setView(u.role === "public" ? "public" : "authority");
          }}
        />
      )}
      {detection && (
        <DetectionDialog
          initial={detection}
          onClose={() => setDetection(null)}
          onCreated={(id) => {
            setDetection(null);
            setSelected(id);
            setTab("Evidence");
            setRefresh((v) => v + 1);
          }}
        />
      )}
      {showReport && detail && (
        <ReportModal detail={detail} onClose={() => setShowReport(false)} />
      )}
    </div>
  );
}
