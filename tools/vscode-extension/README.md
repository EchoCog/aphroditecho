# Echo Copilot Export Integration Extension

Provides wrapper commands that expose GitHub Copilot Chat export & debug export functionality in menus, context menus, and via a keybinding.

## Features
- Wrapper commands for:
  - `github.copilot.chat.debug.exportPromptArchive`
  - `github.copilot.chat.debug.exportLogItem`
  - `github.copilot.chat.debug.export`
  - `workbench.action.chat.export`
- Command Palette entries
- Chat view title button (when chat sidebar active)
- Editor context menu item (Markdown)
- Keybinding: `Ctrl+Alt+E` (when chat sidebar focused) for full session export
- Status bar button (optional enhancement) for quick export

## Commands
| Command ID | Action |
|------------|--------|
| `echoExt.exportPromptArchive` | Export Copilot prompt archive |
| `echoExt.exportLogItem` | Export a specific chat log entry |
| `echoExt.exportAll` | Export full Copilot chat session |
| `echoExt.genericChatExport` | Generic chat export |

## Development
Install dependencies and build:
```bash
cd tools/vscode-extension
npm install
npm run build
```

Launch the extension host from VS Code (Run -> Start Debugging) or press `F5` with a launch config (create one pointing to `dist/extension.js`).

## Packaging
```bash
npm install -g @vscode/vsce
vsce package
```

## Notes
- Wrapper approach isolates us from internal command ID instability while giving menu control.
- If command IDs change upstream, only update the mappings in `extension.ts`.
