import { useState } from "react";
import logo from "../assets/lexora-logo.png";

export default function Header({ mode, setMode, user }) {
  const [open, setOpen] = useState(false);
  const tabs = [
    { id: "home", label: "Home" },
    { id: "studio", label: "Studio" },
    { id: "bulk", label: "Bulk" },
    { id: "workspace", label: "Workspace" },
    { id: "profile", label: "Profile" },
  ];

  const go = (id) => {
    setMode(id);
    setOpen(false);
  };

  return (
    <header className="sticky top-0 z-30 border-b border-white/10 bg-midnight/82 backdrop-blur-2xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
        <button onClick={() => go("home")} className="flex min-w-0 items-center gap-3 text-left" aria-label="Go to Lexora home">
          <div className="relative h-12 w-12 shrink-0 overflow-hidden rounded-2xl border border-lex-cyan/35 bg-white shadow-glow">
            <img src={logo} alt="Lexora logo" className="h-full w-full object-cover" />
          </div>
          <div className="min-w-0">
            <h1 className="font-display text-xl font-extrabold leading-none tracking-tight text-white sm:text-2xl">Lexora</h1>
            <p className="mt-1 truncate font-mono text-[10px] uppercase tracking-[0.24em] text-lex-cyan/75 sm:text-[11px]">AI Tone Studio</p>
          </div>
        </button>

        <button onClick={() => setOpen((v) => !v)} className="rounded-2xl border border-white/10 px-3 py-2 text-sm font-bold text-white/70 hover:border-lex-cyan/35 hover:text-lex-cyan md:hidden" aria-label="Toggle navigation">Menu</button>

        <nav className={`${open ? "absolute left-4 right-4 top-[82px] flex" : "hidden"} max-w-full flex-col gap-2 rounded-3xl border border-white/10 bg-midnight/95 p-2 shadow-premium md:static md:flex md:flex-row md:items-center md:gap-1 md:overflow-x-auto md:rounded-full md:bg-white/[0.04] md:p-1 thin-scroll`}>
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => go(tab.id)}
              className={`whitespace-nowrap rounded-full px-3 py-2 text-xs font-semibold transition-all duration-300 sm:px-4 sm:text-sm ${
                mode === tab.id ? "bg-lex-button text-midnight shadow-glow" : "text-white/62 hover:bg-white/[0.07] hover:text-white"
              }`}
            >
              {tab.label}
              {tab.id === "profile" && user?.avatar && <span className="ml-2 inline-block h-4 w-4 overflow-hidden rounded-full align-[-3px]"><img src={user.avatar} alt="" className="h-full w-full object-cover" /></span>}
            </button>
          ))}
        </nav>
      </div>
    </header>
  );
}
