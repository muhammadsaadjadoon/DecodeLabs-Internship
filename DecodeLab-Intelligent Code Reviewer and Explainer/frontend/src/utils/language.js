// Language metadata and content-first source-language detection used by the composer.
export const LANGUAGE_MAP = {
  py: { label: "Python", highlightLang: "python", ext: "py", family: "python" },
  js: { label: "JavaScript", highlightLang: "javascript", ext: "js", family: "javascript" },
  jsx: { label: "JavaScript (JSX)", highlightLang: "jsx", ext: "jsx", family: "jsx" },
  ts: { label: "TypeScript", highlightLang: "typescript", ext: "ts", family: "typescript" },
  tsx: { label: "TypeScript (TSX)", highlightLang: "tsx", ext: "tsx", family: "tsx" },
  java: { label: "Java", highlightLang: "java", ext: "java", family: "java" },
  cpp: { label: "C++", highlightLang: "cpp", ext: "cpp", family: "cpp" },
  cc: { label: "C++", highlightLang: "cpp", ext: "cc", family: "cpp" },
  c: { label: "C", highlightLang: "c", ext: "c", family: "c" },
  h: { label: "C/C++ Header", highlightLang: "cpp", ext: "h", family: "cpp" },
  hpp: { label: "C++ Header", highlightLang: "cpp", ext: "hpp", family: "cpp" },
  go: { label: "Go", highlightLang: "go", ext: "go", family: "go" },
  rb: { label: "Ruby", highlightLang: "ruby", ext: "rb", family: "ruby" },
  php: { label: "PHP", highlightLang: "php", ext: "php", family: "php" },
  cs: { label: "C#", highlightLang: "csharp", ext: "cs", family: "csharp" },
  rs: { label: "Rust", highlightLang: "rust", ext: "rs", family: "rust" },
  swift: { label: "Swift", highlightLang: "swift", ext: "swift", family: "swift" },
  kt: { label: "Kotlin", highlightLang: "kotlin", ext: "kt", family: "kotlin" },
  sql: { label: "SQL", highlightLang: "sql", ext: "sql", family: "sql" },
  sh: { label: "Shell", highlightLang: "bash", ext: "sh", family: "shell" },
  html: { label: "HTML", highlightLang: "markup", ext: "html", family: "html" },
  css: { label: "CSS", highlightLang: "css", ext: "css", family: "css" },
  txt: { label: "Plain Text", highlightLang: "text", ext: "txt", family: "text" },
};

