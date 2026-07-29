import { useEffect, useRef, useState } from "react";
import Icon from "./Icon";
import PremiumSelect from "./PremiumSelect";

export default function SettingsModal({
  open,
  settings,
  onSave,
  onClose,
  onClearHistory,
  onAvatarUpload,
  avatarUploading,
}) {
  const [draft, setDraft] = useState(settings);
  const [avatarError, setAvatarError] = useState("");
  const fileRef = useRef(null);

  useEffect(() => { setDraft(settings); setAvatarError(""); }, [settings, open]);
  useEffect(() => {
    if (!open) return undefined;
    const handler = (event) => event.key === "Escape" && onClose();
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!open) return null;

  async function handleAvatar(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setAvatarError("");
    try {
      const avatarUrl = await onAvatarUpload(file);
      setDraft((current) => ({
        ...current,
        profile: { ...current.profile, avatarUrl },
      }));
    } catch (err) {
      setAvatarError(err.message || "The selected profile image could not be uploaded.");
    } finally {
      event.target.value = "";
    }
  }

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="settings-modal" role="dialog" aria-modal="true" aria-labelledby="settings-title">
        <header>
          <div><span className="eyebrow">Workspace preferences</span><h2 id="settings-title">Settings</h2></div>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Close settings"><Icon name="close" /></button>
        </header>

        <div className="settings-content">
          <div className="settings-group">
            <div className="settings-group-heading"><Icon name="user" size={18} /><div><strong>Profile</strong><span>Personalize the workspace identity shown in the navigation.</span></div></div>
            <div className="profile-image-setting">
              {draft.profile.avatarUrl ? (
                <img src={draft.profile.avatarUrl} alt="Profile preview" />
              ) : (
                <div>{(draft.profile.name || "You").slice(0, 2).toUpperCase()}</div>
              )}
              <span>
                <strong>Profile image</strong>
                <small>Use a clear PNG, JPG, or WebP image up to 5 MB.</small>
              </span>
              <input ref={fileRef} type="file" accept="image/png,image/jpeg,image/webp" onChange={handleAvatar} hidden />
              <button type="button" className="secondary-action" onClick={() => fileRef.current?.click()} disabled={avatarUploading}>
                {avatarUploading ? <><span className="spinner" /> Uploading…</> : <><Icon name="upload" size={15} /> Update image</>}
              </button>
            </div>
            {avatarError && <p className="settings-inline-error">{avatarError}</p>}
            <div className="settings-grid two">
              <label><span>Display name</span><input value={draft.profile.name} placeholder="Enter your display name" onChange={(event) => setDraft({ ...draft, profile: { ...draft.profile, name: event.target.value } })} /></label>
              <label><span>Professional role</span><input value={draft.profile.role} placeholder="Enter your professional role" onChange={(event) => setDraft({ ...draft, profile: { ...draft.profile, role: event.target.value } })} /></label>
            </div>
          </div>

          <div className="settings-group">
            <div className="settings-group-heading"><Icon name="sun" size={18} /><div><strong>Appearance</strong><span>Choose the visual theme for your CodeFix AI workspace.</span></div></div>
            <button type="button" className="setting-toggle" onClick={() => setDraft({ ...draft, theme: draft.theme === "light" ? "dark" : "light" })}>
              <span><strong>Light theme</strong><small>Use a brighter workspace interface with the same layout and functionality.</small></span>
              <i className={draft.theme === "light" ? "on" : ""}><b /></i>
            </button>
          </div>

          <div className="settings-group">
            <div className="settings-group-heading"><Icon name="sparkles" size={18} /><div><strong>Review intelligence</strong><span>Control how deeply the analysis evaluates submitted code.</span></div></div>
            <div className="settings-grid two">
              <label>
                <span>Review focus</span>
                <PremiumSelect
                  value={draft.focus}
                  onChange={(focus) => setDraft({ ...draft, focus })}
                  ariaLabel="Select review focus"
                  options={[
                    { value: "balanced", label: "Balanced engineering review" },
                    { value: "correctness", label: "Correctness and reliability" },
                    { value: "security", label: "Security and defensive coding" },
                    { value: "performance", label: "Performance and efficiency" },
                  ]}
                />
              </label>
              <label>
                <span>Analysis depth</span>
                <PremiumSelect
                  value={draft.detail}
                  onChange={(detail) => setDraft({ ...draft, detail })}
                  ariaLabel="Select analysis depth"
                  options={[
                    { value: "standard", label: "Professional" },
                    { value: "deep", label: "Deep technical analysis" },
                    { value: "concise", label: "Concise review" },
                  ]}
                />
              </label>
            </div>
            <button type="button" className="setting-toggle" onClick={() => setDraft({ ...draft, autoExplain: !draft.autoExplain })}>
              <span><strong>Generate line-by-line explanation automatically</strong><small>Create a detailed walkthrough immediately after every completed review.</small></span>
              <i className={draft.autoExplain ? "on" : ""}><b /></i>
            </button>
          </div>

          <div className="settings-group danger-group">
            <div className="settings-group-heading"><Icon name="history" size={18} /><div><strong>Review history</strong><span>Remove all review sessions saved in your private workspace.</span></div></div>
            <button type="button" className="danger-action" onClick={onClearHistory}><Icon name="trash" size={16} /> Clear review history</button>
          </div>
        </div>

        <footer>
          <button type="button" className="secondary-action" onClick={onClose}>Cancel</button>
          <button type="button" className="primary-action" onClick={() => onSave(draft)}>Save preferences</button>
        </footer>
      </section>
    </div>
  );
}
