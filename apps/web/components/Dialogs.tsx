"use client";
import { useEffect, useRef, useState } from "react";
import {
  X,
  ArrowRight,
  Radio,
  Satellite,
  ShieldCheck,
  LoaderCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import type { User, Catalog } from "@/lib/types";
export function Modal({
  title,
  children,
  onClose,
}: {
  title: string;
  children: React.ReactNode;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    dialog.current?.showModal();
  }, []);
  return (
    <dialog
      ref={dialog}
      className="modal"
      onCancel={onClose}
      aria-label={title}
    >
      <div className="modal-heading">
        <h2>{title}</h2>
        <button
          className="icon-button"
          aria-label="Close dialog"
          onClick={onClose}
        >
          <X size={20} />
        </button>
      </div>
      {children}
    </dialog>
  );
}
export function LoginDialog({
  onClose,
  onLogin,
}: {
  onClose: () => void;
  onLogin: (user: User) => void;
}) {
  const [email, setEmail] = useState("authority@pelagic.local"),
    [password, setPassword] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  return (
    <Modal title="Enter your workspace" onClose={onClose}>
      <div className="login-intro">
        <ShieldCheck size={28} />
        <p>
          Secure access for maritime investigators and system administrators.
        </p>
      </div>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          setBusy(true);
          setError("");
          try {
            onLogin(
              await api<User>("/auth/login", {
                method: "POST",
                body: JSON.stringify({ email, password }),
              }),
            );
          } catch (e) {
            setError((e as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        <label>
          Email address
          <input
            type="email"
            autoComplete="username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoFocus
          />
        </label>
        <label>
          Password
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <button className="primary full" disabled={busy}>
          {busy ? (
            <LoaderCircle className="spin" size={16} />
          ) : (
            <ShieldCheck size={16} />
          )}
          Sign in
          <ArrowRight size={16} />
        </button>
        <p className="form-help">
          Local demo accounts are generated during setup. Your role is assigned
          by the server.
        </p>
        <div className="demo-quick-login">
          <button
            type="button"
            className="demo-quick-btn"
            onClick={async () => {
              setEmail("admin@pelagic.local");
              setPassword("SoN-yVSJPvold4HoBTbt");
              setBusy(true);
              setError("");
              try {
                onLogin(
                  await api<User>("/auth/login", {
                    method: "POST",
                    body: JSON.stringify({
                      email: "admin@pelagic.local",
                      password: "SoN-yVSJPvold4HoBTbt",
                    }),
                  }),
                );
              } catch (e) {
                setError((e as Error).message);
              } finally {
                setBusy(false);
              }
            }}
          >
            <ShieldCheck size={14} /> Quick Demo Sign In (admin@pelagic.local)
          </button>
        </div>
      </form>
    </Modal>
  );
}
export function DetectionDialog({
  onClose,
  onCreated,
  initial,
}: {
  onClose: () => void;
  onCreated: (id: string) => void;
  initial: "ais" | "sar";
}) {
  const [path, setPath] = useState<"ais" | "sar">(initial),
    [catalog, setCatalog] = useState<Catalog | null>(null),
    [exercise, setExercise] = useState(true),
    [track, setTrack] = useState("demo-1"),
    [obs, setObs] = useState("dwh-2010-05-17"),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  useEffect(() => {
    api<Catalog>("/catalog")
      .then(setCatalog)
      .catch((e) => setError(e.message));
  }, []);
  const tracks = catalog?.tracks.filter((t) => t.synthetic === exercise) || [];
  return (
    <Modal title="Start an investigation" onClose={onClose}>
      <p className="modal-lead">Two entry points. One chain of evidence.</p>
      <div className="path-options">
        <button
          className={path === "ais" ? "path-option selected" : "path-option"}
          onClick={() => setPath("ais")}
        >
          <Radio size={24} />
          <strong>AIS first</strong>
          <span>Behavior → SAR search</span>
        </button>
        <button
          className={path === "sar" ? "path-option selected" : "path-option"}
          onClick={() => setPath("sar")}
        >
          <Satellite size={24} />
          <strong>SAR first</strong>
          <span>Surface slick → source search</span>
        </button>
      </div>
      <label className="check-label">
        <input
          type="checkbox"
          checked={exercise}
          onChange={(e) => {
            setExercise(e.target.checked);
            setTrack(
              e.target.checked
                ? "demo-1"
                : catalog?.tracks.find((t) => !t.synthetic)?.id || "",
            );
          }}
        />
        <span>
          Training exercise{" "}
          <small>Use fictional AIS to demonstrate the workflow.</small>
        </span>
      </label>
      {path === "ais" ? (
        <label>
          AIS trajectory
          <select value={track} onChange={(e) => setTrack(e.target.value)}>
            {tracks.length ? (
              tracks.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))
            ) : (
              <option value="">No recorded AIS imported</option>
            )}
          </select>
        </label>
      ) : (
        <label>
          Historical observation
          <select value={obs} onChange={(e) => setObs(e.target.value)}>
            {catalog?.observations.map((o) => (
              <option key={o.id} value={o.id}>
                {o.title}
              </option>
            ))}
          </select>
        </label>
      )}
      <div className="info-note">
        {path === "ais"
          ? "Searches cached slicks within 100 km and ±24 hours of detected AIS anomalies. A match is a lead, not chemical confirmation."
          : "Uses the archived slick geometry, searches available AIS, and records missing reconstruction inputs."}
      </div>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      <button
        className="primary full"
        disabled={busy || !catalog || (path === "ais" && !tracks.length)}
        onClick={async () => {
          setBusy(true);
          setError("");
          try {
            const r = await api<{ id: string }>("/detections", {
              method: "POST",
              body: JSON.stringify({
                path,
                exercise,
                track_id: track,
                observation_id: obs,
              }),
            });
            onCreated(r.id);
          } catch (e) {
            setError((e as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        {busy ? (
          <LoaderCircle className="spin" size={17} />
        ) : (
          <ArrowRight size={17} />
        )}
        Create investigation
      </button>
    </Modal>
  );
}
