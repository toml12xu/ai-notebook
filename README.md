# AI Notebook

Use AI agent skills to create a powerful AI-augmented notebook — when paired with an AI coding assistant like **Cursor** or **VS Code Copilot (GitHub Copilot)**, with **Obsidian** tool.

**Recommendation** to install [Obsidian](https://obsidian.md/) tool to view and navigate all generated outputs. Markdown notes, canvases, bases, and converted documents are best experienced in Obsidian's views. 


## What Is This?

AI Notebook **creates a new AI coach skill**, which can

- **Coach you** through concepts using Socratic questioning and save insights directly to your Obsidian vault

AI Notebook also collects a set of *skills* that can:

- **Read and convert** PDFs, DOCX, PPTX, XLSX, HTML into Markdown notes, so that LLM could understand and reason over them
- **Write rich Obsidian notes** with full support for wikilinks, callouts, properties, Mermaid diagrams, and LaTeX math
- **Build visual canvases** — mind maps, flowcharts, and knowledge graphs in Obsidian
- **Create database views** of your notes with filters, formulas, and summaries using Obsidian Bases
- **Plan complex tasks** with persistent, file-based task tracking that survives session resets
- **Create and edit** Word documents, PowerPoint presentations, and PDF forms

## Quick Start

### 1. Clone the repository

```bash
git clone https://gitlabe1.ext.net.nokia.com/l12xu/ai-notebook.git
```

### 2. Configure your AI assistant

#### For Cursor

Copy the `skills/` directory to Cursor's skills folder:

```bash
# Globally applies to all Cursor projects (recommended)

# macOS / Linux
cp -r skills/* ~/.cursor/skills/
# Windows (PowerShell)
Copy-Item -Recurse -Force skills\* $env:USERPROFILE\.cursor\skills\

# or Project-level 
cp -r skills/* <your-project>/.cursor/skills/

```

#### For VS Code + GitHub Copilot

Copy the `skills/` directory to Copilot's skills folder:

```bash
# Globally Applies to all VS Code projects (recommended)

# macOS / Linux
cp -r skills/* ~/.copilot/skills/
# Windows (PowerShell)
Copy-Item -Recurse -Force skills\* $env:USERPROFILE\.copilot\skills\

# or Project-level 
cp -r skills/* <your-project>/.github/skills/
```

### 3. Start using skills

In your AI assistant's chat, skills can be invoked **explicitly** or triggered **implicitly**:

- **Explicit**: type `/ai-coach` in chat to activate **Interactive learning** — Socratic questioning, Mermaid diagrams, adaptive pacing; and support saving notes into Obsidian 
- **Implicit**: say "learning mode", "coach mode",  — the AI detects intent and activates the skill automatically


## Skills Brief Descriptions

### Core Notebook Skills

| Skill | Description |
|-------|-------------|
| **[ai-coach](skills/ai-coach/)** | Socratic learning coach — guides you through concepts and saves insights to Obsidian. |
| **[planning-with-files](skills/planning-with-files/)** | File-based task planning — integrated with ai-coach for implementation plans with persistent progress tracking. |
| **[obsidian-markdown](skills/obsidian-markdown/)** | Write Obsidian-flavored Markdown — wikilinks, callouts, properties, LaTeX, Mermaid, etc. |
| **[obsidian-bases](skills/obsidian-bases/)** | Create Obsidian Bases (`.base`) — database views over your notes with filters and formulas. |
| **[json-canvas](skills/json-canvas/)** | Create JSON Canvas (`.canvas`) — visual mind maps and knowledge graphs in Obsidian. |

### Document Processing Skills

| Skill | Description |
|-------|-------------|
| **[docling](skills/docling/)** | Convert PDF, DOCX, PPTX, images, etc. to Markdown with OCR and table extraction. |
| **[docx](skills/docx/)** | Create and edit Word documents — tracked changes, comments, and text extraction. |
| **[pptx](skills/pptx/)** | Create and edit PowerPoint presentations — from HTML, templates, or OOXML. |
| **[pdf](skills/pdf/)** | PDF toolkit — extract text, fill forms, merge/split, OCR, and watermarking. |

## License

Individual skills may carry their own licenses. Skills with explicit license files use the **Apache License 2.0**. See each skill's directory for details.
