const MODE_LABELS = {
  generate: "Generate",
  rewrite: "Rewrite",
  shorten: "Shorten",
  expand: "Expand",
  improve: "Improve",
  simplify: "Simplify",
  humanize: "Humanize",
  grammar_fix: "Grammar Fix",
  make_professional: "Professional",
  change_tone: "Change Tone",
  headlines: "Headlines",
  hashtags: "Hashtags",
  translate: "Translate",
};

function labelize(value) {
  return String(value).replaceAll("_", " ").replace(/\b\w/g, (m) => m.toUpperCase());
}

function Field({ label, children, hint }) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between gap-3">
        <label className="font-mono text-[11px] uppercase tracking-wider text-white/45">{label}</label>
        {hint && <span className="text-right text-[11px] text-white/30">{hint}</span>}
      </div>
      {children}
    </div>
  );
}

function Input({ className = "", ...props }) {
  return (
    <input
      {...props}
      className={`w-full rounded-2xl border border-white/10 bg-midnight/70 px-4 py-3 text-sm text-white outline-none transition placeholder:text-white/24 focus:border-lex-cyan/70 focus:shadow-glow ${className}`}
    />
  );
}

function TextArea({ className = "", ...props }) {
  return (
    <textarea
      {...props}
      className={`w-full resize-none rounded-2xl border border-white/10 bg-midnight/70 px-4 py-3 text-sm leading-relaxed text-white outline-none transition placeholder:text-white/24 focus:border-lex-cyan/70 focus:shadow-glow ${className}`}
    />
  );
}

function Select({ children, ...props }) {
  return (
    <select
      {...props}
      className="w-full rounded-2xl border border-white/10 bg-midnight/70 px-4 py-3 text-sm text-white outline-none transition focus:border-lex-cyan/70 focus:shadow-glow"
    >
      {children}
    </select>
  );
}

function OptionPills({ items, value, onChange, accent = "cyan", render }) {
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => {
        const active = value === item;
        const activeClass = accent === "teal" ? "border-lex-teal/70 bg-lex-teal/10 text-lex-teal shadow-glow" : "border-lex-cyan/70 bg-lex-cyan/10 text-white shadow-glow";
        return (
          <button
            key={item}
            type="button"
            onClick={() => onChange(item)}
            className={`rounded-full border px-3.5 py-2 text-xs font-semibold capitalize transition-all duration-300 ${
              active ? activeClass : "border-white/10 bg-white/[0.03] text-white/50 hover:border-white/24 hover:text-white"
            }`}
          >
            {render ? render(item) : labelize(item)}
          </button>
        );
      })}
    </div>
  );
}

