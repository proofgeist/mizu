# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Mizu (水) is a FileMaker theme and add-on by Proof+Geist, inspired by Material Design and IBM Carbon. It targets FileMaker 19+ and ships as a `.fmaddon` archive with a companion `.fmp12` helper file.

## Build Process

The build is a hybrid manual/scripted process — theme changes happen inside FileMaker, then XML is cleaned up and packaged:

1. Update theme in FileMaker (foundations-dev file)
2. Update version in `mizu_theme::__versionString` and `FMAddonTemplate_Version` on `__FMdAddonTemplate_Metadata` layout
3. Export via "Generate Add-on" in FileMaker (outputs to `~/Library/Application Support/FileMaker/Extensions/AddonModules`)
4. Copy `proof_mizu_theme/` folder to project root
5. Clean up extraneous XML (see below)
6. Build the archive: `source build.sh`

### Build Command

```
source build.sh
```

Requires `xar` utility. Creates `proof_mizu_theme.fmaddon` from the `proof_mizu_theme/` directory.

### XML Cleanup After Export

FileMaker generates duplicate objects that must be manually removed. Use VSCode compare against `previous/` versions to detect diffs. Key fixes:

- **Portals layout**: Remove 2 extra buttons in Portal UUID `47F1ED16-...`, set membercount to 5
- **Tabs layout**: Remove 3 duplicate button bar buttons in SlidePanel UUID `B2C37ECE-...`, set membercount to 14
- **List layout**: Remove 2 extra objects in Portal, set membercount to 3

See `build-how-to.md` for exact XPaths and UUIDs.

### Testing

1. Uninstall existing mizu add-on in FileMaker
2. Delete `.fmaddon` file and `proof_mizu_theme/` from FileMaker's `Extensions/AddonModules` directory
3. Double-click the new `.fmaddon` to install
4. Create a new FileMaker file, add the add-on, verify no duplicate buttons on Portal/List/Tabs layouts

## Architecture

This is an XML/JSON-based theme definition, not a traditional code project.

### Key Files

- **`proof_mizu_theme/template.xml`** — Main theme definition (~7,000 lines). Contains structure definitions (FieldCatalog, LayoutCatalog with 13 layouts) and literal content in CDATA sections. **Do not modify CDATA sections** — it breaks XML folding and risks corrupting the file.
- **`proof_mizu_theme/info.json`** — Core metadata (GUID, version, supported clients)
- **`proof_mizu_theme/info_[lang].json`** + **`[lang].xml`** + **`records_[lang].xml`** — Localized strings for 11 languages (en, de, es, fr, it, ja, ko, nl, pt, sv, zh)
- **`proof_mizu_helper.fmp12`** — Companion helper file (binary, Git LFS tracked)
- **`previous/`** — Previous template.xml versions kept for diff comparison during builds

### Binary Files

`.fmp12`, `.fmaddon`, and `.zip` files are tracked via Git LFS (configured in `.gitattributes`).
