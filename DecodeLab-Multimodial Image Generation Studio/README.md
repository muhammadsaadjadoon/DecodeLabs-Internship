<div align="center">
  <img src="./backend/static/assets/prismora-logo.png" alt="Prismora logo" width="100" height="100" />

  <h1>Prismora</h1>

  <p><strong>AI Visual Studio</strong></p>

  <p>
    A private visual workspace for prompt development, image generation, controlled refinement,
    safety checks, visual quality review, and creative asset management.
  </p>

  <p>
    <a href="#quick-start"><img src="https://img.shields.io/badge/Run%20Locally-Quick%20Start-2AC7F7?style=for-the-badge" alt="Run Prismora locally" /></a>
    <a href="#product-tour"><img src="https://img.shields.io/badge/Product%20Tour-17%20Screens-6957FF?style=for-the-badge" alt="View the product tour" /></a>
    <a href="#system-architecture"><img src="https://img.shields.io/badge/Architecture-Full%20Stack-111827?style=for-the-badge" alt="View the system architecture" /></a>
  </p>

  <p>
    <img src="https://img.shields.io/badge/Python-3.13%2B-3776AB?logo=python&logoColor=white" alt="Python 3.13+" />
    <img src="https://img.shields.io/badge/FastAPI-0.121%2B-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
    <img src="https://img.shields.io/badge/Gemini-Prompt%20%26%20Vision%20QA-8E75B2?logo=googlegemini&logoColor=white" alt="Gemini prompt and vision QA" />
    <img src="https://img.shields.io/badge/Cloudflare%20Workers%20AI-FLUX.1%20Schnell-F38020?logo=cloudflare&logoColor=white" alt="Cloudflare Workers AI" />
    <img src="https://img.shields.io/badge/SQLite-Private%20Persistence-003B57?logo=sqlite&logoColor=white" alt="SQLite persistence" />
    <img src="https://img.shields.io/badge/Tests-8%2F8%20Passing-2EA44F?logo=pytest&logoColor=white" alt="8 of 8 tests passing" />
    <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-7C3AED" alt="MIT License" /></a>
  </p>

  <a href="./docs/assets/prismora-readme-cover.png">
    <img src="./docs/assets/prismora-readme-cover.png" alt="Prismora AI Visual Studio" width="100%" />
  </a>

  <p>
    <a href="#overview">Overview</a> ·
    <a href="#product-tour">Product Tour</a> ·
    <a href="#creation-pipeline">Pipeline</a> ·
    <a href="#system-architecture">Architecture</a> ·
    <a href="#api-reference">API</a> ·
    <a href="#quick-start">Installation</a>
  </p>
</div>

---

## Overview

Prismora started as my internship image-generation project. I chose to develop it into a full visual workspace instead of stopping at a prompt field connected to an image API.

The application covers the full creative flow. A user can create a private account, shape an early idea in **Prompt Studio**, review the enhanced production prompt, choose a visual direction and canvas, generate multiple results, refine an existing image without losing the original scene, inspect quality and safety information, organize assets, revisit earlier creation threads, and download finished work.

The project combines a responsive browser interface, a FastAPI backend, Gemini prompt and vision support, Cloudflare Workers AI image generation, SQLite persistence, user-scoped file delivery, disk-based provider processing, and automated tests.

> **Workflow:** idea → structured prompt → safety check → generation → file validation → visual review → private library → refinement.

### Project at a glance

<table>
  <tr>
    <td align="center"><strong>8</strong><br />Visual modes</td>
    <td align="center"><strong>6</strong><br />Creative finishes</td>
    <td align="center"><strong>8</strong><br />Canvas formats</td>
    <td align="center"><strong>1 to 4</strong><br />Variations per request</td>
  </tr>
  <tr>
    <td align="center"><strong>2</strong><br />Interface themes</td>
    <td align="center"><strong>22</strong><br />Application/API routes</td>
    <td align="center"><strong>7</strong><br />Core data tables</td>
    <td align="center"><strong>8/8</strong><br />Automated tests passing</td>
  </tr>
</table>

---

## What I built beyond image generation

| Area | Implementation |
|---|---|
| **Prompt intelligence** | Accepts ideas written in English, Urdu, Roman Urdu, or Hindi and turns them into focused English production prompts. |
| **Intent preservation** | Carries forward subject identity, count, relationships, action, clothing, colors, objects, environment, and details that were not requested to change. |
| **Deterministic fallback** | Uses a local structured prompt builder when Gemini enhancement is unavailable. |
| **Generation reliability** | Streams provider responses to temporary files, handles both direct-image and JSON/base64 responses, and avoids joining large payloads in memory. |
| **Asset validation** | Decodes each generated file, applies EXIF orientation, normalizes dimensions, converts the result to PNG, calculates SHA-256, and stores file metadata. |
| **Automated visual QA** | Combines image heuristics with Gemini vision review for aesthetics, semantic alignment, and output safety. |
| **Automatic recovery** | Can retry a generation when verified quality checks fail, based on a configurable policy. |
| **Private organization** | Stores user-scoped threads, messages, generations, images, settings, sessions, favorites, profile data, and history. |
| **Interface** | Includes dark and light themes, an auto-growing prompt composer, scroll preservation, inline enhancement, refinement dialogs, clear feedback, downloads, and synchronized collections. |
| **QA status handling** | Separates verified review results from fallback states, so an unavailable reviewer is never shown as a successful quality check. |

