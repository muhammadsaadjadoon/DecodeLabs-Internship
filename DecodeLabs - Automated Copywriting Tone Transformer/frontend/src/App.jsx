import { useEffect, useMemo, useRef, useState } from "react";
import Header from "./components/Header.jsx";
import StepIndicator from "./components/StepIndicator.jsx";
import ConsolePanel from "./components/ConsolePanel.jsx";
import PressPanel from "./components/PressPanel.jsx";
import BulkPanel from "./components/BulkPanel.jsx";
import {
  fetchMeta,
  generateCopy,
  getCurrentUser,
  signUpAccount,
  signInAccount,
  logoutAccount,
  requestPasswordReset,
  resetAccountPassword,
  updateProfile,
  uploadProfilePhoto,
  removeProfilePhoto,
  changeAccountPassword,
  deleteAccount as deleteBackendAccount,
  fetchWorkspace,
  saveWorkspaceItem,
  deleteWorkspaceItem,
  clearWorkspaceSection,
} from "./api.js";
import logo from "./assets/lexora-logo.png";

const ROUTES = ["home", "studio", "bulk", "workspace", "profile"];

const FALLBACK_META = {
  platforms: [
    { value: "linkedin", label: "LinkedIn", max_chars: 3000, supports_hashtags: true, format: "professional post" },
    { value: "instagram", label: "Instagram", max_chars: 2200, supports_hashtags: true, format: "caption + hashtags" },
    { value: "facebook", label: "Facebook", max_chars: 3000, supports_hashtags: true, format: "conversational post" },
    { value: "email", label: "Email", max_chars: 1500, supports_hashtags: false, format: "subject + body" },
    { value: "twitter", label: "X / Twitter", max_chars: 280, supports_hashtags: true, format: "short post" },
    { value: "google_ads", label: "Google Ads", max_chars: 450, supports_hashtags: false, format: "headline + description" },
    { value: "youtube", label: "YouTube", max_chars: 5000, supports_hashtags: true, format: "title + description + tags" },
    { value: "tiktok", label: "TikTok", max_chars: 2200, supports_hashtags: true, format: "hook + caption + hashtags" },
  ],
  tones: ["witty", "professional", "bold", "friendly", "luxury", "urgent", "energetic", "empathetic", "confident"],
  objectives: ["sales", "awareness", "engagement", "lead_generation", "education", "launch", "retention"],
  copy_lengths: ["short", "medium", "long"],
  emoji_levels: ["none", "low", "medium", "high"],
  formality_levels: ["casual", "balanced", "formal"],
  cta_types: ["shop_now", "learn_more", "sign_up", "book_demo", "download", "comment", "follow", "custom"],
  transform_modes: ["generate", "rewrite", "shorten", "expand", "improve", "simplify", "humanize", "grammar_fix", "make_professional", "change_tone", "headlines", "hashtags", "translate"],
  variation_presets: ["Safe", "Creative", "Bold"],
  bulk_max_rows: 200,
};

const DEFAULT_FORM = {
  product_name: "",
  product_description: "",
  target_audience: "General buyers",
  content_objective: "sales",
  language: "English",
  copy_length: "medium",
  keywords: "",
  brand_voice: "",
  brand_voice_profile: {
    brand_description: "",
    preferred_tone: "",
    vocabulary: "",
    words_to_avoid: "",
    audience_notes: "",
    cta_style: "",
    example_copy: "",
  },
  emoji_level: "low",
  number_of_variations: 3,
  formality_level: "balanced",
  cta_type: "learn_more",
  custom_cta: "",
  transform_mode: "generate",
  source_text: "",
  platform: "linkedin",
  tone: "professional",
  temperature: 0.7,
  top_p: 0.9,
};

function normalizeLabel(value) {
  return String(value).replaceAll("_", " ").replace(/\b\w/g, (m) => m.toUpperCase());
}

function getInitialRoute() {
  const hash = window.location.hash.replace("#", "");
  if (ROUTES.includes(hash)) return hash;
  return "home";
}

function smartInitials(name = "") {
  const clean = name.trim() || "Lexora User";
  return clean.split(/\s+/).slice(0, 2).map((part) => part[0]?.toUpperCase()).join("");
}

