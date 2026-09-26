"use client";
import { useEffect, useRef, useState } from "react";
import {
  Database,
  ShieldCheck,
  CheckCircle2,
  Upload,
  RefreshCw,
  ExternalLink,
  FileCheck2,
  Activity,
  UserPlus,
} from "lucide-react";
import type { AdminData, User } from "@/lib/types";
import { api, date, utc } from "@/lib/api";
export default function AdminView({ user }: { user: User }) {
  const [data, setData] = useState<AdminData | null>(null),
    [error, setError] = useState(""),
    [success, setSuccess] = useState(""),
    [adding, setAdding] = useState(false),
    [account, setAccount] = useState({ name: "", email: "", password: "" }),
    [busy, setBusy] = useState(false);
  const file = useRef<HTMLInputElement>(null);
  const load = () =>
    api<AdminData>("/admin/overview")
      .then(setData)
      .catch((e) => setError(e.message));
  useEffect(() => {
    load();
  }, []);
  return (
    <main className="admin-view">
      <div className="admin-heading">
        <div>
          <span className="eyebrow">SYSTEM ADMINISTRATION</span>
          <h1>Trust starts with the data.</h1>
          <p>
            Manage access, inspect cached evidence, and keep a traceable record.
          </p>
        </div>
        <button className="outline" onClick={load}>
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>
      {error && (
        <p role="alert" className="form-error">
          {error}
        </p>
      )}
      {success && (
        <p role="status" className="success-note">
          {success}
        </p>
      )}
      <div className="admin-stats">
        <div>
          <Database size={21} />
          <strong>{data?.counts.observations ?? "—"}</strong>
          <span>Historical composites</span>
        </div>
        <div>
          <Activity size={21} />
          <strong>{data?.counts.tracks ?? "—"}</strong>
          <span>Cached AIS trajectories</span>
        </div>
        <div>
          <FileCheck2 size={21} />
          <strong>{data?.counts.cases ?? "—"}</strong>
          <span>Investigation cases</span>
        </div>
        <div>
          <ShieldCheck size={21} />
          <strong>{data?.users.length ?? "—"}</strong>
          <span>Managed accounts</span>
        </div>
      </div>
      <div className="admin-grid">
        <section className="admin-card">
          <div className="section-title">
            <h2>Dataset integrity</h2>
            <span className="badge">SHA-256 VERIFIED</span>
          </div>
          <p className="body-copy">
            Checksums are recomputed from the cached source files. No external
            services are needed during a demonstration.
          </p>
          <div className="dataset-table">
            {data?.datasets.map((d) => (
              <div className="dataset-row" key={d.file}>
                <FileCheck2 size={20} />
                <div>
                  <strong>{d.file}</strong>
                  <p>
                    {d.feature_count ? `${d.feature_count} features · ` : ""}
                    {(d.bytes / 1024).toFixed(0)} KB · {date(d.retrieved_at)}
                  </p>
                  <code title={d.sha256}>{d.sha256.slice(0, 22)}…</code>
                </div>
                <span className={d.verified ? "verified" : "form-error"}>
                  {d.verified ? <CheckCircle2 size={17} /> : null}
                  {d.verified ? "Verified" : "Changed"}
                </span>
                <a
                  href={d.url}
                  aria-label={`Original source for ${d.file}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  <ExternalLink size={15} />
                </a>
              </div>
            ))}
          </div>
        </section>
        <section className="admin-card">
          <div className="section-title">
            <h2>Access control</h2>
            <ShieldCheck size={18} />
          </div>
          <p className="body-copy">
            Permissions are checked by the API on every request. Role changes
            revoke existing sessions.
          </p>
          <button
            className="outline full"
            onClick={() => setAdding(!adding)}
            aria-expanded={adding}
          >
            <UserPlus size={16} />
            {adding ? "Close account form" : "Add authority"}
          </button>
          {adding && (
            <form
              className="authority-form"
              onSubmit={async (e) => {
                e.preventDefault();
                setBusy(true);
                setError("");
                setSuccess("");
                try {
                  const created = await api<User>("/admin/authorities", {
                    method: "POST",
                    body: JSON.stringify(account),
                  });
                  setSuccess(
                    `Authority account created for ${created.email}. They can sign in with the password you supplied.`,
                  );
                  setAccount({ name: "", email: "", password: "" });
                  setAdding(false);
                  await load();
                } catch (e) {
                  setError((e as Error).message);
                } finally {
                  setBusy(false);
                }
              }}
            >
              <label>
                Full name
                <input
                  required
                  minLength={2}
                  maxLength={100}
                  autoComplete="name"
                  value={account.name}
                  onChange={(e) =>
                    setAccount({ ...account, name: e.target.value })
                  }
                />
              </label>
              <label>
                Email address
                <input
                  required
                  type="email"
                  maxLength={254}
                  autoComplete="off"
                  value={account.email}
                  onChange={(e) =>
                    setAccount({ ...account, email: e.target.value })
                  }
                />
              </label>
              <label>
                Initial password
                <input
                  required
                  type="password"
                  minLength={12}
                  maxLength={128}
                  autoComplete="new-password"
                  value={account.password}
                  onChange={(e) =>
                    setAccount({ ...account, password: e.target.value })
                  }
                />
              </label>
              <p className="stat-note">
                At least 12 characters. Share the login directly with your
                officer. This creates authority access immediately.
              </p>
              <button className="primary full" disabled={busy}>
                {busy ? "Creating…" : "Create authority account"}
              </button>
            </form>
          )}
          {data?.users.map((u) => (
            <div className="user-row" key={u.id}>
              <span className="avatar">{u.name.charAt(0)}</span>
              <div>
                <strong>
                  {u.name}
                  {u.id === user.id ? " (you)" : ""}
                </strong>
                <p>{u.email}</p>
              </div>
              <select
                aria-label={`Role for ${u.name}`}
                disabled={u.id === user.id || busy}
                value={u.role}
                onChange={async (e) => {
                  setBusy(true);
                  setError("");
                  try {
                    await api(`/admin/users/${u.id}/role`, {
                      method: "PATCH",
                      body: JSON.stringify({ role: e.target.value }),
                    });
                    setSuccess("Role updated. Existing sessions were revoked.");
                    await load();
                  } catch (e) {
                    setError((e as Error).message);
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                <option value="public">Public</option>
                <option value="authority">Authority</option>
                <option value="admin">Admin</option>
              </select>
            </div>
          ))}
          <div className="role-matrix">
            <span>Public</span>
            <p>Published historical records</p>
            <span>Authority</span>
            <p>Investigations, replay, review, export</p>
            <span>Admin</span>
            <p>Authority tools + users, AIS imports, audit</p>
          </div>
          <div className="section-title">
            <h2>Import an AIS trajectory</h2>
          </div>
          <p className="body-copy">
            Upload normalized JSON with a source, license, timestamped
            coordinates, and an explicit synthetic flag. Imported recorded data
            remains operator-declared.
          </p>
          <input
            ref={file}
            type="file"
            accept=".json,application/json"
            hidden
            onChange={async (e) => {
              const f = e.target.files?.[0];
              if (!f) return;
              setBusy(true);
              setError("");
              try {
                if (f.size > 2000000)
                  throw new Error("Use a JSON file smaller than 2 MB.");
                const body = JSON.parse(await f.text());
                const result = await api<{ points: number }>("/admin/ais", {
                  method: "POST",
                  body: JSON.stringify(body),
                });
                setSuccess(`Imported ${result.points} normalized AIS reports.`);
                await load();
              } catch (e) {
                setError((e as Error).message);
              } finally {
                setBusy(false);
                if (file.current) file.current.value = "";
              }
            }}
          />
          <button
            className="outline full"
            disabled={busy}
            onClick={() => file.current?.click()}
          >
            <Upload size={16} />
            Select AIS JSON
          </button>
          <p className="stat-note">Schema and example: docs/ais-import.md</p>
        </section>
        <section className="admin-card audit-card">
          <div className="section-title">
            <h2>Audit trail</h2>
            <span className="mono">LATEST 50 EVENTS</span>
          </div>
          <div className="audit-table">
            <div className="audit-header">
              <span>Time (UTC)</span>
              <span>Actor</span>
              <span>Action</span>
              <span>Entity</span>
            </div>
            {data?.audit.map((a) => (
              <div className="audit-row" key={a.id}>
                <span>
                  {date(a.created_at, true)} · {utc(a.created_at)}
                </span>
                <span>{a.actor || "System"}</span>
                <strong>{a.action.replaceAll("_", " ")}</strong>
                <code>{a.entity_id || "—"}</code>
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