const RULES = {
  py: [
    [/^\s*(?:async\s+)?def\s+[A-Za-z_]\w*\s*\([^\n]*\)\s*(?:->[^:]+)?\s*:/m, 16, "Python function definition"],
    [/^\s*class\s+[A-Za-z_]\w*(?:\([^)]*\))?\s*:/m, 13, "Python class definition"],
    [/^\s*(?:from\s+[\w.]+\s+import|import\s+[\w.]+)/m, 9, "Python import"],
    [/if\s+__name__\s*==\s*["']__main__["']\s*:/, 18, "Python entry point"],
    [/^\s*(?:for\s+.+\s+in\s+.+|while\s+.+|if\s+.+|elif\s+.+|else|try|except(?:\s+.+)?|finally|with\s+.+)\s*:\s*$/m, 9, "Python block syntax"],
    [/\b(?:print|input|len|range|enumerate|zip|isinstance)\s*\(/, 11, "Python built-in call"],
    [/\b(?:None|True|False|self|elif|yield|lambda|asyncio)\b/, 5, "Python keyword"],
    [/\[[^\]\n]+\s+for\s+[A-Za-z_]\w*\s+in\s+[^\]\n]+\]/, 8, "Python comprehension"],
  ],
  jsx: [
    [/(?:from\s+["']react["']|require\(["']react["']\))/, 10, "React import"],
    [/return\s*\(\s*<[A-Za-z][\w.-]*(?:\s|>)/s, 16, "JSX return tree"],
    [/(?:=>|function\s+[A-Za-z_$]\w*)\s*\(?[^=\n]*\)?\s*=>?\s*<[A-Za-z]/s, 11, "JSX component expression"],
    [/<[A-Z][A-Za-z0-9]*(?:\s|\/?>)/, 10, "JSX component"],
  ],
  tsx: [
    [/(?:interface|type)\s+[A-Z]\w*/, 7, "TypeScript declaration"],
    [/return\s*\(\s*<[A-Za-z][\w.-]*(?:\s|>)/s, 14, "TSX return tree"],
    [/(?:React\.FC|JSX\.Element|Props\s*=|:\s*React\.)/, 12, "TSX typing"],
  ],
  ts: [
    [/\binterface\s+[A-Za-z_]\w*/, 14, "TypeScript interface"],
    [/\btype\s+[A-Za-z_]\w*\s*=/, 13, "TypeScript type alias"],
    [/\benum\s+[A-Za-z_]\w*/, 12, "TypeScript enum"],
    [/(?:\(|,)\s*[A-Za-z_]\w*\??\s*:\s*(?:string|number|boolean|unknown|never|void|any|readonly|[A-Z]\w*(?:<[^>]+>)?)/, 9, "TypeScript parameter annotation"],
    [/\)\s*:\s*(?:string|number|boolean|void|Promise<|[A-Z]\w*)/, 8, "TypeScript return annotation"],
    [/\b(?:as\s+const|satisfies\s+[A-Z]\w*|implements\s+[A-Z]\w*)\b/, 8, "TypeScript-only syntax"],
  ],
  js: [
    [/\b(?:const|let|var)\s+[A-Za-z_$][\w$]*\s*=/, 8, "JavaScript declaration"],
    [/=>/, 7, "JavaScript arrow function"],
    [/\bfunction\s+[A-Za-z_$][\w$]*\s*\(/, 8, "JavaScript function"],
    [/\b(?:console\.log|document\.|window\.|module\.exports|exports\.|require\s*\()/, 12, "JavaScript runtime API"],
    [/^\s*(?:import\s+.+\s+from|export\s+(?:default\s+)?(?:async\s+)?(?:function|class|const|let|var))\b/m, 9, "JavaScript module syntax"],
    [/\b(?:async\s+function|await\s+|new\s+Promise\s*\()/, 6, "JavaScript asynchronous syntax"],
  ],
  java: [
    [/public\s+static\s+void\s+main\s*\(/, 19, "Java entry point"],
    [/System\.out\.print(?:ln)?\s*\(/, 15, "Java console API"],
    [/\bpublic\s+class\s+[A-Za-z_]\w*/, 13, "Java public class"],
    [/^\s*(?:package\s+[\w.]+\s*;|import\s+java\.)/m, 11, "Java package or import"],
    [/\b(?:private|protected|public)\s+(?:static\s+)?(?:final\s+)?(?:void|int|long|double|boolean|String|List<)/, 7, "Java member declaration"],
  ],
  cpp: [
    [/#include\s*<(?:iostream|vector|string|map|memory|algorithm)>/, 18, "C++ standard header"],
    [/\bstd::/, 14, "C++ standard namespace"],
    [/\b(?:cout|cin|cerr)\s*(?:<<|>>)/, 13, "C++ stream operation"],
    [/using\s+namespace\s+std\s*;/, 13, "C++ namespace declaration"],
    [/\btemplate\s*</, 10, "C++ template"],
    [/\b(?:unique_ptr|shared_ptr|nullptr|constexpr|namespace)\b/, 8, "C++ keyword"],
  ],
  c: [
    [/#include\s*<(?:stdio\.h|stdlib\.h|string\.h)>/, 16, "C standard header"],
    [/\b(?:printf|scanf|malloc|calloc|realloc|free|sizeof)\s*\(/, 12, "C library API"],
    [/\bstruct\s+[A-Za-z_]\w*\s*\{/, 8, "C struct"],
    [/\bint\s+main\s*\([^)]*\)\s*\{/, 7, "C entry point"],
  ],
  cs: [
    [/^\s*using\s+System(?:\.|;)/m, 18, "C# System import"],
    [/Console\.Write(?:Line)?\s*\(/, 15, "C# console API"],
    [/\bnamespace\s+[A-Za-z_]\w*/, 10, "C# namespace"],
    [/\b(?:public|private|protected|internal)\s+(?:static\s+)?(?:class|record|interface|void|string|int|bool)\b/, 8, "C# declaration"],
    [/\b(?:async\s+Task|IEnumerable<|List<|DateTime|var\s+\w+\s*=\s*new\s+)/, 6, "C# framework syntax"],
  ],
  go: [
    [/^\s*package\s+(?:main|[A-Za-z_]\w*)/m, 18, "Go package declaration"],
    [/\bfunc\s+(?:\([^)]*\)\s*)?[A-Za-z_]\w*\s*\(/, 14, "Go function"],
    [/\bfmt\.(?:Print|Printf|Println|Sprintf)\s*\(/, 13, "Go fmt API"],
    [/:=/, 7, "Go short declaration"],
    [/\bgo\s+[A-Za-z_]\w*\s*\(|\bchan\s+\w+/, 7, "Go concurrency syntax"],
  ],
  rs: [
    [/\bfn\s+main\s*\(\s*\)/, 16, "Rust entry point"],
    [/\b(?:println|print|eprintln)!\s*\(/, 14, "Rust macro"],
    [/\blet\s+mut\s+/, 10, "Rust mutable binding"],
    [/^\s*(?:use\s+std::|impl\s+|pub\s+(?:struct|enum|trait)\s+)/m, 10, "Rust declaration"],
    [/\b(?:Option<|Result<|Some\(|None\b|match\s+\w+\s*\{)/, 7, "Rust type or match syntax"],
  ],
  swift: [
    [/^\s*import\s+(?:Foundation|SwiftUI|UIKit)/m, 17, "Swift framework import"],
    [/\bfunc\s+[A-Za-z_]\w*\s*\([^)]*\)\s*(?:->\s*[^\{]+)?\s*\{/, 12, "Swift function"],
    [/\b(?:guard\s+let|if\s+let)\b/, 11, "Swift optional binding"],
    [/\b(?:let|var)\s+[A-Za-z_]\w*\s*:\s*(?:String|Int|Double|Bool|[A-Z]\w*)/, 8, "Swift typed binding"],
    [/\bprint\s*\(/, 4, "Swift print call"],
  ],
  kt: [
    [/\bfun\s+main\s*\(/, 17, "Kotlin entry point"],
    [/\bdata\s+class\s+[A-Za-z_]\w*/, 14, "Kotlin data class"],
    [/\b(?:val|var)\s+[A-Za-z_]\w*\s*(?::[^=\n]+)?=/, 9, "Kotlin property"],
    [/\bprintln\s*\(/, 10, "Kotlin output"],
    [/\b(?:when\s*\(|object\s*:\s*|companion\s+object|suspend\s+fun)\b/, 9, "Kotlin-specific syntax"],
  ],
  php: [
    [/<\?php/i, 24, "PHP opening tag"],
    [/\$[A-Za-z_]\w*\s*(?:=|->|\[)/, 11, "PHP variable"],
    [/\b(?:echo|namespace|use|require_once|include_once)\s+/i, 9, "PHP keyword"],
  ],
  rb: [
    [/^\s*def\s+[A-Za-z_]\w*[!?=]?(?:\([^\n]*\))?\s*$/m, 13, "Ruby method"],
    [/^\s*(?:class|module)\s+[A-Z]\w*/m, 12, "Ruby class or module"],
    [/\b(?:puts|require|attr_accessor|attr_reader)\b/, 11, "Ruby API"],
    [/\bdo\s*\|[^|]+\|/, 9, "Ruby block"],
    [/^\s*end\s*$/m, 5, "Ruby end keyword"],
  ],
  sql: [
    [/\bSELECT\b[\s\S]+\bFROM\b/i, 19, "SQL SELECT statement"],
    [/\b(?:CREATE\s+TABLE|ALTER\s+TABLE|INSERT\s+INTO|UPDATE\s+\w+\s+SET|DELETE\s+FROM|DROP\s+TABLE)\b/i, 18, "SQL data statement"],
    [/\b(?:JOIN|GROUP\s+BY|ORDER\s+BY|HAVING|WHERE|LIMIT)\b/i, 7, "SQL clause"],
  ],
  sh: [
    [/^#!\s*\/(?:usr\/bin\/env\s+|(?:usr\/)?bin\/)?(?:ba|z|k)?sh/m, 22, "shell shebang"],
    [/\b(?:then|fi|done|esac)\b/, 12, "shell control keyword"],
    [/\$\([^)]+\)|\$\{[^}]+\}/, 9, "shell expansion"],
    [/^\s*(?:echo|export|source|chmod|mkdir|grep|sed|awk)\b/m, 7, "shell command"],
  ],
  html: [
    [/<!doctype\s+html/i, 24, "HTML document declaration"],
    [/<html(?:\s|>)/i, 20, "HTML root element"],
    [/<(?:head|body|main|section|article|nav|header|footer|div|form|input|button)(?:\s|>)/i, 13, "HTML element"],
    [/<\/[a-z][\w-]*\s*>/i, 7, "HTML closing tag"],
  ],
  css: [
    [/(?:^|\})\s*(?:[.#][\w-]+|:root|\*|(?:html|body|main|section|article|button|input|textarea|nav|header|footer)(?:[\s.#:[>+~][^{]*)?)\s*\{[\s\S]*?[\w-]+\s*:\s*[^;{}]+;?/im, 20, "CSS selector and declaration block"],
    [/@(?:media|supports|keyframes|font-face|import|layer|tailwind)\b/i, 15, "CSS at-rule"],
    [/--[\w-]+\s*:\s*[^;{}]+;/, 11, "CSS custom property"],
    [/\b(?:display|color|background|margin|padding|font-size|grid-template|border-radius|position|width|height)\s*:\s*[^;{}]+/i, 7, "CSS property"],
  ],
};

const HARD_MATCHES = [
  ["php", /<\?php/i, "PHP opening tag"],
  ["tsx", /(?:React\.FC|JSX\.Element)[\s\S]*<[A-Za-z]|(?:interface|type)\s+[A-Z]\w*[\s\S]*return\s*\(\s*</, "TSX structure"],
  ["jsx", /(?:from\s+["']react["']|return\s*\(\s*<[A-Za-z]|=>\s*<[A-Za-z])/, "JSX structure"],
  ["html", /<!doctype\s+html|<html(?:\s|>)/i, "HTML document"],
  ["sh", /^#!\s*\/(?:usr\/bin\/env\s+|(?:usr\/)?bin\/)?(?:ba|z|k)?sh/m, "shell shebang"],
];

function resultFor(ext, score, evidence, confidence = 0.99) {
  return {
    ...LANGUAGE_MAP[ext],
    ext,
    score,
    confidence,
    evidence,
  };
}

export function detectFromFilename(filename = "") {
  const ext = filename.includes(".") ? filename.split(".").pop().toLowerCase() : "";
  return LANGUAGE_MAP[ext] || LANGUAGE_MAP.txt;
}

export function sameLanguageFamily(first, second) {
  const a = LANGUAGE_MAP[first]?.family || first;
  const b = LANGUAGE_MAP[second]?.family || second;
  return a === b;
}

export function detectLanguageFromCode(source = "") {
  const code = String(source || "").trim();
  if (code.length < 4) return null;

  for (const [ext, pattern, reason] of HARD_MATCHES) {
    if (pattern.test(code)) return resultFor(ext, 30, [reason]);
  }

  // A standalone print-style snippet without braces or terminators is overwhelmingly Python.
  if (
    /^\s*(?:print|input|len|range)\s*\([^\n]*\)\s*$/m.test(code)
    && !/[;{}]/.test(code)
    && !/\b(?:let|var|val|func|fun)\b/.test(code)
  ) {
    return resultFor("py", 24, ["Python built-in expression"]);
  }

  const candidates = Object.entries(RULES).map(([ext, rules]) => {
    let score = 0;
    const evidence = [];
    rules.forEach(([pattern, weight, reason]) => {
      pattern.lastIndex = 0;
      if (pattern.test(code)) {
        score += weight;
        evidence.push(reason);
      }
    });

    // Targeted penalties prevent common false positives without changing the UI-selected language.
    if (ext === "css" && /\b(?:def|print|import|from|console\.log|function|const|let|var)\b/.test(code)) score -= 14;
    if (ext === "py" && /(?:=>|console\.log|System\.out|std::|#include\s*<|\bpackage\s+main\b)/.test(code)) score -= 14;
    if (ext === "js" && /\b(?:interface|type)\s+[A-Z]\w*|:\s*(?:string|number|boolean)\b/.test(code)) score -= 7;
    if (ext === "html" && /(?:return\s*\(|=>)\s*<[A-Za-z]|from\s+["']react["']/.test(code)) score -= 12;
    if (ext === "php" && !/<\?php/i.test(code) && !/\$[A-Za-z_]\w*/.test(code)) score -= 12;
    if (ext === "sh" && /(?:^|\n)\s*(?:import|export)\s+|=>|\bfunction\s+|console\./m.test(code)) score -= 18;
    if (ext === "sql" && /(?:^|\n)\s*(?:import|export)\s+|\b(?:const|let|var|function)\s+|=>/m.test(code)) score -= 24;

    return { ext, score, evidence };
  }).sort((a, b) => b.score - a.score);

  const best = candidates[0];
  const runnerUp = candidates[1]?.score || 0;
  if (!best || best.score < 7) return null;

  const margin = best.score - Math.max(0, runnerUp);
  if (margin < 2 && best.score < 15) return null;

  const confidence = Math.min(0.99, 0.58 + (best.score / 60) + (Math.max(0, margin) / 50));
  return resultFor(best.ext, best.score, best.evidence, confidence);
}

export const LANGUAGE_OPTIONS = [
  "py", "js", "jsx", "ts", "tsx", "java", "cpp", "c", "h", "hpp",
  "go", "rb", "php", "cs", "rs", "swift", "kt", "sql", "sh", "html", "css"
].map((value) => ({ value, label: LANGUAGE_MAP[value].label }));

export const ACCEPTED_EXTENSIONS = Object.keys(LANGUAGE_MAP)
  .filter((extension) => extension !== "txt")
  .map((extension) => `.${extension}`)
  .join(",");

export const SUPPORTED_BADGES = ["py", "js", "ts", "java", "cpp", "go", "rb", "php", "cs", "rs"];