---

## Product tour

Each preview shows the full interface frame. Click an image to open the original PNG at full resolution.

### 1. Private account access

Authentication is the entry point to each user's private workspace, with separate sign-in and account-creation views.

<a href="./docs/screenshots/01-authentication-overview.png">
  <img src="./docs/screenshots/web/01-authentication-overview.webp" alt="Prismora authentication overview" width="100%" />
</a>

<table>
  <tr>
    <td width="50%" align="center" valign="top">
      <a href="./docs/screenshots/02-sign-in-panel.png">
        <img src="./docs/screenshots/web/02-sign-in-panel.webp" alt="Prismora sign-in panel" width="100%" />
      </a>
      <br /><strong>Returning user sign-in</strong>
    </td>
    <td width="50%" align="center" valign="top">
      <a href="./docs/screenshots/03-create-account-panel.png">
        <img src="./docs/screenshots/web/03-create-account-panel.webp" alt="Prismora account creation panel" width="100%" />
      </a>
      <br /><strong>Account creation</strong>
    </td>
  </tr>
</table>

### 2. Prompt Studio

Prompt Studio separates ideation from generation. Users can define an initial concept, list exclusions, refine the direction, review the production prompt, and move the final prompt into the creation workspace.

<a href="./docs/screenshots/04-prompt-studio.png">
  <img src="./docs/screenshots/web/04-prompt-studio.webp" alt="Prismora Prompt Studio" width="100%" />
</a>

### 3. Visual Library and Favorites

The Visual Library keeps generated work in one place. Favorites provides a smaller curated view for selected assets.

<table>
  <tr>
    <td width="50%" align="center" valign="top">
      <a href="./docs/screenshots/05-visual-library.png">
        <img src="./docs/screenshots/web/05-visual-library.webp" alt="Prismora Visual Library" width="100%" />
      </a>
      <br /><strong>Visual Library</strong>
    </td>
    <td width="50%" align="center" valign="top">
      <a href="./docs/screenshots/06-favorites.png">
        <img src="./docs/screenshots/web/06-favorites.webp" alt="Prismora curated favorites" width="100%" />
      </a>
      <br /><strong>Curated Selections</strong>
    </td>
  </tr>
</table>

### 4. Account and studio preferences

Account details, avatar management, email and password updates, theme selection, prompt behavior, and creative defaults are managed from the same settings area.

<table>
  <tr>
    <td width="50%" align="center" valign="top">
      <a href="./docs/screenshots/07-personal-studio-account.png">
        <img src="./docs/screenshots/web/07-personal-studio-account.webp" alt="Prismora personal studio account" width="100%" />
      </a>
      <br /><strong>Personal Studio</strong>
    </td>
    <td width="50%" align="center" valign="top">
      <a href="./docs/screenshots/08-studio-preferences.png">
        <img src="./docs/screenshots/web/08-studio-preferences.webp" alt="Prismora studio preferences" width="100%" />
      </a>
      <br /><strong>Studio Preferences</strong>
    </td>
  </tr>
</table>

### 5. Creation workspace

The main workspace brings the generation timeline, output cards, prompt composer, visual controls, refinement, downloads, and quality feedback into one screen.

<a href="./docs/screenshots/09-create-studio-light-theme.png">
  <img src="./docs/screenshots/web/09-create-studio-light-theme.webp" alt="Prismora creation workspace in Light Prism theme" width="100%" />
</a>

### 6. Creation History

Every result remains connected to its prompt, mode, canvas, timestamp, status, preview, view action, and download action.

<a href="./docs/screenshots/10-creation-history.png">
  <img src="./docs/screenshots/web/10-creation-history.webp" alt="Prismora creation history" width="100%" />
</a>

### 7. Creative controls

The inspector keeps detailed controls beside the main canvas without taking over the workspace. It includes eight visual directions, six finishes, eight canvas ratios, automatic or fixed seeds, variation count, prompt refinement, and exclusions.

