import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Sidebar from "./components/Sidebar";
import ReviewComposer from "./components/ReviewComposer";
import ReviewWorkspace from "./components/ReviewWorkspace";
import SettingsModal from "./components/SettingsModal";
import Icon from "./components/Icon";
import {
  clearReviewHistory,
  explainCode,
  getWorkspace,
  reviewCode,
  saveWorkspaceSettings,
  uploadProfileAvatar,
} from "./utils/api";

const DEFAULT_SETTINGS = {
  profile: { name: "", role: "", avatarUrl: "" },
  focus: "balanced",
  detail: "standard",
  autoExplain: false,
  theme: "dark",
};

function normalizeSettings(value = {}) {
  return {
    ...DEFAULT_SETTINGS,
    ...value,
    profile: { ...DEFAULT_SETTINGS.profile, ...(value.profile || {}) },
  };
}

export default function App() {
  const [sessions, setSessions] = useState([]);
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  const [activeId, setActiveId] = useState(null);
  const [pendingInput, setPendingInput] = useState(null);
  const [loading, setLoading] = useState(false);
  const [workspaceLoading, setWorkspaceLoading] = useState(true);
  const [explaining, setExplaining] = useState(false);
  const [avatarUploading, setAvatarUploading] = useState(false);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [composerResetKey, setComposerResetKey] = useState(0);
  const scrollRef = useRef(null);

  const activeSession = useMemo(
    () => sessions.find((item) => item.id === activeId) || null,
    [sessions, activeId]
  );

  useEffect(() => {
    document.documentElement.dataset.theme = settings.theme || "dark";
    document.documentElement.style.colorScheme = settings.theme === "light" ? "light" : "dark";
  }, [settings.theme]);

  useEffect(() => {
    let alive = true;
    getWorkspace()
      .then((workspace) => {
        if (!alive) return;
        setSessions(workspace.sessions || []);
        setSettings(normalizeSettings(workspace.settings));
      })
      .catch((err) => alive && setError(err.message || "The workspace could not be loaded."))
      .finally(() => alive && setWorkspaceLoading(false));
    return () => { alive = false; };
  }, []);

  useEffect(() => {
    const handler = (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "n") {
        event.preventDefault();
        handleNewReview();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  });

  useEffect(() => {
    if (!loading && !activeSession) return;
    requestAnimationFrame(() => {
      const container = scrollRef.current;
      if (container) container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });
    });
  }, [loading, activeSession?.id, activeSession?.explanation]);

  const updateSession = useCallback((id, patch) => {
    setSessions((current) => current.map((item) => (
      item.id === id ? { ...item, ...patch, updatedAt: new Date().toISOString() } : item
    )));
  }, []);

  async function generateExplanation(session) {
    if (!session?.result?.refactored_code || explaining) return;
    setExplaining(true);
    setError("");
    try {
      const response = await explainCode({
        code: session.result.refactored_code,
        language: session.result.language,
        filename: session.result.filename,
        detail: settings.detail,
        sessionId: session.id,
      });
      updateSession(session.id, { explanation: response.explanation });
    } catch (err) {
      setError(err.message || "The code walkthrough could not be generated. Please try again.");
    } finally {
      setExplaining(false);
    }
  }

  async function handleSubmit(input) {
    setLoading(true);
    setError("");
    setPendingInput({
      filename: input.filename,
      language: input.language,
      sourceCode: input.sourceCode,
    });
    setActiveId(null);

    try {
      const response = await reviewCode({
        file: input.file,
        code: input.code,
        language: input.language,
        filename: input.filename,
        focus: settings.focus,
        detail: settings.detail,
      });
      const session = response.session;
      setSessions((current) => [session, ...current.filter((item) => item.id !== session.id)]);
      setActiveId(session.id);
      setPendingInput(null);
      setComposerResetKey((value) => value + 1);
      if (settings.autoExplain) window.setTimeout(() => generateExplanation(session), 100);
    } catch (err) {
      setError(err.message || "The review could not be completed. Please verify the file and try again.");
    } finally {
      setLoading(false);
    }
  }

  function handleNewReview() {
    setActiveId(null);
    setPendingInput(null);
    setError("");
    setSidebarOpen(false);
    setComposerResetKey((value) => value + 1);
    requestAnimationFrame(() => scrollRef.current?.scrollTo({ top: 0, behavior: "auto" }));
  }

  function handleOpen(id) {
    setActiveId(id);
    setPendingInput(null);
    setError("");
    setSidebarOpen(false);
  }

  async function handleClearHistory() {
    if (!window.confirm("Clear every saved code review from this workspace?")) return;
    try {
      await clearReviewHistory();
      setSessions([]);
      setActiveId(null);
      setSettingsOpen(false);
      setComposerResetKey((value) => value + 1);
    } catch (err) {
      setError(err.message || "Review history could not be cleared.");
    }
  }

  async function saveSettings(next) {
    const normalized = normalizeSettings(next);
    try {
      const saved = await saveWorkspaceSettings(normalized);
      setSettings(normalizeSettings(saved));
      setSettingsOpen(false);
    } catch (err) {
      setError(err.message || "Workspace preferences could not be saved.");
    }
  }

  async function handleAvatarUpload(file) {
    if (!file) return;
    setAvatarUploading(true);
    setError("");
    try {
      const uploaded = await uploadProfileAvatar(file);
      return uploaded.avatarUrl;
    } catch (err) {
      setError(err.message || "The profile image could not be updated.");
      throw err;
    } finally {
      setAvatarUploading(false);
    }
  }

  async function toggleTheme() {
    const previous = settings;
    const next = { ...settings, theme: settings.theme === "light" ? "dark" : "light" };
    setSettings(next);
    try {
      const saved = await saveWorkspaceSettings(next);
      setSettings(normalizeSettings(saved));
    } catch (err) {
      setSettings(previous);
      setError(err.message || "The appearance preference could not be saved.");
    }
  }

  const headerTitle = activeSession?.title || (loading ? pendingInput?.filename : "New code review");

  return (
    <div className="app-shell">
      <Sidebar
        sessions={sessions}
        activeId={activeId}
        search={search}
        onSearch={setSearch}
        onNew={handleNewReview}
        onOpen={handleOpen}
        onSettings={() => setSettingsOpen(true)}
        profile={settings.profile}
        theme={settings.theme}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <main className={`main-workspace ${!activeSession && !loading && !workspaceLoading ? "home-fixed" : ""}`}> 
        <header className="workspace-header">
          <div className="workspace-title">
            <button type="button" className="mobile-menu-btn" onClick={() => setSidebarOpen(true)} aria-label="Open navigation">
              <Icon name="menu" size={20} />
            </button>
            <div>
              <span>Code review workspace</span>
              <h2>{headerTitle || "New code review"}</h2>
            </div>
          </div>
          <div className="header-status">
            <span className="engine-status"><i /> Analysis engine ready</span>
            <button
              type="button"
              className="header-action theme-action"
              onClick={toggleTheme}
              aria-label={settings.theme === "light" ? "Switch to dark theme" : "Switch to light theme"}
              title={settings.theme === "light" ? "Dark theme" : "Light theme"}
            >
              <Icon name={settings.theme === "light" ? "moon" : "sun"} size={18} />
            </button>
          </div>
        </header>

        <div className="workspace-scroll" ref={scrollRef}>
          <ReviewWorkspace
            session={activeSession}
            loading={loading || workspaceLoading}
            pendingInput={pendingInput}
            onExplain={() => generateExplanation(activeSession)}
            explaining={explaining}
            theme={settings.theme}
            profile={settings.profile}
          />
          {error && (
            <div className="workspace-error" role="alert">
              <Icon name="alert" size={18} />
              <div><strong>Review interrupted</strong><span>{error}</span></div>
              <button type="button" onClick={() => setError("")}><Icon name="close" size={16} /></button>
            </div>
          )}
        </div>

        <div className="composer-dock">
          <ReviewComposer
            onSubmit={handleSubmit}
            loading={loading || workspaceLoading}
            resetKey={composerResetKey}
            compact={Boolean(activeSession || loading)}
          />
          <p className="composer-disclaimer">AI review can accelerate engineering judgment; validate critical changes before deployment.</p>
        </div>
      </main>

      <SettingsModal
        open={settingsOpen}
        settings={settings}
        onSave={saveSettings}
        onClose={() => setSettingsOpen(false)}
        onClearHistory={handleClearHistory}
        onAvatarUpload={handleAvatarUpload}
        avatarUploading={avatarUploading}
      />
    </div>
  );
}
