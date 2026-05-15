# Design Document: ConfigUI

**ConfigUI** is a CLI-driven terminal user interface (TUI) designed to bridge the gap between manual text editing and complex configuration management. It provides a visual, type-aware environment for editing YAML, JSON, and TOML files without the overhead of a full IDE or the friction of a standard text editor.

---

## 1. Problem Statement

The current workflow for managing deployment or model training configurations is often cumbersome:

* **Manual Friction:** Users must manually edit configuration files in a text editor, which is prone to syntax errors and lacks immediate type validation.
* **CLI Inefficiency:** Configuring agents or services via standard CLI flags requires changing values one by one or navigating clunky, non-persistent TUI sessions.
* **Context Loss:** There is no lightweight middle ground between raw text editing and heavy, application-specific dashboards.

## 2. Goals and Non-Goals

### Goals

* **Visual Configuration:** Display the entire configuration in a single TUI session with smart interpretation of fields.
* **Type-Aware Editing:** Automatically map data types to appropriate widgets (e.g., Booleans to radio buttons/switches).
* **File Management:** Allow users to view, edit, save, discard changes, or "Save As" a new file before exiting.
* **Comment Preservation:** Maintain existing comments in formats that support them (YAML, TOML) during the read/write cycle.

### Non-Goals

* **Not a Wrangler:** This is a UI layer, not a replacement for tools like **OmegaConf** or **Pydantic**.
* **No Interpolation:** Variable interpolation or "magic" syntax will be treated as plain strings.
* **Logic Engine:** The tool will not validate business logic within the config; it focuses strictly on data types and syntax.

---

## 3. Proposed Solution

### Distribution

The tool will be built with **Python** and distributed via **PyPI**. Users can install it via standard package managers:

```bash
pip install configui
# Or the preferred modern method
uv tool install configui

```

### The CLI Interface

The command-line interface is designed to be minimal:

* `configui <path-to-config>`: Open the interactive editor.
* `configui <path-to-config> -r`: Open in **Read-Only** mode.

### Technical Implementation

#### Config Handling (Strategy Pattern)

To support multiple formats while keeping the codebase extensible, we will use a **Strategy Pattern** for the Reader and Writer interfaces.

* **Internal Representation:** All configs are converted to standard Python primitives (`dict`, `list`, `float`, `int`, `str`).
* **Library Choice:**
* **YAML:** `ruamel.yaml` (selected for its superior comment-preservation capabilities).
* **TOML:** `tomlkit` (designed to preserve style and comments).
* **JSON:** Standard library `json` (as comments are not natively supported).

#### TUI Architecture

The interface will be powered by [Textual](https://textual.textualize.io).

* **Smart Widgets:**
* `bool` $\rightarrow$ **Checkbox** or **Switch**.
* `float`, `int`, `str` $\rightarrow$ **Input Box**.
* **Nested Structures** $\rightarrow$ **Collapsible** containers.
* **Theming:** User-configurable themes implemented via a Strategy Pattern to swap CSS definitions dynamically.

---

## 4. Milestones

1. **Project Scaffolding:** Set up the environment and add core dependencies (`textual`, `ruamel.yaml`, `tomlkit`).
2. **Core Interfaces:** Define the abstract base classes for Config Readers/Writers.
3. **Phase 1 - JSON:** Implement the JSON strategy (base case, no comment handling).
4. **Phase 2 - YAML & TOML:** Implement strategies with full comment and style preservation.
5. **TUI Development:** Build the dynamic form generator and navigation logic in Textual.
6. **Distribution:** Finalize documentation (README) and publish the initial version to PyPI.