<table>
  <tr>
    <td width="50%" align="center" valign="top">
      <a href="./docs/screenshots/11-visual-direction-controls.png">
        <img src="./docs/screenshots/web/11-visual-direction-controls.webp" alt="Prismora visual direction controls" width="100%" />
      </a>
      <br /><strong>Visual Direction</strong>
    </td>
    <td width="50%" align="center" valign="top">
      <a href="./docs/screenshots/12-creative-finish-controls.png">
        <img src="./docs/screenshots/web/12-creative-finish-controls.webp" alt="Prismora creative finish controls" width="100%" />
      </a>
      <br /><strong>Creative Finish</strong>
    </td>
  </tr>
  <tr>
    <td width="50%" align="center" valign="top">
      <a href="./docs/screenshots/13-canvas-format-controls.png">
        <img src="./docs/screenshots/web/13-canvas-format-controls.webp" alt="Prismora canvas format controls" width="100%" />
      </a>
      <br /><strong>Canvas Format</strong>
    </td>
    <td width="50%" align="center" valign="top">
      <a href="./docs/screenshots/14-generation-controls.png">
        <img src="./docs/screenshots/web/14-generation-controls.webp" alt="Prismora generation configuration controls" width="100%" />
      </a>
      <br /><strong>Generation Configuration</strong>
    </td>
  </tr>
</table>

### 8. Inline prompt enhancement

The composer supports a concise manual direction and a reviewable enhanced prompt. Prompt text grows within a controlled height, becomes internally scrollable when long, and remains editable before generation.

<a href="./docs/screenshots/15-prompt-composer.png">
  <img src="./docs/screenshots/web/15-prompt-composer.webp" alt="Prismora prompt composer" width="100%" />
</a>

<a href="./docs/screenshots/16-enhanced-prompt-review.png">
  <img src="./docs/screenshots/web/16-enhanced-prompt-review.webp" alt="Prismora enhanced prompt review" width="100%" />
</a>

### 9. Reviewed generation result

Each completed result shows the final production prompt, generated image, dimensions, file size, aesthetic score, prompt-alignment score, quality status, safety status, and available actions.

<p align="center">
  <a href="./docs/screenshots/17-quality-verified-generation.png">
    <img src="./docs/screenshots/web/17-quality-verified-generation.webp" alt="Prismora quality-verified generation result" width="620" />
  </a>
</p>

---

## Capabilities

### Prompt intelligence

- Enhances short or incomplete visual ideas into production-ready prompts.
- Understands English, Urdu, Roman Urdu, and Hindi input through the configured Gemini model.
- Preserves critical user intent rather than replacing the concept with an unrelated interpretation.
- Adds useful composition, lens, lighting, material, environment, depth, and quality direction.
- Supports separate exclusions/negative preferences.
- Uses a deterministic local compiler when external prompt intelligence is unavailable.
- Cleans headings, markdown fences, repeated whitespace, and overly long provider output before use.

### Generation and refinement

- Generates through Cloudflare Workers AI using the configurable FLUX.1 Schnell endpoint.
- Supports 1 to 4 variations in a single request.
- Supports automatic or explicit seed values.
- Enforces ratio-compatible output resolution through strict Pydantic validation.
- Creates refinement requests from an earlier generation.
- Locks the previous prompt as context and applies only the requested changes.
- Keeps unspecified subject and scene details consistent unless the refinement request changes them.

### Creative organization

- Private creation threads containing prompts, system responses, and generated results.
- Visual Library with full result cards.
- Curated Favorites collection.
- Creation History with reopen and download actions.
- Persistent user preferences for theme, default mode, default finish, default ratio, and auto-enhancement.
- Profile identity, avatar upload, email update, and password update.
- Deletion that removes both database records and stored generated files.

### Interface and workflow

- Dark Prism and Light Prism themes.
- Responsive sidebar and workspace layouts.
- Hash-based client routing with browser navigation support.
- Preserved workspace scroll position.
- Automatic focus on a pending or newly completed generation without forcing the page back to the top.
- Auto-growing prompt input with a controlled internal scrollbar.
- Friendly safety, quality, provider, timeout, and authentication messages.
- Toast confirmations for refinement, settings, and collection actions.

---

## Creative controls

### Visual directions

| Mode | Intended result |
|---|---|
| `realistic` | Real-camera appearance, natural textures, believable depth, no artificial look. |
| `natural` | Organic daylight, authentic surroundings, subtle contrast, realistic imperfections. |
| `cinematic` | Filmic light, dimensional composition, controlled shadows, atmospheric depth. |
| `product` | Clean campaign imagery with controlled lighting, surfaces, edges, and reflections. |
| `portrait` | Expressive facial detail, realistic eyes, clean subject separation, and professional portrait lighting. |
| `fantasy` | Concept-driven artwork with detailed environments, atmosphere, and imaginative scale. |
| `minimal` | Disciplined composition, elegant negative space, restrained presentation. |
| `illustration` | Art-directed forms, stylized storytelling, and controlled illustrative detail. |

### Creative finishes

| Finish | Direction |
|---|---|
| `premium` | Refined detail, controlled contrast, and a balanced composition. |
| `editorial` | Magazine-style composition and art direction. |
| `commercial` | Clean commercial presentation suitable for campaign assets. |
| `film` | Filmic color, lens character, and atmospheric depth. |
| `studio` | Controlled studio lighting and a clean final image. |
| `raw` | A direct rendering with minimal added styling. |

