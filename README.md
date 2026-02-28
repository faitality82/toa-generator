# TOA Generator

A standalone Windows desktop app that automatically generates a **Table of Authorities** from legal briefs (.docx or .pdf). Built for solo practitioners and small firms, with a focus on Michigan courts.

## Features

- **Upload** a legal brief (.docx or .pdf)
- **Automatic citation detection** using 17+ regex patterns covering:
  - Cases (federal, state, unpublished, parallel citations)
  - Statutes (U.S.C., M.C.L., public laws)
  - Constitutional provisions (U.S. and Michigan)
  - Court rules (federal, Michigan, local)
  - Other authorities (restatements, law reviews, treatises)
  - Short forms (Id., supra, short pincites) resolved to parent citations
- **AI-powered classification** for ambiguous citations (optional, supports 22 models across 7 providers)
- **Review and edit** detected citations in an interactive table
- **Generate** a properly formatted .docx Table of Authorities with:
  - Dot leaders and right-aligned page numbers
  - Italicized case names
  - Category headers (Cases, Statutes, Constitutional Provisions, etc.)
  - Primary authority markers (*)
  - Hanging indents
- **Court presets** for Michigan COA, 6th Circuit, SCOTUS, ED/WD Michigan

## Download

Download the latest `TOAGenerator.exe` from the [Releases](../../releases) page.

## Running from Source

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python run_gui.py
```

## AI Providers (Optional)

AI classification is optional — regex handles 90%+ of citations. When enabled, supports:

| Provider | Models |
|----------|--------|
| Anthropic | Claude Sonnet 4, Claude Haiku |
| OpenAI | GPT-4o, GPT-4o Mini |
| Google | Gemini 2.0 Flash, Gemini 2.5 Pro |
| Mistral | Large, Small, Codestral |
| Cohere | Command R+, Command R |
| DeepSeek | Chat, Reasoner |
| Meta | Llama 3.3, Llama 3.1 (via Together AI) |

Toggle AI on/off in the Settings tab. API keys are saved to a local `.env` file.

## Building the Executable

```bash
pip install pyinstaller
pyinstaller toa_generator.spec --clean --noconfirm
```

The exe will be created at `dist/TOAGenerator.exe` (~80 MB).

## Tech Stack

- **GUI**: CustomTkinter (dark theme)
- **Document parsing**: python-docx, pdfplumber
- **Citation detection**: Regex pattern engine with short-form resolution
- **AI classification**: Multi-provider support (Anthropic, OpenAI, Google, Mistral, Cohere, DeepSeek, Meta)
- **Output**: python-docx with raw XML for dot leaders
- **Packaging**: PyInstaller (single-file Windows exe)