function HomePanel({ setMode }) {
  return (
    <section className="relative overflow-hidden rounded-[2.25rem] border border-white/10 bg-white/[0.035] px-5 py-8 shadow-premium backdrop-blur-xl sm:px-8 lg:px-10 lg:py-10">
      <div className="pointer-events-none absolute -left-32 top-10 h-72 w-72 rounded-full bg-lex-cyan/10 blur-3xl" />
      <div className="pointer-events-none absolute -right-24 bottom-4 h-80 w-80 rounded-full bg-lex-blue/14 blur-3xl" />
      <div className="relative grid items-center gap-8 lg:grid-cols-[0.95fr_1.05fr]">
        <div>
          <div className="mb-6 flex items-center gap-3">
            <div className="h-16 w-16 overflow-hidden rounded-3xl border border-lex-cyan/35 bg-white shadow-glow">
              <img src={logo} alt="Lexora logo" className="h-full w-full object-cover" />
            </div>
            <div>
              <p className="font-mono text-[11px] uppercase tracking-[0.28em] text-lex-cyan/80">Lexora</p>
              <p className="mt-1 text-sm text-white/45">Premium AI copywriting workspace</p>
            </div>
          </div>
          <h2 className="font-display text-4xl font-extrabold leading-[0.95] tracking-tight text-white sm:text-5xl lg:text-6xl">
            Convert raw ideas into controlled, polished copy.
          </h2>
          <p className="mt-5 max-w-2xl text-base leading-relaxed text-white/58 sm:text-lg">
            Create platform-ready copy with audience, goal, language, brand voice, CTA, length, and professional variation controls.
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <button onClick={() => setMode("studio")} className="rounded-2xl bg-lex-button px-5 py-3 font-display text-sm font-extrabold text-midnight shadow-glow transition hover:-translate-y-0.5 hover:brightness-110">
              Start Creating
            </button>
            <button onClick={() => setMode("workspace")} className="rounded-2xl border border-white/10 px-5 py-3 text-sm font-bold text-white/70 transition hover:border-lex-cyan/40 hover:text-lex-cyan">
              Open Workspace
            </button>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
          {[
            ["01", "Brand Voice", "Remember tone, vocabulary, CTAs."],
            ["02", "3 Variations", "Safe, Creative, and Bold outputs."],
            ["03", "Workspace", "History, favourites, templates."],
          ].map(([n, title, text]) => (
            <div key={n} className="rounded-3xl border border-white/10 bg-midnight/55 p-5 shadow-premium">
              <p className="font-mono text-[11px] text-lex-cyan">{n}</p>
              <h3 className="mt-3 font-display text-lg font-bold text-white">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-white/45">{text}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function ConfirmModal({ modal, onCancel, onConfirm }) {
  if (!modal) return null;
  return (
    <div className="fixed inset-0 z-[70] grid place-items-center bg-midnight/80 px-4 backdrop-blur-md" role="dialog" aria-modal="true">
      <div className="w-full max-w-md rounded-[2rem] border border-white/10 bg-lex-panel p-6 shadow-premium">
        <p className="font-mono text-[11px] uppercase tracking-[0.24em] text-lex-cyan/75">Confirm action</p>
        <h3 className="mt-2 font-display text-2xl font-extrabold text-white">{modal.title}</h3>
        <p className="mt-3 text-sm leading-relaxed text-white/55">{modal.message}</p>
        <div className="mt-6 grid gap-3 sm:grid-cols-2">
          <button onClick={onCancel} className="rounded-2xl border border-white/10 px-4 py-3 text-sm font-bold text-white/65 hover:bg-white/5">Cancel</button>
          <button onClick={onConfirm} className="rounded-2xl border border-red-400/25 bg-red-500/10 px-4 py-3 text-sm font-bold text-red-200 hover:bg-red-500/18">Confirm</button>
        </div>
      </div>
    </div>
  );
}

function AccountPanel({ user, setUser, showToast, clearPrivateData, refreshWorkspace }) {
  const [screen, setScreen] = useState(user ? "profile" : "signin");
  const [message, setMessage] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [resetToken, setResetToken] = useState("");
  const [saving, setSaving] = useState(false);
  const [profileDraft, setProfileDraft] = useState({
    name: user?.name || "",
    email: user?.email || "",
    avatar: user?.avatar || "",
  });
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    confirm: "",
    remember: true,
    terms: false,
    currentPassword: "",
    newPassword: "",
    confirmNew: "",
  });

  const clearPasswordFields = () => setForm((prev) => ({
    ...prev,
    password: "",
    confirm: "",
    currentPassword: "",
    newPassword: "",
    confirmNew: "",
  }));

  useEffect(() => {
    setScreen(user ? "profile" : "signin");
    if (user) setProfileDraft({ name: user.name || "", email: user.email || "", avatar: user.avatar || "" });
    clearPasswordFields();
  }, [user]);

  const update = (key) => (e) => {
    const value = e.target.type === "checkbox" ? e.target.checked : e.target.value;
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const applyUser = async (nextUser) => {
    setUser(nextUser);
    setProfileDraft({ name: nextUser?.name || "", email: nextUser?.email || "", avatar: nextUser?.avatar || "" });
    setScreen("profile");
    clearPasswordFields();
    await refreshWorkspace?.();
  };

  const signUp = async () => {
    setMessage("");
    setSaving(true);
    try {
      const nextUser = await signUpAccount({
        name: form.name,
        email: form.email,
        password: form.password,
        terms: form.terms,
      });
      await applyUser(nextUser);
      showToast("Account created");
    } catch (err) {
      setMessage(err.message);
    } finally {
      setSaving(false);
    }
  };

  const signIn = async () => {
    setMessage("");
    setSaving(true);
    try {
      const nextUser = await signInAccount({ email: form.email, password: form.password, remember: form.remember });
      await applyUser(nextUser);
      showToast("Signed in");
    } catch (err) {
      setMessage(err.message);
    } finally {
      setSaving(false);
    }
  };

  const forgot = async () => {
    setMessage("");
    setSaving(true);
    try {
      const data = await requestPasswordReset(form.email);
      setResetToken(data.reset_token || "");
      setMessage(data.reset_token ? `Reset token: ${data.reset_token}` : data.message);
      setScreen("reset");
    } catch (err) {
      setMessage(err.message);
    } finally {
      setSaving(false);
    }
  };

  const resetPassword = async () => {
    setMessage("");
    setSaving(true);
    try {
      await resetAccountPassword({ email: form.email, token: resetToken, new_password: form.newPassword });
      clearPasswordFields();
      setResetToken("");
      setMessage("Password reset completed. You can sign in now.");
      setScreen("signin");
    } catch (err) {
      setMessage(err.message);
    } finally {
      setSaving(false);
    }
  };

  const onPhoto = async (file) => {
    if (!file) return;
    setMessage("");
    setSaving(true);
    try {
      const nextUser = await uploadProfilePhoto(file);
      setUser(nextUser);
      setProfileDraft({ name: nextUser.name || "", email: nextUser.email || "", avatar: nextUser.avatar || "" });
      showToast("Profile image saved");
    } catch (err) {
      setMessage(err.message);
    } finally {
      setSaving(false);
    }
  };

  const saveProfile = async () => {
    if (!user) return;
    setMessage("");
    setSaving(true);
    try {
      const nextUser = await updateProfile({ name: profileDraft.name });
      setUser(nextUser);
      setProfileDraft({ name: nextUser.name || "", email: nextUser.email || "", avatar: nextUser.avatar || "" });
      showToast("Profile updated");
    } catch (err) {
      setMessage(err.message);
    } finally {
      setSaving(false);
    }
  };

  const removePhoto = async () => {
    if (!user) return;
    setMessage("");
    setSaving(true);
    try {
      const nextUser = await removeProfilePhoto();
      setUser(nextUser);
      setProfileDraft({ name: nextUser.name || "", email: nextUser.email || "", avatar: "" });
      showToast("Profile image removed");
    } catch (err) {
      setMessage(err.message);
    } finally {
      setSaving(false);
    }
  };

  const changePassword = async () => {
    if (!user) return;
    setMessage("");
    setSaving(true);
    try {
      await changeAccountPassword({ current_password: form.currentPassword, new_password: form.newPassword });
      clearPasswordFields();
      setUser(null);
      clearPrivateData?.();
      setScreen("signin");
      showToast("Password changed. Please sign in again.");
    } catch (err) {
      setMessage(err.message);
    } finally {
      setSaving(false);
    }
  };

  const logout = async () => {
    setSaving(true);
    try {
      await logoutAccount();
    } finally {
      clearPasswordFields();
      setUser(null);
      clearPrivateData?.();
      setScreen("signin");
      setSaving(false);
      showToast("Signed out");
    }
  };

  const deleteAccount = async () => {
    if (!user) return;
    setSaving(true);
    try {
      await deleteBackendAccount();
      clearPasswordFields();
      setUser(null);
      clearPrivateData?.();
      setScreen("signup");
      showToast("Account deleted");
    } catch (err) {
      setMessage(err.message);
    } finally {
      setSaving(false);
    }
  };

  const avatar = profileDraft.avatar || user?.avatar;

  if (screen === "profile" && user) {
    return (
      <section className="grid items-start gap-6 lg:grid-cols-[0.82fr_1.18fr]">
        <div className="lex-card relative overflow-hidden rounded-[2rem] border border-white/10 bg-lex-panel p-6 shadow-premium sm:p-8">
          <div className="absolute -right-16 -top-16 h-48 w-48 rounded-full bg-lex-cyan/10 blur-3xl" />
          <div className="relative text-center">
            <div className="mx-auto grid h-28 w-28 place-items-center overflow-hidden rounded-full border border-lex-cyan/40 bg-midnight text-3xl font-extrabold text-lex-cyan shadow-glow">
              {avatar ? <img src={avatar} alt="Profile avatar" className="h-full w-full object-cover" /> : smartInitials(user.name)}
            </div>
            <h2 className="mt-5 font-display text-3xl font-extrabold text-white">{user.name || "Lexora User"}</h2>
            <p className="mt-1 text-sm text-white/48">{user.email}</p>
            <div className="mt-5 grid grid-cols-2 gap-3 text-left">
              <div className="rounded-3xl border border-white/10 bg-midnight/60 p-4"><p className="font-mono text-[10px] uppercase tracking-wider text-white/35">Plan</p><p className="mt-1 text-sm font-bold text-white">{user.plan || "Lexora Starter"}</p></div>
              <div className="rounded-3xl border border-white/10 bg-midnight/60 p-4"><p className="font-mono text-[10px] uppercase tracking-wider text-white/35">Created</p><p className="mt-1 text-sm font-bold text-white">{new Date(user.created_at || Date.now()).toLocaleDateString()}</p></div>
            </div>
            <div className="mt-5 grid gap-3 text-left">
              <div className="rounded-3xl border border-lex-cyan/15 bg-lex-cyan/5 p-4">
                <p className="font-mono text-[10px] uppercase tracking-wider text-lex-cyan/75">Account Status</p>
                <p className="mt-1 text-sm font-bold text-white">Active Lexora workspace</p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-3xl border border-white/10 bg-midnight/55 p-4">
                  <p className="font-mono text-[10px] uppercase tracking-wider text-white/35">Session</p>
                  <p className="mt-1 text-sm font-bold text-white">Secured</p>
                </div>
                <div className="rounded-3xl border border-white/10 bg-midnight/55 p-4">
                  <p className="font-mono text-[10px] uppercase tracking-wider text-white/35">Workspace</p>
                  <p className="mt-1 text-sm font-bold text-white">Private</p>
                </div>
              </div>
              <button onClick={logout} disabled={saving} className="w-full rounded-2xl border border-white/10 px-4 py-3 text-sm font-bold text-white/65 hover:border-lex-cyan/35 hover:text-lex-cyan disabled:opacity-50">Logout</button>
            </div>
          </div>
        </div>

        <div className="grid gap-6">
          <div className="rounded-[2rem] border border-white/10 bg-midnight/70 p-6 shadow-premium sm:p-8">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div><p className="font-mono text-[11px] uppercase tracking-[0.24em] text-lex-cyan/75">Edit profile</p><h3 className="mt-2 font-display text-2xl font-extrabold text-white">Account details</h3></div>
              <button onClick={saveProfile} disabled={saving || profileDraft.name.trim() === user.name} className="rounded-2xl bg-lex-button px-5 py-3 font-display text-sm font-extrabold text-midnight shadow-glow disabled:opacity-40">Save Profile</button>
            </div>
            <div className="mt-5 grid gap-4 sm:grid-cols-2">
              <input value={profileDraft.name} onChange={(e) => setProfileDraft((p) => ({ ...p, name: e.target.value }))} placeholder="Full name" autoComplete="name" className="rounded-2xl border border-white/10 bg-canvas/80 px-4 py-3 text-sm outline-none focus:border-lex-cyan" />
              <input value={profileDraft.email} disabled placeholder="Email address" autoComplete="email" className="rounded-2xl border border-white/10 bg-canvas/45 px-4 py-3 text-sm text-white/42 outline-none" />
              <label className="cursor-pointer rounded-2xl border border-dashed border-lex-cyan/35 bg-lex-cyan/5 px-4 py-3 text-sm font-bold text-lex-cyan hover:bg-lex-cyan/10">Upload / replace photo<input type="file" accept="image/png,image/jpeg,image/webp" className="hidden" onChange={(e) => onPhoto(e.target.files?.[0])} /></label>
              <button onClick={removePhoto} disabled={saving || !avatar} className="rounded-2xl border border-white/10 px-4 py-3 text-sm font-bold text-white/60 hover:text-white disabled:opacity-40">Remove Photo</button>
            </div>
          </div>

          <div className="grid gap-6 xl:grid-cols-2">
            <div className="rounded-[2rem] border border-white/10 bg-midnight/70 p-6 shadow-premium">
              <p className="font-mono text-[11px] uppercase tracking-[0.24em] text-lex-cyan/75">Change password</p>
              <div className="mt-5 grid gap-3">
                <input type="password" name="lexora-current-password" autoComplete="current-password" value={form.currentPassword} onChange={update("currentPassword")} placeholder="Current password" className="rounded-2xl border border-white/10 bg-canvas/80 px-4 py-3 text-sm outline-none focus:border-lex-cyan" />
                <input type="password" name="lexora-new-password" autoComplete="new-password" value={form.newPassword} onChange={update("newPassword")} placeholder="New password" className="rounded-2xl border border-white/10 bg-canvas/80 px-4 py-3 text-sm outline-none focus:border-lex-cyan" />
                <input type="password" name="lexora-confirm-new-password" autoComplete="new-password" value={form.confirmNew} onChange={update("confirmNew")} placeholder="Confirm new password" className="rounded-2xl border border-white/10 bg-canvas/80 px-4 py-3 text-sm outline-none focus:border-lex-cyan" />
                <button onClick={changePassword} disabled={saving} className="rounded-2xl border border-lex-cyan/30 px-4 py-3 text-sm font-bold text-lex-cyan hover:bg-lex-cyan/10 disabled:opacity-40">Update Password</button>
              </div>
            </div>
            <div className="rounded-[2rem] border border-red-400/20 bg-red-500/5 p-6 shadow-premium">
              <p className="font-mono text-[11px] uppercase tracking-[0.24em] text-red-200/80">Danger zone</p>
              <h3 className="mt-2 font-display text-xl font-extrabold text-white">Delete account</h3>
              <p className="mt-2 text-sm leading-relaxed text-white/45">Permanently deletes your Lexora account along with your saved history, favourites, templates, profile details, and profile image. This action cannot be undone.</p>
              <button onClick={deleteAccount} disabled={saving} className="mt-5 rounded-2xl border border-red-300/30 px-4 py-3 text-sm font-bold text-red-200 hover:bg-red-500/12 disabled:opacity-40">Delete Account</button>
            </div>
          </div>
          {message && <p className="rounded-2xl border border-lex-cyan/20 bg-lex-cyan/10 px-4 py-3 text-sm text-lex-cyan/90">{message}</p>}
        </div>
      </section>
    );
  }

  return (
    <section className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
      <div className="lex-card relative overflow-hidden rounded-[2rem] border border-white/10 bg-lex-panel p-6 shadow-premium sm:p-8">
        <p className="font-mono text-[11px] uppercase tracking-[0.26em] text-lex-cyan/75">Lexora account</p>
        <h2 className="mt-2 font-display text-3xl font-extrabold text-white">Secure your copy workspace.</h2>
        <p className="mt-3 text-sm leading-relaxed text-white/55">Sign in to keep history, favourites, templates and profile preferences inside your secure Lexora workspace.</p>
        <div className="mt-6 grid gap-3 sm:grid-cols-3">
          {["Protected history", "Private favourites", "Saved templates"].map((item) => <div key={item} className="rounded-3xl border border-white/10 bg-midnight/55 p-4 text-sm font-bold text-white/75">{item}</div>)}
        </div>
      </div>
      <div className="rounded-[2rem] border border-white/10 bg-midnight/70 p-6 shadow-premium sm:p-8">
        <div className="mb-5 flex gap-2 rounded-full border border-white/10 bg-white/[0.04] p-1">
          {[["signin", "Sign In"], ["signup", "Sign Up"], ["forgot", "Forgot"]].map(([id, label]) => (
            <button key={id} onClick={() => { setScreen(id); setMessage(""); clearPasswordFields(); }} className={`flex-1 rounded-full px-3 py-2 text-sm font-bold ${screen === id ? "bg-lex-button text-midnight" : "text-white/55 hover:text-white"}`}>{label}</button>
          ))}
        </div>
        <div className="grid gap-4">
          {screen === "signup" && <input value={form.name} onChange={update("name")} placeholder="Full name" autoComplete="name" className="rounded-2xl border border-white/10 bg-canvas/80 px-4 py-3 text-sm outline-none focus:border-lex-cyan" />}
          <input value={form.email} onChange={update("email")} placeholder="Email address" autoComplete="email" className="rounded-2xl border border-white/10 bg-canvas/80 px-4 py-3 text-sm outline-none focus:border-lex-cyan" />
          {screen !== "forgot" && screen !== "reset" && (
            <div className="relative">
              <input type={showPassword ? "text" : "password"} name="lexora-login-password" autoComplete={screen === "signin" ? "current-password" : "new-password"} value={form.password} onChange={update("password")} placeholder="Password" className="w-full rounded-2xl border border-white/10 bg-canvas/80 px-4 py-3 pr-24 text-sm outline-none focus:border-lex-cyan" />
              <button type="button" onClick={() => setShowPassword((v) => !v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-bold text-lex-cyan/75">{showPassword ? "Hide" : "Show"}</button>
            </div>
          )}
          {screen === "signup" && <input type="password" name="lexora-signup-confirm" autoComplete="new-password" value={form.confirm} onChange={update("confirm")} placeholder="Confirm password" className="rounded-2xl border border-white/10 bg-canvas/80 px-4 py-3 text-sm outline-none focus:border-lex-cyan" />}
          {screen === "signup" && <label className="flex gap-3 text-sm text-white/52"><input type="checkbox" checked={form.terms} onChange={update("terms")} /> I agree to Lexora workspace terms.</label>}
          {screen === "signin" && <label className="flex gap-3 text-sm text-white/52"><input type="checkbox" checked={form.remember} onChange={update("remember")} /> Remember me</label>}
          {screen === "reset" && (
            <>
              <input value={resetToken} onChange={(e) => setResetToken(e.target.value)} placeholder="Reset token" className="rounded-2xl border border-white/10 bg-canvas/80 px-4 py-3 text-sm outline-none focus:border-lex-cyan" />
              <input type="password" name="lexora-reset-password" autoComplete="new-password" value={form.newPassword} onChange={update("newPassword")} placeholder="New password" className="rounded-2xl border border-white/10 bg-canvas/80 px-4 py-3 text-sm outline-none focus:border-lex-cyan" />
              <input type="password" name="lexora-reset-confirm" autoComplete="new-password" value={form.confirmNew} onChange={update("confirmNew")} placeholder="Confirm new password" className="rounded-2xl border border-white/10 bg-canvas/80 px-4 py-3 text-sm outline-none focus:border-lex-cyan" />
            </>
          )}
          <button disabled={saving} onClick={screen === "signin" ? signIn : screen === "signup" ? signUp : screen === "forgot" ? forgot : resetPassword} className="rounded-2xl bg-lex-button px-5 py-3 font-display text-sm font-extrabold text-midnight shadow-glow disabled:opacity-45">
            {saving ? "Please wait…" : screen === "signin" ? "Sign In" : screen === "signup" ? "Create Account" : screen === "forgot" ? "Prepare Reset" : "Reset Password"}
          </button>
          {screen === "signin" && <button onClick={() => { setScreen("forgot"); setMessage(""); clearPasswordFields(); }} className="text-left text-xs font-mono text-lex-cyan/75 hover:text-lex-cyan">Forgot password?</button>}
          {message && <p className="rounded-2xl border border-lex-cyan/20 bg-lex-cyan/10 px-4 py-3 text-sm text-lex-cyan/90">{message}</p>}
        </div>
      </div>
    </section>
  );
}

function WorkspacePanel({ history, favourites, templates, onLoad, onDeleteHistory, onDeleteFavourite, onFavouriteLoad, onSaveTemplate, onDeleteTemplate, onClearHistory }) {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState({ platform: "all", tone: "all" });

  const filtered = useMemo(() => history.filter((item) => {
    const haystack = `${item.form.product_name} ${item.form.product_description} ${item.form.platform} ${item.form.tone}`.toLowerCase();
    const matchesQuery = !query || haystack.includes(query.toLowerCase());
    const matchesPlatform = filter.platform === "all" || item.form.platform === filter.platform;
    const matchesTone = filter.tone === "all" || item.form.tone === filter.tone;
    return matchesQuery && matchesPlatform && matchesTone;
  }), [history, query, filter]);

  const platforms = [...new Set(history.map((item) => item.form.platform))];
  const tones = [...new Set(history.map((item) => item.form.tone))];

  return (
    <section className="grid gap-6 xl:grid-cols-[1.12fr_0.88fr]">
      <div className="flex h-[clamp(620px,74vh,840px)] flex-col rounded-[2rem] border border-white/10 bg-transparent p-5 shadow-premium sm:p-7">
        <div className="pb-5">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div><p className="font-mono text-[11px] uppercase tracking-[0.26em] text-lex-cyan/75">Recent generations</p><h2 className="mt-2 font-display text-2xl font-extrabold text-white">History & saved content</h2></div>
            <button onClick={onClearHistory} className="rounded-full border border-red-400/20 px-3 py-2 text-xs font-bold text-red-300 hover:bg-red-500/10">Delete history</button>
          </div>
          <div className="mt-5 grid gap-3 sm:grid-cols-3">
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search history" className="rounded-2xl border border-white/10 bg-midnight/70 px-4 py-3 text-sm outline-none focus:border-lex-cyan" />
            <select value={filter.platform} onChange={(e) => setFilter((f) => ({ ...f, platform: e.target.value }))} className="rounded-2xl border border-white/10 bg-midnight/70 px-4 py-3 text-sm outline-none focus:border-lex-cyan"><option value="all">All platforms</option>{platforms.map((p) => <option key={p} value={p}>{normalizeLabel(p)}</option>)}</select>
            <select value={filter.tone} onChange={(e) => setFilter((f) => ({ ...f, tone: e.target.value }))} className="rounded-2xl border border-white/10 bg-midnight/70 px-4 py-3 text-sm outline-none focus:border-lex-cyan"><option value="all">All tones</option>{tones.map((t) => <option key={t} value={t}>{normalizeLabel(t)}</option>)}</select>
          </div>
        </div>
        <div tabIndex={0} className="thin-scroll grid flex-1 gap-3 overflow-y-auto pr-1">
          {filtered.length === 0 && <div className="grid min-h-[260px] place-items-center rounded-3xl border border-dashed border-white/10 px-5 text-center text-sm text-white/40">No saved generations yet.</div>}
          {filtered.map((item) => (
            <div key={item.id} className="rounded-3xl border border-white/10 bg-midnight/55 p-4">
              <div className="flex flex-wrap justify-between gap-3">
                <div><p className="font-display text-lg font-bold text-white">{item.form.product_name || "Untitled generation"}</p><p className="mt-1 font-mono text-[11px] uppercase tracking-[0.18em] text-white/35">{item.form.platform} · {item.form.tone} · {new Date(item.created_at).toLocaleString()}</p></div>
                <div className="flex flex-wrap gap-2">
                  <button onClick={() => onLoad(item.form)} className="rounded-full border border-lex-cyan/30 px-3 py-1.5 text-xs font-bold text-lex-cyan hover:bg-lex-cyan/10">Duplicate</button>
                  <button onClick={() => onSaveTemplate(item.form)} className="rounded-full border border-white/10 px-3 py-1.5 text-xs font-bold text-white/60 hover:bg-white/5">Save template</button>
                  <button onClick={() => onDeleteHistory(item.id)} className="rounded-full border border-red-400/20 px-3 py-1.5 text-xs font-bold text-red-300 hover:bg-red-500/10">Delete</button>
                </div>
              </div>
              <p className="mt-3 line-clamp-2 text-sm text-white/50">{item.result?.variations?.[0]?.headline || "Saved generation"}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="grid gap-6">
        <div className="flex h-[clamp(300px,36vh,420px)] flex-col rounded-[2rem] border border-white/10 bg-lex-panel p-5 shadow-premium sm:p-7">
          <p className="font-mono text-[11px] uppercase tracking-[0.26em] text-lex-cyan/75">Favourite outputs</p>
          <div tabIndex={0} className="thin-scroll mt-4 grid flex-1 gap-3 overflow-y-auto pr-1">
            {favourites.length === 0 && <p className="grid place-items-center rounded-3xl border border-dashed border-white/10 px-4 py-8 text-center text-sm text-white/40">No favourites yet.</p>}
            {favourites.map((fav) => (
              <div key={fav.id} className="rounded-3xl border border-white/10 bg-midnight/55 p-4">
                <p className="font-display font-bold text-white">{fav.variation.headline}</p>
                <p className="mt-2 line-clamp-3 text-sm text-white/48">{fav.variation.body}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  <button onClick={() => navigator.clipboard.writeText(`${fav.variation.headline}\n\n${fav.variation.body}\n\n${fav.variation.call_to_action || ""}`)} className="rounded-full border border-white/10 px-3 py-1.5 text-xs font-bold text-white/60 hover:text-white">Copy</button>
                  <button onClick={() => onFavouriteLoad?.(fav.form)} className="rounded-full border border-lex-cyan/30 px-3 py-1.5 text-xs font-bold text-lex-cyan hover:bg-lex-cyan/10">Reuse</button>
                  <button onClick={() => onDeleteFavourite(fav.id)} className="rounded-full border border-red-400/20 px-3 py-1.5 text-xs font-bold text-red-300 hover:bg-red-500/10">Remove</button>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="flex h-[clamp(300px,36vh,420px)] flex-col rounded-[2rem] border border-white/10 bg-lex-panel p-5 shadow-premium sm:p-7">
          <p className="font-mono text-[11px] uppercase tracking-[0.26em] text-lex-cyan/75">Saved templates</p>
          <div tabIndex={0} className="thin-scroll mt-4 grid flex-1 gap-3 overflow-y-auto pr-1">
            {templates.length === 0 && <p className="grid place-items-center rounded-3xl border border-dashed border-white/10 px-4 py-8 text-center text-sm text-white/40">Templates you save will appear here.</p>}
            {templates.map((template) => (
              <div key={template.id} className="rounded-3xl border border-white/10 bg-midnight/55 p-4">
                <button onClick={() => onLoad(template.form)} className="block w-full text-left"><p className="font-display font-bold text-white">{template.form.product_name || "Untitled template"}</p><p className="mt-1 font-mono text-[11px] uppercase tracking-[0.18em] text-white/35">{template.form.platform} · {template.form.tone}</p></button>
                <div className="mt-3 flex flex-wrap gap-2"><button onClick={() => onLoad(template.form)} className="rounded-full border border-lex-cyan/30 px-3 py-1.5 text-xs font-bold text-lex-cyan hover:bg-lex-cyan/10">Use template</button><button onClick={() => onDeleteTemplate(template.id)} className="rounded-full border border-red-400/20 px-3 py-1.5 text-xs font-bold text-red-300 hover:bg-red-500/10">Delete</button></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

export default function App() {
  const [mode, setModeState] = useState(getInitialRoute);
  const [meta, setMeta] = useState(FALLBACK_META);
  const [metaError, setMetaError] = useState(false);
  const [form, setForm] = useState(DEFAULT_FORM);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [highlightOutput, setHighlightOutput] = useState(false);
  const [history, setHistory] = useState([]);
  const [favourites, setFavourites] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [user, setUser] = useState(null);
  const [toast, setToast] = useState("");
  const [modal, setModal] = useState(null);
  const outputRef = useRef(null);

  const showToast = (message) => {
    setToast(message);
    window.clearTimeout(showToast._id);
    showToast._id = window.setTimeout(() => setToast(""), 2200);
  };

  const clearPrivateData = () => {
    setHistory([]);
    setFavourites([]);
    setTemplates([]);
  };

  const refreshWorkspace = async () => {
    try {
      const data = await fetchWorkspace();
      setHistory(data.history || []);
      setFavourites(data.favourites || []);
      setTemplates(data.templates || []);
    } catch {
      clearPrivateData();
    }
  };

  const setMode = (next) => {
    setModeState(next);
    if (window.location.hash.replace("#", "") !== next) window.history.pushState(null, "", `#${next}`);
  };

  useEffect(() => {
    const onPop = () => setModeState(getInitialRoute());
    window.addEventListener("popstate", onPop);
    window.addEventListener("hashchange", onPop);
    return () => {
      window.removeEventListener("popstate", onPop);
      window.removeEventListener("hashchange", onPop);
    };
  }, []);

  useEffect(() => {
    fetchMeta().then((data) => setMeta({ ...FALLBACK_META, ...data })).catch(() => setMetaError(true));
    getCurrentUser()
      .then((current) => {
        setUser(current);
        if (current) return fetchWorkspace();
        return { history: [], favourites: [], templates: [] };
      })
      .then((data) => {
        setHistory(data.history || []);
        setFavourites(data.favourites || []);
        setTemplates(data.templates || []);
      })
      .catch(() => clearPrivateData());
  }, []);

  useEffect(() => {
    if (user) refreshWorkspace();
    else clearPrivateData();
  }, [user?.id]);

  const step = loading ? 1 : result || error ? 2 : 0;

  const handleGenerate = async (overrideForm = null) => {
    if (loading) return;
    const payload = overrideForm || form;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await generateCopy({
        ...payload,
        temperature: Number(payload.temperature),
        top_p: Number(payload.top_p),
        number_of_variations: Number(payload.number_of_variations || 3),
      });
      setResult(data);
      if (user) {
        const saved = await saveWorkspaceItem("history", { created_at: new Date().toISOString(), form: payload, result: data });
        setHistory((prev) => [saved, ...prev.filter((item) => item.id !== saved.id)].slice(0, 80));
        showToast("Generation saved to history");
      } else {
        showToast("Generated. Sign in to save history.");
      }
      window.requestAnimationFrame(() => {
        const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        outputRef.current?.scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "start" });
        setHighlightOutput(true);
        window.setTimeout(() => setHighlightOutput(false), 1400);
      });
    } catch (err) {
      setError(err.message);
      showToast("Generation failed");
    } finally {
      setLoading(false);
    }
  };

  const loadForm = (nextForm) => {
    setForm({ ...DEFAULT_FORM, ...nextForm });
    setMode("studio");
    showToast("Brief loaded into Studio");
  };

  const addFavourite = async (variation) => {
    if (!user) return showToast("Sign in to save favourites");
    try {
      const saved = await saveWorkspaceItem("favourites", { created_at: new Date().toISOString(), variation, form });
      setFavourites((prev) => [saved, ...prev.filter((item) => item.id !== saved.id)].slice(0, 80));
      showToast("Added to favourites");
    } catch (err) {
      showToast(err.message);
    }
  };

  const saveTemplate = async (templateForm = form) => {
    if (!user) return showToast("Sign in to save templates");
    try {
      const saved = await saveWorkspaceItem("templates", { created_at: new Date().toISOString(), form: templateForm });
      setTemplates((prev) => [saved, ...prev.filter((item) => item.id !== saved.id)].slice(0, 40));
      showToast("Template saved");
    } catch (err) {
      showToast(err.message);
    }
  };

  const confirmAction = (title, message, action) => setModal({ title, message, action });

  const runConfirmedAction = async () => {
    try {
      await modal?.action?.();
      setModal(null);
      showToast("Action completed");
    } catch (err) {
      setModal(null);
      showToast(err.message || "Action failed");
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-canvas text-white">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_18%_10%,rgba(32,217,242,.16),transparent_34%),radial-gradient(circle_at_82%_14%,rgba(8,123,255,.18),transparent_30%),linear-gradient(180deg,#081426_0%,#050A14_100%)]" />
      <div className="pointer-events-none fixed inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-lex-cyan/70 to-transparent" />
      <div className="relative">
        <Header mode={mode} setMode={setMode} user={user} />
        <main className="mx-auto max-w-7xl px-4 py-7 sm:px-6 lg:py-10">
          {metaError && (
            <p className="mb-6 rounded-2xl border border-lex-cyan/25 bg-lex-cyan/10 px-4 py-3 font-mono text-xs text-lex-cyan/85">Lexora service is unavailable right now. Reconnect the service to generate live copy.</p>
          )}

          {mode === "home" && <HomePanel setMode={setMode} />}

          {mode === "studio" && (
            <section>
              <div className="mb-6"><StepIndicator active={step} /></div>
              <div className="grid items-start gap-7">
                <ConsolePanel meta={meta} form={form} setForm={setForm} onGenerate={() => handleGenerate()} loading={loading} onSaveTemplate={() => saveTemplate()} />
                <div ref={outputRef} className={`${highlightOutput ? "rounded-[2.4rem] ring-2 ring-lex-cyan/70 ring-offset-4 ring-offset-canvas" : ""} transition-all duration-500`}>
                  <PressPanel loading={loading} error={error} result={result} onRegenerate={() => handleGenerate()} onFavourite={addFavourite} onClear={() => { setResult(null); setError(null); }} onSaveOutput={addFavourite} />
                </div>
              </div>
            </section>
          )}

          {mode === "bulk" && <BulkPanel meta={meta} />}
          {mode === "workspace" && (
            <WorkspacePanel
              history={history}
              favourites={favourites}
              templates={templates}
              onLoad={loadForm}
              onDeleteHistory={(id) => confirmAction("Delete this history item?", "This saved generation will be removed from your workspace.", async () => { await deleteWorkspaceItem("history", id); setHistory((prev) => prev.filter((item) => item.id !== id)); })}
              onDeleteFavourite={(id) => confirmAction("Remove favourite?", "This output will be removed from your favourites.", async () => { await deleteWorkspaceItem("favourites", id); setFavourites((prev) => prev.filter((item) => item.id !== id)); })}
              onFavouriteLoad={loadForm}
              onSaveTemplate={saveTemplate}
              onDeleteTemplate={(id) => confirmAction("Delete template?", "This template cannot be restored after deletion.", async () => { await deleteWorkspaceItem("templates", id); setTemplates((prev) => prev.filter((item) => item.id !== id)); })}
              onClearHistory={() => confirmAction("Delete all history?", "All history for this account will be deleted.", async () => { await clearWorkspaceSection("history"); setHistory([]); })}
            />
          )}
          {mode === "profile" && <AccountPanel user={user} setUser={setUser} showToast={showToast} clearPrivateData={clearPrivateData} refreshWorkspace={refreshWorkspace} />}
        </main>

        <footer className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
          <div className="rounded-3xl border border-white/8 bg-white/[0.03] px-5 py-4 font-mono text-[11px] text-white/30">Lexora keeps your private workspace secure, organized, and accessible while protecting your content, and personal data through a reliable and privacy-focused experience.</div>
        </footer>
      </div>
      {toast && <div className="fixed bottom-5 left-1/2 z-50 -translate-x-1/2 rounded-full border border-lex-cyan/30 bg-midnight/95 px-5 py-3 text-sm font-bold text-lex-cyan shadow-glow backdrop-blur-xl">{toast}</div>}
      <ConfirmModal modal={modal} onCancel={() => setModal(null)} onConfirm={runConfirmedAction} />
    </div>
  );
}