### Canvas formats

| Ratio | Output canvas | Typical use |
|---|---:|---|
| `1:1` | `1024 × 1024` | Square posts, avatars, balanced compositions. |
| `16:9` | `1344 × 768` | Widescreen scenes, banners, presentations. |
| `9:16` | `768 × 1344` | Reels, Shorts, TikTok, vertical storytelling. |
| `4:5` | `1024 × 1280` | Social portrait posts and feed campaigns. |
| `5:4` | `1280 × 1024` | Landscape editorial and product work. |
| `3:4` | `960 × 1280` | Classic portrait photography. |
| `4:3` | `1280 × 960` | Traditional landscape compositions. |
| `21:9` | `1536 × 640` | Ultra-wide cinematic frames. |

---

## Creation pipeline

```mermaid
flowchart LR
    A[User concept] --> B[Input safety gate]
    B -->|Allowed| C{Auto enhance?}
    B -->|Rejected| X[Clear safety response]
    C -->|Yes + Gemini available| D[Gemini Prompt Architect]
    C -->|No or unavailable| E[Deterministic prompt compiler]
    D --> F[Final production prompt]
    E --> F
    F --> G[Cloudflare Workers AI / FLUX.1 Schnell]
    G --> H[Stream response to temporary file]
    H --> I[Extract direct image, URL, or base64 asset]
    I --> J[Decode + EXIF transpose + normalize canvas]
    J --> K[Hash + metadata + integrity checks]
    K --> L[Pixel aesthetic heuristics]
    L --> M{Gemini vision QA available?}
    M -->|Yes| N[Safety + aesthetic + semantic review]
    M -->|No| O[Review-unavailable fallback state]
    N --> P{Pass thresholds?}
    P -->|Yes| Q[Commit validated asset]
    P -->|No, retries remain| G
    P -->|No| R[Quality-assurance response]
    O --> Q
    Q --> S[Private thread, library, history and download]
```

### Validation and recovery rules

1. **Prompt safety is evaluated before provider generation.**
2. **Provider payloads are written to disk in chunks** instead of being concatenated into one large in-memory response.
3. **Direct images and JSON responses are both supported.** JSON can contain a URL or a base64 image payload.
4. **The returned image must decode completely.** Truncated or unidentified image streams are rejected.
5. **The stored asset matches the selected canvas.** If the provider returns different dimensions, Prismora normalizes the image with high-quality resampling and records the adjustment.
6. **Every stored image receives a SHA-256 digest and file-size metadata.**
7. **Vision QA can score aesthetics and prompt alignment.** If the reviewer is unavailable, Prismora records that state instead of showing an unverified score.
8. **Quality enforcement is configurable.** A verified failure can trigger another generation attempt before the request is marked unsuccessful.

---

## Safety and quality review

### Input safety gate

`moderate_input_text()` checks the prompt before any image-generation request is sent. It rejects patterns associated with:

- explicit sexual content;
- sexual content involving minors;
- graphic gore;
- self-harm instructions or imagery;
- targeted hateful abuse.

The API returns a structured code such as `INPUT_SAFETY_REJECTED`, while the interface translates it into a respectful user-facing message.

### Binary and dimensional validation

`validate_and_normalize_image()` performs:

- format identification;
- full pixel decode;
- EXIF orientation correction;
- source-dimension capture;
- exact requested-canvas normalization;
- RGB conversion;
- optimized PNG output;
- SHA-256 calculation;
- final file-size calculation;
- dimension-adjustment metadata.

### Visual review

When Gemini vision review is configured, Prismora evaluates:

| Signal | Range | Default pass threshold |
|---|---:|---:|
| Aesthetic score | `0.0 to 10.0` | `7.0` |
| Semantic prompt alignment | `0.0 to 1.0` | `0.58` |
| Output safety | Boolean | Must be safe |

Aesthetic review considers composition, lighting, coherence, anatomy/material quality, detail, and polish. Semantic review considers subject, count, action, relationships, colors, objects, and setting.

The threshold values, review enforcement, output moderation, file limits, and retry count are configurable through environment variables.

---

## System architecture

Prismora uses a single-service architecture. FastAPI serves both the static frontend and the JSON API, which keeps local setup straightforward and avoids a separate frontend development server.

