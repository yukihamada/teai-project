const vscode = require('vscode');

function activate(context) {
    let disposable = vscode.commands.registerCommand('teai-hello-world.helloWorld', function () {
        vscode.window.showInformationMessage('Hello from TeAI!');
    });

    context.subscriptions.push(disposable);
}

function deactivate() {}

module.exports = {
    activate,
    deactivate
}
