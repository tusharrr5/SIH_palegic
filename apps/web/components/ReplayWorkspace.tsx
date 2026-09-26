"use client";
import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";
import {
  Radio,
  Play,
  Pause,
  RotateCcw,
  Ship,
  ExternalLink,
  Database,
  Clock3,
} from "lucide-react";
import { api, date, utc } from "@/lib/api";
import type { Track, TrackSummary, MapDetail } from "@/lib/types";
const OceanMap = dynamic(() => import("./OceanMap"), { ssr: false });
type Position = { lon: number; lat: number; quality: string };
export default function ReplayWorkspace() {
  const [library, setLibrary] = useState<TrackSummary[]>([]);
  const [selected, setSelected] = useState("");
  const [track, setTrack] = useState<Track | null>(null);
  const [time, setTime] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(60);
  const [position, setPosition] = useState<Position | null>(null);
  const [positionPending, setPositionPending] = useState(false);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("recorded");
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let live = true;
    api<TrackSummary[]>("/tracks")
      .then((list) => {
        if (live) {
          setLibrary(list);
          setSelected(
            list.find((t) => t.id === "recorded-dma-265410000")?.id ||
              list.find((t) => !t.synthetic)?.id ||
              list[0]?.id ||
              "",
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
  }, []);
  useEffect(() => {
    if (!selected) return;
    let live = true;
    setPlaying(false);
    setTrack(null);
    setTime(0);
    setPosition(null);
    setError("");
    api<Track>(`/tracks/${selected}`)
      .then((t) => {
        if (live) {
          setTrack(t);
          setTime(Date.parse(t.points[0].time));
        }
      })
      .catch((e) => {
        if (live) setError(e.message);
      });
    return () => {
      live = false;
    };
  }, [selected]);
  const start = track ? Date.parse(track.points[0].time) : 0;
  const end = track
    ? Date.parse(track.points[track.points.length - 1].time)
    : 0;
  useEffect(() => {
    if (!track) return;
    let live = true;
    setPosition(null);
    setPositionPending(true);
    api<{ position: Position | null }>(
      `/tracks/${track.id}/replay?at=${encodeURIComponent(new Date(time).toISOString())}`,
    )
      .then((r) => {
        if (live) {
          setPositionPending(false);
          setPosition(r.position);
          setError("");
        }
      })
      .catch((e) => {
        if (live) {
          setError(e.message);
          setPlaying(false);
          setPositionPending(false);
        }
      });
    return () => {
      live = false;
    };
  }, [track, time]);
  useEffect(() => {
    if (!playing) return;
    const timer = setInterval(
      () => setTime((t) => Math.min(end, t + speed * 1000)),
      500,
    );
    return () => clearInterval(timer);
  }, [playing, speed, end]);
  useEffect(() => {
    if (time >= end) setPlaying(false);
  }, [time, end]);
  const mapDetail: MapDetail | null = useMemo(
    () =>
      track
        ? { id: track.id, trigger: "ais" as const, observation: null, tracks: [track], exercise: false }
        : null,
    [track],
  );
  const filtered = library.filter(
    (t) =>
      filter === "all" || (filter === "recorded" ? !t.synthetic : t.synthetic),
  );
  const gaps = useMemo(
    () =>
      track?.points.flatMap((p, i) =>
        i &&
        Date.parse(p.time) - Date.parse(track.points[i - 1].time) > 45 * 60000
          ? [{ from: track.points[i - 1].time, to: p.time }]
          : [],
      ) || [],
    [track],
  );
  const lastReport = track?.points.findLast((p) => Date.parse(p.time) <= time);
  return (
    <main className="replay-workspace">
      <div className="workspace-heading">
        <div>
          <div className="breadcrumb">OPERATIONS / TRAJECTORY LIBRARY</div>
          <h1>Replay the recorded journey.</h1>
          <p>
            Explore timestamped AIS reports, with source provenance and visible
            gaps in reception.
          </p>
        </div>
        <span className="badge">
          <Database size={14} /> CACHED AIS
        </span>
      </div>
      {error && (
        <p role="alert" className="form-error replay-alert">
          {error}
        </p>
      )}
      <div className="replay-layout">
        <aside className="replay-library">
          <div className="section-title">
            <h2>
              <Radio size={16} /> Trajectories
            </h2>
            <span className="mono">{filtered.length}</span>
          </div>
          <label className="replay-filter">
            Dataset
            <select
              value={filter}
              onChange={(e) => {
                const f = e.target.value;
                setFilter(f);
                const first = library.find(
                  (t) =>
                    f === "all" ||
                    (f === "recorded" ? !t.synthetic : t.synthetic),
                );
                setSelected(first?.id || "");
                setTrack(null);
                setPlaying(false);
              }}
            >
              <option value="recorded">Recorded AIS</option>
              <option value="synthetic">Training AIS</option>
              <option value="all">All trajectories</option>
            </select>
          </label>
          {loading && <p className="body-copy">Loading trajectory library…</p>}
          {!loading && !filtered.length && (
            <p className="body-copy">
              No trajectories yet. An administrator can import AIS JSON in
              Administration.
            </p>
          )}
          {filtered.map((t) => (
            <button
              key={t.id}
              className={`replay-track ${selected === t.id ? "active" : ""}`}
              onClick={() => setSelected(t.id)}
            >
              <Ship size={17} />
              <div>
                <strong>{t.name}</strong>
                <p>
                  {date(t.start_at)} · {t.report_count} reports
                </p>
                <small>
                  {t.synthetic
                    ? "Fictional training data"
                    : t.provenance.kind === "recorded_archive"
                      ? "Published historical AIS"
                      : "Operator-declared recording"}
                </small>
              </div>
            </button>
          ))}
          <div className="replay-note">
            <Clock3 size={17} />
            <p>
              The bundled passages are from Gothenburg in 2017. They have no
              established connection to the 2010 Gulf spill archive.
            </p>
          </div>
        </aside>
        <section className="replay-chart" aria-label="AIS replay map">
          <OceanMap
            detail={mapDetail}
            time={time}
            positions={track ? { [track.id]: position } : {}}
            showTracks={true}
            showSlick={false}
            reconstruction={null}
            driftFrame={0}
            onSelectTrack={() => {}}
            selectedTrack={track?.id || null}
          />
          <div className="recorded-timeline">
            <div className="replay-clock">
              <div>
                <span className="eyebrow">
                  {track?.synthetic ? "TRAINING REPLAY" : "RECORDED AIS REPLAY"}
                </span>
                <strong>
                  {time
                    ? new Date(time).toISOString().slice(11, 19)
                    : "--:--:--"}{" "}
                  <small>UTC</small>
                </strong>
              </div>
              <span className={`position-quality ${position ? "" : "missing"}`}>
                {positionPending && track
                  ? "Loading position…"
                  : position
                    ? position.quality === "received"
                      ? "Recorded report"
                      : "Interpolated position"
                    : track
                      ? "No position in this interval"
                      : "Select a trajectory"}
              </span>
            </div>
            <div className="replay-controls">
              <button
                className="play-button"
                aria-label={
                  playing ? "Pause recorded replay" : "Play recorded replay"
                }
                disabled={!track}
                onClick={() => {
                  if (time >= end) setTime(start);
                  setPlaying(!playing);
                }}
              >
                {playing ? <Pause size={19} /> : <Play size={19} />}
              </button>
              <button
                className="icon-button"
                aria-label="Restart recorded replay"
                disabled={!track}
                onClick={() => {
                  setTime(start);
                  setPlaying(false);
                }}
              >
                <RotateCcw size={17} />
              </button>
              <input
                aria-label="Recorded replay time"
                type="range"
                min={start}
                max={end || 1}
                step={1000}
                value={time}
                disabled={!track}
                onChange={(e) => {
                  setTime(Number(e.target.value));
                  setPlaying(false);
                }}
              />
              <select
                aria-label="Replay speed"
                value={speed}
                onChange={(e) => setSpeed(Number(e.target.value))}
              >
                <option value={15}>30×</option>
                <option value={60}>120×</option>
                <option value={300}>600×</option>
              </select>
            </div>
            <div className="replay-times">
              <span>{start ? utc(new Date(start).toISOString()) : "—"}</span>
              <span>{start ? date(new Date(start).toISOString()) : ""}</span>
              <span>{end ? utc(new Date(end).toISOString()) : "—"}</span>
            </div>
          </div>
        </section>
        <aside className="replay-provenance">
          <span className="eyebrow">REPORT & PROVENANCE</span>
          <h2>{track?.name || "Select a trajectory"}</h2>
          {track && (
            <>
              <span className="badge">
                {track.synthetic
                  ? "SYNTHETIC"
                  : track.provenance.kind === "recorded_archive"
                    ? "PUBLISHED RECORDING"
                    : "OPERATOR-DECLARED"}
              </span>
              <p className="body-copy">{track.provenance.description}</p>
              <dl>
                <dt>MMSI</dt>
                <dd>{track.provenance.mmsi || "Not supplied"}</dd>
                <dt>Retained reports</dt>
                <dd>{track.points.length}</dd>
                <dt>Last received report</dt>
                <dd>{lastReport ? utc(lastReport.time) : "—"}</dd>
                <dt>Reported speed</dt>
                <dd>
                  {lastReport?.sog != null
                    ? `${lastReport.sog.toFixed(1)} kn`
                    : "Unavailable"}
                </dd>
                <dt>Reported course</dt>
                <dd>
                  {lastReport?.cog != null
                    ? `${lastReport.cog.toFixed(1)}°`
                    : "Unavailable"}
                </dd>
              </dl>
              <h3>Source</h3>
              <p className="body-copy">{track.provenance.provider}</p>
              {track.provenance.url && (
                <a
                  className="source-link"
                  href={track.provenance.url}
                  target="_blank"
                  rel="noreferrer"
                >
                  Open dataset reference <ExternalLink size={13} />
                </a>
              )}
              <p className="stat-note">
                {track.provenance.time_basis ||
                  "UTC timestamps supplied by the importing operator."}
              </p>
              <h3>Replay method</h3>
              <p className="body-copy">
                WGS84 geodesic interpolation between reports. Gaps longer than
                45 minutes are left empty. Reported speed and course are
                observations, not interpolated measurements.
              </p>
              {gaps.map((g) => (
                <button
                  className="gap-jump"
                  key={g.from}
                  onClick={() => {
                    setPlaying(false);
                    setTime(
                      Math.round((Date.parse(g.from) + Date.parse(g.to)) / 2),
                    );
                  }}
                >
                  Reception gap · {utc(g.from)}–{utc(g.to)}
                </button>
              ))}
              <details>
                <summary>Data preparation & rights</summary>
                <p>
                  {track.provenance.transformation ||
                    "Normalized operator import; last report wins duplicate timestamps."}
                </p>
                <p>{track.provenance.license}</p>
                {track.provenance.license_url && (
                  <a
                    className="source-link"
                    href={track.provenance.license_url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Provider terms <ExternalLink size={13} />
                  </a>
                )}
              </details>
            </>
          )}
        </aside>
      </div>
    </main>
  );
}