```mermaid
flowchart TB
    subgraph Browser[Browser Application]
        UI[Responsive SPA\nHTML + CSS + Vanilla JavaScript]
        ROUTER[Hash Router + Client State]
        UI <--> ROUTER
    end

    subgraph API[FastAPI Application]
        AUTH[Authentication + Sessions]
        PROFILE[Profile + Preferences]
        PROMPT[Prompt Intelligence]
        GENERATION[Generation Orchestrator]
        COLLECTIONS[Threads + Library + Favorites + History]
        FILES[User-scoped Image Delivery]
    end

    subgraph INTELLIGENCE[External Intelligence]
        GEMINI[Gemini\nPrompt enhancement + vision QA]
        CF[Cloudflare Workers AI\nFLUX.1 Schnell]
    end

    subgraph PIPELINE[Local Quality Pipeline]
        MOD[Input Moderation]
        STREAM[Disk-first Streaming]
        VALIDATE[Decode + Normalize + Hash]
        QA[Aesthetic + Semantic + Safety Review]
    end

    subgraph DATA[Private Runtime Data]
        DB[(SQLite / WAL)]
        IMG[(Generated Images)]
        AV[(Avatars)]
        TMP[(Temporary Files)]
    end

    Browser <-->|Same-origin HTTP + HttpOnly session cookie| API
    PROMPT --> GEMINI
    GENERATION --> MOD --> CF
    CF --> STREAM --> VALIDATE --> QA
    QA --> GEMINI
    AUTH --> DB
    PROFILE --> DB
    COLLECTIONS --> DB
    GENERATION --> DB
    VALIDATE --> IMG
    PROFILE --> AV
    STREAM --> TMP
    FILES --> IMG
```

### Key architecture choices

- **Same-origin application:** frontend and API are served from one FastAPI process.
- **No frontend build step:** the interface is delivered as static HTML, CSS, and JavaScript.
- **SQLite WAL mode:** suited to local development and single-instance demonstration workloads.
- **Disk-first provider handling:** lower peak memory usage for large JSON and base64 responses.
- **Provider abstraction points:** prompt enhancement, image generation, and vision QA are separated into clear functions.
- **Runtime storage isolation:** generated data is excluded from source control.
- **Strict schema validation:** supported modes, finishes, ratios, resolutions, variation counts, and seed limits are enforced at the API boundary.

---

## Authentication and data protection

### Security controls

- Passwords are hashed using **PBKDF2-HMAC-SHA256 with 250,000 iterations** and a random 16-byte salt.
- Password verification uses `hmac.compare_digest()` to avoid simple timing comparisons.
- Session tokens are generated with `secrets.token_urlsafe(48)`.
- Only a SHA-256 hash of each session token is stored in SQLite.
- Session cookies are `HttpOnly`, `SameSite=Lax`, scoped to `/`, and expire after 14 days.
- Logout removes the stored session and clears the browser cookie.
- Recovery requests use a generic response to avoid revealing whether an email exists.
- Generation, thread, favorite, deletion, and image queries are scoped to the authenticated user.
- Generated image delivery checks both the filename and the owning user before returning a file.
- Avatar uploads are limited to 5 MB, decoded as images, resized to a maximum of 512 × 512, and saved as JPEG.
- `.env`, databases, generated images, avatars, logs, and temporary data are excluded from Git.

> **Production note:** the current local-development cookie uses `secure=False`. A deployment behind HTTPS should set `Secure`, add CSRF protection for state-changing routes, configure rate limits, and move secrets to the platform secret manager.

---

## Data model

```mermaid
erDiagram
    USERS ||--o{ SESSIONS : owns
    USERS ||--|| SETTINGS : configures
    USERS ||--o{ THREADS : creates
    USERS ||--o{ MESSAGES : writes
    USERS ||--o{ GENERATIONS : requests
    USERS ||--o{ IMAGES : owns
    THREADS ||--o{ MESSAGES : contains
    THREADS ||--o{ GENERATIONS : contains
    GENERATIONS ||--o{ IMAGES : produces

    USERS {
        integer id PK
        text name
        text email UK
        text password_hash
        text avatar_path
        text created_at
    }
    SESSIONS {
        text token_hash PK
        integer user_id FK
        text created_at
        text expires_at
    }
    SETTINGS {
        integer user_id PK,FK
        text theme
        text default_mode
        text default_ratio
        text default_style
        integer auto_enhance
    }
    THREADS {
        integer id PK
        integer user_id FK
        text title
        text created_at
        text updated_at
    }
    MESSAGES {
        integer id PK
        integer thread_id FK
        integer user_id FK
        text role
        text content
        integer generation_id
        text created_at
    }
    GENERATIONS {
        integer id PK
        integer user_id FK
        integer thread_id FK
        text prompt
        text enhanced_prompt
        text negative_prompt
        text mode
        text style
        text aspect_ratio
        integer width
        integer height
        integer count
        integer seed
        text provider
        text model
        text status
        integer favorite
        text safety_status
        text quality_status
        integer qa_attempts
        text created_at
    }
    IMAGES {
        integer id PK
        integer generation_id FK
        integer user_id FK
        text file_path
        text mime_type
        integer width
        integer height
        integer source_width
        integer source_height
        integer dimension_adjusted
        real aesthetic_score
        real semantic_score
        integer qa_passed
        text qa_method
        text moderation_status
        text sha256
        integer size_bytes
        text created_at
    }
```

---

