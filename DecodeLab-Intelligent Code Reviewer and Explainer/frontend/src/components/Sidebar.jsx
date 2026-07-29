import Icon from "./Icon";

function formatTime(value) {
  try {
    const date = new Date(value);
    const today = new Date();
    const sameDay = date.toDateString() === today.toDateString();
    return sameDay
      ? date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      : date.toLocaleDateString([], { month: "short", day: "numeric" });
  } catch {
    return "";
  }
}

export default function Sidebar({
  sessions,
  activeId,
  search,
  onSearch,
  onNew,
  onOpen,
  onSettings,
  profile,
  theme,
  open,
  onClose,
}) {
  const filtered = sessions.filter((item) =>
    `${item.title} ${item.filename} ${item.language}`.toLowerCase().includes(search.toLowerCase())
  );
  const logo = theme === "light" ? "/codefix-logo-light.png" : "/codefix-logo.png";

  return (
    <>
      <button
        type="button"
        aria-label="Close navigation"
        className={`sidebar-scrim ${open ? "show" : ""}`}
        onClick={onClose}
      />
      <aside className={`app-sidebar ${open ? "show" : ""}`}>
        <div className="brand-lockup">
          <img src={logo} alt="CodeFix AI" />
          <div>
            <strong>CodeFix AI</strong>
            <span>Code Intelligence Studio</span>
          </div>
        </div>

        <button type="button" className="new-review-btn" onClick={onNew}>
          <Icon name="plus" size={19} />
          <span>New review</span>
          <kbd>⌘ N</kbd>
        </button>

        <label className="sidebar-search">
          <Icon name="search" size={17} />
          <input
            value={search}
            onChange={(event) => onSearch(event.target.value)}
            placeholder="Search review history"
            aria-label="Search review history"
          />
        </label>

        <div className="sidebar-section-heading">
          <span>Review history</span>
          <span>{filtered.length}</span>
        </div>

        <nav className="history-list" aria-label="Review history">
          {filtered.length ? (
            filtered.map((item) => (
              <button
                type="button"
                key={item.id}
                className={`history-item ${activeId === item.id ? "active" : ""}`}
                onClick={() => onOpen(item.id)}
              >
                <span className={`history-icon ${item.result?.has_issues ? "issues" : "clean"}`}>
                  <Icon name={item.result?.has_issues ? "bug" : "check"} size={16} />
                </span>
                <span className="history-copy">
                  <strong>{item.title || item.filename || "Untitled review"}</strong>
                  <small>{item.language || "Code"} · {formatTime(item.updatedAt || item.createdAt)}</small>
                </span>
              </button>
            ))
          ) : (
            <div className="history-empty">
              <Icon name="history" size={20} />
              <p>{search ? "No matching reviews" : "Your completed reviews will appear here."}</p>
            </div>
          )}
        </nav>

        <div className="sidebar-footer">
          <div className="profile-card">
            {profile.avatarUrl ? (
              <img className="profile-avatar profile-avatar-image" src={profile.avatarUrl} alt="Profile" />
            ) : (
              <div className="profile-avatar">{(profile.name || "You").slice(0, 2).toUpperCase()}</div>
            )}
            <div className="profile-copy">
              <strong>{profile.name?.trim() || "Your profile"}</strong>
              <span>{profile.role?.trim() || "Add your professional role"}</span>
            </div>
            <button type="button" className="icon-btn" onClick={onSettings} aria-label="Open settings">
              <Icon name="settings" size={18} />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
