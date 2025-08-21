import * as vscode from 'vscode';

function registerWrapper(ctx: vscode.ExtensionContext, alias: string, target: string, before?: () => void) {
  const disposable = vscode.commands.registerCommand(alias, async (...args) => {
    try {
      before?.();
      await vscode.commands.executeCommand(target, ...args);
    } catch (err) {
      vscode.window.showErrorMessage(`Failed executing ${alias}: ${String(err)}`);
    }
  });
  ctx.subscriptions.push(disposable);
}

export function activate(ctx: vscode.ExtensionContext) {
  registerWrapper(ctx, 'echoExt.exportPromptArchive', 'github.copilot.chat.debug.exportPromptArchive');
  registerWrapper(ctx, 'echoExt.exportLogItem', 'github.copilot.chat.debug.exportLogItem');
  registerWrapper(ctx, 'echoExt.exportAll', 'github.copilot.chat.debug.export');
  registerWrapper(ctx, 'echoExt.genericChatExport', 'workbench.action.chat.export');

  // Status bar quick access (optional lightweight enhancement)
  const statusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 5);
  statusItem.text = '$(export) Chat Export';
  statusItem.command = 'echoExt.exportAll';
  statusItem.tooltip = 'Export current Copilot Chat session';
  statusItem.show();
  ctx.subscriptions.push(statusItem);
}

export function deactivate() {}