## Technology stack

| Layer | Technology | Responsibility |
|---|---|---|
| Application server | FastAPI | Static interface, REST endpoints, validation, authentication, orchestration. |
| Runtime | Python 3.13+ | Backend logic, provider integration, storage, safety, and QA. |
| Validation | Pydantic 2 | Strict request models and compatible canvas validation. |
| Prompt intelligence | Google Gemini | Prompt enhancement and multilingual concept interpretation. |
| Vision intelligence | Google Gemini | Output safety, aesthetic scoring, and semantic prompt alignment. |
| Image generation | Cloudflare Workers AI | FLUX.1 Schnell image generation. |
| HTTP client | Requests | Provider calls and streamed response handling. |
| Image processing | Pillow | Decode, EXIF transpose, resize, normalize, convert, inspect, and score. |
| Persistence | SQLite | Users, sessions, settings, threads, messages, generations, and image metadata. |
| Frontend | HTML, CSS, Vanilla JavaScript | Responsive SPA, client state, routing, interaction, and themes. |
| Testing | Pytest + FastAPI TestClient | API, schema, moderation, streaming extraction, and normalization tests. |
| Automation | GitHub Actions | Repeatable dependency installation and test execution. |

---

## Repository structure

```text
Prismora-AI-Visual-Studio/
├── .github/
│   └── workflows/
│       └── tests.yml
├── backend/
│   ├── main.py                     # FastAPI app, routes, DB, auth and orchestration
│   ├── quality_pipeline.py         # Safety, streaming, validation and visual QA
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── pytest.ini
│   ├── static/
│   │   ├── index.html
│   │   ├── css/style.css
│   │   ├── js/app.js
│   │   └── assets/                 # Prismora brand assets
│   ├── storage/
│   │   ├── avatars/.gitkeep
│   │   ├── images/.gitkeep
│   │   ├── logs/.gitkeep
│   │   └── tmp/.gitkeep
│   └── tests/
│       ├── test_core.py
│       └── test_quality_pipeline.py
├── docs/
│   ├── architecture.md
│   ├── assets/
│   │   ├── prismora-readme-cover.png
│   │   └── prismora-social-preview.png
│   └── screenshots/
│       ├── 01-authentication-overview.png
│       ├── ...
│       ├── 17-quality-verified-generation.png
│       └── web/                    # Optimized README previews
├── scripts/
│   ├── setup_unix.sh
│   ├── setup_windows.bat
│   ├── setup_windows.ps1
│   ├── run_unix.sh
│   ├── run_windows.bat
│   └── run_windows.ps1
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
└── SECURITY.md
```

---

## API reference

All protected routes require the `prismora_session` cookie created during registration or login.

<details>
<summary><strong>Application and health</strong></summary>

| Method | Route | Description |
|---|---|---|
| `GET` | `/` | Serves the Prismora SPA. |
| `GET` | `/api/health` | Returns database, provider, storage, threshold, and QA configuration status. |
| `GET` | `/{path:path}` | Serves static files or falls back to the SPA entry point. |

</details>

<details>
<summary><strong>Authentication</strong></summary>

| Method | Route | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Creates a user, default settings, and a session. |
| `POST` | `/api/auth/login` | Verifies credentials and creates a session. |
| `POST` | `/api/auth/forgot-password` | Records a recovery request and returns a generic response. |
| `POST` | `/api/auth/logout` | Deletes the active server-side session and cookie. |
| `GET` | `/api/auth/me` | Returns the authenticated public user profile. |

</details>

<details>
<summary><strong>Profile and settings</strong></summary>

| Method | Route | Description |
|---|---|---|
| `GET` | `/api/settings` | Returns the authenticated user's creative defaults. |
| `PUT` | `/api/settings` | Updates theme, mode, ratio, finish, and auto-enhancement. |
| `PUT` | `/api/profile` | Updates the user's name and email. |
| `PUT` | `/api/profile/password` | Changes the password after current-password verification. |
| `POST` | `/api/profile/avatar` | Uploads and normalizes a profile portrait. |
| `GET` | `/api/profile/avatar/{user_id}` | Returns a stored profile portrait. |

</details>

<details>
<summary><strong>Prompt intelligence and generation</strong></summary>

| Method | Route | Description |
|---|---|---|
| `POST` | `/api/prompt/enhance` | Compiles an idea into a production-ready prompt. |
| `POST` | `/api/generations` | Runs moderation, enhancement, generation, validation, QA, persistence, and messaging. |
| `GET` | `/api/generations` | Lists up to 120 user-scoped generations; supports a favorite filter. |
| `POST` | `/api/generations/{generation_id}/favorite` | Toggles favorite status. |
| `DELETE` | `/api/generations/{generation_id}` | Deletes a generation and its stored assets. |
| `GET` | `/api/images/{filename}` | Returns a generated image only when owned by the current user. |

</details>

<details>
<summary><strong>Threads and history</strong></summary>