export default function ConsolePanel({ meta, form, setForm, onGenerate, loading, onSaveTemplate }) {
  const update = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));
  const setValue = (key, value) => setForm((f) => ({ ...f, [key]: value }));
  const updateBrand = (key) => (e) =>
    setForm((f) => ({
      ...f,
      brand_voice_profile: { ...(f.brand_voice_profile || {}), [key]: e.target.value },
    }));

  const needsSourceText = form.transform_mode !== "generate";
  const productLabel = needsSourceText ? "Project / Offer Name" : "Product Name";
  const descriptionLabel = needsSourceText ? "Transformation Context" : "Product Description";

  return (
    <div className="lex-card relative overflow-hidden rounded-[2rem] border border-white/10 bg-lex-panel p-5 shadow-premium sm:p-7">
      <div className="pointer-events-none absolute -right-24 -top-24 h-64 w-64 rounded-full bg-lex-cyan/10 blur-3xl" />
      <div className="relative flex flex-col gap-6">
        <div>
          <p className="font-mono text-[11px] uppercase tracking-[0.25em] text-lex-cyan/75">Advanced brief</p>
          <h2 className="mt-2 font-display text-2xl font-bold text-white">Control the output</h2>
          <p className="mt-2 text-sm leading-relaxed text-white/52">
            Audience, goal, language, length, keywords, CTA, formality, and brand voice now guide every variation.
          </p>
        </div>

        <Field label="Mode">
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {meta.transform_modes.map((mode) => (
              <button
                key={mode}
                type="button"
                onClick={() => setValue("transform_mode", mode)}
                className={`rounded-2xl border px-3 py-2.5 text-left text-xs font-bold transition-all ${
                  form.transform_mode === mode
                    ? "border-lex-cyan/70 bg-lex-cyan/10 text-white shadow-glow"
                    : "border-white/10 bg-white/[0.03] text-white/52 hover:border-white/24 hover:text-white"
                }`}
              >
                {MODE_LABELS[mode] || labelize(mode)}
              </button>
            ))}
          </div>
        </Field>

        {needsSourceText && (
          <Field label="Existing Text" hint="for rewrite, shorten, translate, tone tools">
            <TextArea
              value={form.source_text}
              onChange={update("source_text")}
              placeholder="Paste the copy you want Lexora to transform."
              rows={5}
            />
          </Field>
        )}

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label={productLabel}>
            <Input value={form.product_name} onChange={update("product_name")} placeholder="Aurora Wireless Earbuds" />
          </Field>
          <Field label="Target Audience">
            <Input value={form.target_audience} onChange={update("target_audience")} placeholder="University students" />
          </Field>
        </div>

        <Field label={descriptionLabel}>
          <TextArea
            value={form.product_description}
            onChange={update("product_description")}
            placeholder="Raw facts only — Lexora handles tone, clarity, and persuasion."
            rows={4}
          />
        </Field>

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <Field label="Objective">
            <Select value={form.content_objective} onChange={update("content_objective")}>
              {meta.objectives.map((item) => <option key={item} value={item}>{labelize(item)}</option>)}
            </Select>
          </Field>
          <Field label="Language">
            <Input value={form.language} onChange={update("language")} placeholder="English, Urdu, Spanish..." />
          </Field>
          <Field label="Copy Length">
            <Select value={form.copy_length} onChange={update("copy_length")}>
              {meta.copy_lengths.map((item) => <option key={item} value={item}>{labelize(item)}</option>)}
            </Select>
          </Field>
          <Field label="Keywords">
            <Input value={form.keywords} onChange={update("keywords")} placeholder="wireless, study, commute" />
          </Field>
          <Field label="Emoji Level">
            <Select value={form.emoji_level} onChange={update("emoji_level")}>
              {meta.emoji_levels.map((item) => <option key={item} value={item}>{labelize(item)}</option>)}
            </Select>
          </Field>
          <Field label="CTA Type">
            <Select value={form.cta_type} onChange={update("cta_type")}>
              {meta.cta_types.map((item) => <option key={item} value={item}>{labelize(item)}</option>)}
            </Select>
          </Field>
        </div>

        {form.cta_type === "custom" && (
          <Field label="Custom CTA">
            <Input value={form.custom_cta} onChange={update("custom_cta")} placeholder="Start your free trial today" />
          </Field>
        )}

        <div>
          <label className="mb-3 block font-mono text-[11px] uppercase tracking-wider text-white/45">Platform Preset</label>
          <div className="grid grid-cols-2 gap-2.5 xl:grid-cols-4">
            {meta.platforms.map((p) => (
              <button
                key={p.value}
                type="button"
                onClick={() => setValue("platform", p.value)}
                className={`rounded-2xl border px-3 py-3 text-left text-sm transition-all duration-300 ${
                  form.platform === p.value
                    ? "border-lex-cyan/70 bg-lex-cyan/10 text-white shadow-glow"
                    : "border-white/10 bg-white/[0.03] text-white/62 hover:border-white/24 hover:bg-white/[0.06] hover:text-white"
                }`}
              >
                <span className="font-semibold">{p.label}</span>
                <span className="mt-1 block font-mono text-[10px] text-white/38">{p.max_chars} chars · {p.supports_hashtags ? "hashtags" : "no tags"}</span>
              </button>
            ))}
          </div>
        </div>

        <Field label="Tone">
          <OptionPills items={meta.tones} value={form.tone} onChange={(value) => setValue("tone", value)} accent="teal" />
        </Field>

        <div className="grid gap-4 sm:grid-cols-3">
          <Field label="Formality">
            <Select value={form.formality_level} onChange={update("formality_level")}>
              {meta.formality_levels.map((item) => <option key={item} value={item}>{labelize(item)}</option>)}
            </Select>
          </Field>
          <Field label="Variations">
            <Select value={form.number_of_variations} onChange={update("number_of_variations")}>
              {[3, 4, 5].map((item) => <option key={item} value={item}>{item} versions</option>)}
            </Select>
          </Field>
          <Field label="Brand Voice">
            <Input value={form.brand_voice} onChange={update("brand_voice")} placeholder="Premium, direct, no hype" />
          </Field>
        </div>

        <details className="rounded-3xl border border-white/10 bg-midnight/45 p-4 open:bg-midnight/65">
          <summary className="cursor-pointer font-display text-sm font-bold text-white">Brand Voice Memory</summary>
          <div className="mt-5 grid gap-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Brand Description"><Input value={form.brand_voice_profile?.brand_description || ""} onChange={updateBrand("brand_description")} placeholder="What the brand does" /></Field>
              <Field label="Preferred Tone"><Input value={form.brand_voice_profile?.preferred_tone || ""} onChange={updateBrand("preferred_tone")} placeholder="Calm, premium, confident" /></Field>
              <Field label="Common Vocabulary"><Input value={form.brand_voice_profile?.vocabulary || ""} onChange={updateBrand("vocabulary")} placeholder="words Lexora should use" /></Field>
              <Field label="Words to Avoid"><Input value={form.brand_voice_profile?.words_to_avoid || ""} onChange={updateBrand("words_to_avoid")} placeholder="cheap, guaranteed, best ever" /></Field>
              <Field label="Audience Notes"><Input value={form.brand_voice_profile?.audience_notes || ""} onChange={updateBrand("audience_notes")} placeholder="students, founders, parents..." /></Field>
              <Field label="CTA Style"><Input value={form.brand_voice_profile?.cta_style || ""} onChange={updateBrand("cta_style")} placeholder="soft CTA, direct CTA, premium CTA" /></Field>
            </div>
            <Field label="Example Copy"><TextArea value={form.brand_voice_profile?.example_copy || ""} onChange={updateBrand("example_copy")} placeholder="Paste brand copy examples Lexora should emulate." rows={4} /></Field>
          </div>
        </details>

        <div className="grid grid-cols-1 gap-5 border-t border-white/10 pt-5 sm:grid-cols-2">
          <div>
            <div className="mb-2 flex items-center justify-between gap-2 font-mono text-[11px] text-white/45">
              <span title="Creativity level. Lower is safer, higher is more experimental.">TEMPERATURE ⓘ</span>
              <span className="text-lex-cyan">{Number(form.temperature).toFixed(2)}</span>
            </div>
            <input type="range" min="0" max="2" step="0.05" value={form.temperature} onChange={update("temperature")} />
          </div>
          <div>
            <div className="mb-2 flex items-center justify-between gap-2 font-mono text-[11px] text-white/45">
              <span title="Controls how broad the model's word choices can be.">TOP_P ⓘ</span>
              <span className="text-lex-cyan">{Number(form.top_p).toFixed(2)}</span>
            </div>
            <input type="range" min="0" max="1" step="0.05" value={form.top_p} onChange={update("top_p")} />
          </div>
        </div>

        <div className="sticky bottom-3 z-10 grid gap-3 rounded-3xl border border-white/10 bg-midnight/85 p-3 backdrop-blur-xl sm:grid-cols-[1fr_auto]">
          <button
            onClick={onGenerate}
            disabled={loading || !form.product_name || !form.product_description || (needsSourceText && !form.source_text)}
            className="group w-full rounded-2xl bg-lex-button px-5 py-4 font-display text-sm font-extrabold tracking-tight text-midnight shadow-glow transition-all duration-300 hover:-translate-y-0.5 hover:brightness-110 active:translate-y-0 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {loading ? "Generating with Lexora…" : "Generate Safe · Creative · Bold"}
          </button>
          <button
            type="button"
            onClick={onSaveTemplate}
            className="rounded-2xl border border-white/10 px-5 py-4 text-sm font-bold text-white/70 hover:border-lex-cyan/40 hover:text-lex-cyan"
          >
            Save Template
          </button>
        </div>
      </div>
    </div>
  );
}