| Method | Route | Description |
|---|---|---|
| `GET` | `/api/threads` | Lists up to 80 creation sessions ordered by recent activity. |
| `GET` | `/api/threads/{thread_id}` | Returns one thread with messages and generations. |

</details>

### Example generation request

```json
{
  "prompt": "A confident rescue dog standing beside a rain-covered city window",
  "negative_prompt": "text, watermark, distorted anatomy, duplicate dog",
  "mode": "cinematic",
  "style": "premium",
  "aspect_ratio": "4:5",
  "resolution": "auto",
  "count": 1,
  "seed": 82431,
  "auto_enhance": true,
  "thread_id": null,
  "refine_from_generation_id": null,
  "refine_instruction": ""
}
```

### Example refinement request

```json
{
  "prompt": "Use the previous generation as the locked base scene",
  "negative_prompt": "text, watermark, duplicate subjects",
  "mode": "cinematic",
  "style": "premium",
  "aspect_ratio": "4:5",
  "resolution": "auto",
  "count": 1,
  "seed": null,
  "auto_enhance": true,
  "thread_id": 14,
  "refine_from_generation_id": 37,
  "refine_instruction": "Replace only the background with a quiet blue-hour city street"
}
```

---

## Quick start

### Prerequisites

- Python **3.13 or newer**
- `pip`
- A Cloudflare account with Workers AI access for live generation
- A Gemini API key for prompt enhancement and visual review

> Prismora can still compile prompts locally without Gemini. Live generated images require the Cloudflare credentials unless `ALLOW_DEV_PLACEHOLDER=true` is enabled for development previews.

### 1. Clone and enter the repository

```bash
git clone <your-repository-url>
cd Prismora-AI-Visual-Studio
```

### 2. Create the environment file

**Windows PowerShell**

```powershell
Copy-Item .env.example .env
```

**Linux or macOS**

```bash
cp .env.example .env
```

Add your provider credentials and replace `APP_SECRET_KEY` with a long random value.

### 3. Use the setup scripts

**Windows PowerShell**

```powershell
.\scripts\setup_windows.ps1
.\scripts\run_windows.ps1
```

**Windows Command Prompt**

```bat
scripts\setup_windows.bat
scripts\run_windows.bat
```

**Linux or macOS**

```bash
chmod +x scripts/setup_unix.sh scripts/run_unix.sh
./scripts/setup_unix.sh
./scripts/run_unix.sh
```

### 4. Manual installation

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
python -m uvicorn main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

**Linux or macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
python -m uvicorn main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000` in the browser.

---

## Environment configuration

```dotenv
APP_SECRET_KEY=replace_with_a_long_random_secret
DATABASE_PATH=storage/prismora.db
ALLOW_DEV_PLACEHOLDER=false

GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.1-flash-lite

CLOUDFLARE_ACCOUNT_ID=
CLOUDFLARE_API_TOKEN=
CLOUDFLARE_MODEL=@cf/black-forest-labs/flux-1-schnell

QA_ENABLED=true
QA_ENFORCE=true
OUTPUT_MODERATION_ENABLED=true
QA_REGENERATION_ATTEMPTS=1
AESTHETIC_THRESHOLD=7.0
SEMANTIC_THRESHOLD=0.58
MAX_PROVIDER_JSON_BYTES=67108864
MAX_IMAGE_BYTES=41943040
```

| Variable | Purpose |
|---|---|
| `APP_SECRET_KEY` | Application secret placeholder for deployment configuration. Use a strong random value. |
| `DATABASE_PATH` | SQLite path; relative values are resolved under `backend/`. |
| `ALLOW_DEV_PLACEHOLDER` | Allows a locally generated placeholder when the image provider is not configured. |
| `GEMINI_API_KEY` | Enables Gemini prompt enhancement and vision QA. |
| `GEMINI_MODEL` | Configurable Gemini model identifier. |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare account identifier. |
| `CLOUDFLARE_API_TOKEN` | Token with Workers AI access. |
| `CLOUDFLARE_MODEL` | Workers AI image model identifier. |
| `QA_ENABLED` | Enables automated visual review logic. |
| `QA_ENFORCE` | Rejects verified outputs that do not meet configured thresholds. |
| `OUTPUT_MODERATION_ENABLED` | Rejects output when the configured vision reviewer marks it unsafe. |
| `QA_REGENERATION_ATTEMPTS` | Extra regeneration attempts after a verified quality failure; clamped from `0` to `2`. |
| `AESTHETIC_THRESHOLD` | Required aesthetic score when QA is enforced. |
| `SEMANTIC_THRESHOLD` | Required prompt-alignment score when QA is enforced. |
| `MAX_PROVIDER_JSON_BYTES` | Maximum streamed JSON response size. |
| `MAX_IMAGE_BYTES` | Maximum streamed or decoded image size. |

---

## Testing and continuous integration

At the time of this README update, the included test suite passes:

```text
........                                                                 [100%]
8 passed
```

Run it locally:

```bash
python -m pip install -r backend/requirements-dev.txt
python -m pytest -q backend/tests
```

### Covered behavior

- health endpoint availability;
- account registration and login;
- authenticated profile/settings retrieval;
- SPA entry-point delivery;
- rejection of unsupported mode, finish, ratio, and resolution combinations;
- input-safety rejection for explicit prompts;
- disk-based extraction of base64 provider payloads;
- exact output-canvas normalization.

The GitHub Actions workflow installs dependencies and runs the same suite on repository updates.

---

## Runtime storage

The following files are created during execution and should not be committed:

```text
backend/storage/
├── prismora.db
├── avatars/
├── images/
├── logs/
└── tmp/
```

- `prismora.db` stores application records.
- `avatars/` stores normalized profile portraits.
- `images/` stores committed generated PNG files.
- `tmp/` stores provider responses and intermediate assets only while they are being processed.
- failed generations trigger asset cleanup before the final error response.

---

## Engineering decisions

### Single-service delivery

FastAPI serves the SPA and API together, reducing setup complexity and avoiding a separate frontend runtime for an internship/demo environment.

### Disk-first provider processing

Cloud providers may return large base64 strings inside JSON. Prismora writes streamed chunks to temporary files and decodes base64 ranges from memory-mapped JSON instead of loading the entire provider response and decoded image into RAM at the same time.

### Strict canvas compatibility

The API refuses a fixed resolution that does not correspond to the selected ratio. This prevents silent mismatches between the UI selection and the generated output contract.

### Exact final dimensions

Provider output dimensions are treated as untrusted. Every accepted asset is normalized to the requested canvas and the source dimensions are retained in metadata.

### Fallback behavior

Prompt compilation can continue without Gemini by using a deterministic local direction builder. When vision QA is unavailable, the result is marked as a fallback state instead of a verified pass.

### User-scoped assets

The image route verifies database ownership before returning a generated file, even when a filename is known.

### Clear error handling

The API maps provider failures, safety rejections, quality failures, and session errors to clear messages without exposing raw infrastructure details.

---

## Production considerations

The current build is intended for internship evaluation and local demonstration. A public multi-user deployment should add the following infrastructure controls.

| Current implementation | Production recommendation |
|---|---|
| SQLite with WAL | Managed PostgreSQL with migrations and connection pooling. |
| Local image/portrait storage | Private object storage with signed delivery URLs. |
| Synchronous generation request | Background worker and job queue for long-running provider calls. |
| Local `HttpOnly` cookie | HTTPS-only `Secure` cookie, CSRF strategy, session rotation, and configurable expiry. |
| Application-level moderation | Provider moderation plus policy logging and reviewed appeal workflow where required. |
| Basic provider retry behavior | Circuit breaker, idempotency keys, quotas, and structured retry telemetry. |
| Application logs | Centralized observability, tracing, metrics, dashboards, and alerting. |
| Recovery request recording | Real transactional email with signed, expiring reset tokens. |
| Existing API validation | IP/user rate limits, abuse controls, request-size middleware, and security headers. |
| Unit/API tests | Browser end-to-end tests, provider contract tests, and deployment smoke tests. |

---

## Roadmap

- [ ] PostgreSQL persistence and migration tooling.
- [ ] S3-compatible private object storage.
- [ ] Background generation queue with progress updates.
- [ ] Real email-based password recovery.
- [ ] Additional image providers behind one generation interface.
- [ ] Named collections and project folders.
- [ ] Side-by-side refinement comparison.
- [ ] Prompt/version history with restore controls.
- [ ] Playwright end-to-end coverage.
- [ ] Accessibility and keyboard-navigation audit.
- [ ] Provider latency, retry, safety, and quality dashboards.
- [ ] Containerized production deployment.

---

## Repository presentation

`docs/assets/prismora-social-preview.png` is included as a GitHub social-preview image. Upload it through the repository settings so Prismora has a consistent branded appearance when the repository is shared.

The README uses optimized WebP previews for performance while every preview links to its original full-resolution PNG.

---

## Author

**Muhammad Saad Jadoon**  
Creator and developer of Prismora.

I developed Prismora from an internship brief into a working AI visual studio. The project covers interface design, frontend behavior, backend APIs, database modeling, authentication, provider integration, prompt enhancement, image processing, safety checks, visual review, persistence, and automated testing.

---

## License

Distributed under the [MIT License](./LICENSE).

---

<p align="center">
  <img src="./backend/static/assets/prismora-logo.png" alt="Prismora logo" width="82" />
</p>

<h3 align="center">Develop precise creative direction. Generate with confidence. Preserve every result.</h3>

<p align="center">
  Built around <strong>intent preservation</strong>, <strong>visual quality</strong>, <strong>private organization</strong>, and a <strong>carefully designed workflow</strong>.
</p>
