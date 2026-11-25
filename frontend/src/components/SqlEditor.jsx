import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import { Copy, Check, Play, Terminal } from 'lucide-react';

export const SqlEditor = ({ value, onChange, onExecute, readOnly = false, height = '180px' }) => {
  const [copied, setCopied] = useState(false);
  const [editorError, setEditorError] = useState(false);

  const handleCopy = () => {
    if (!value) return;
    navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleEditorMount = (editor, monaco) => {
    // Add command for Ctrl+Enter / Cmd+Enter
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => {
      if (onExecute) onExecute();
    });
  };

  return (
    <div className="border border-slate-200 rounded-lg overflow-hidden bg-white shadow-xs">
      {/* Editor Toolbar */}
      <div className="bg-slate-50 border-b border-slate-200 px-3 py-1.5 flex items-center justify-between text-xs">
        <div className="flex items-center gap-2 text-slate-600 font-mono font-medium">
          <Terminal className="w-3.5 h-3.5 text-brand-600" />
          <span>SQL Query (Read-Only Validated)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-[11px] text-slate-400 font-sans mr-2 hidden sm:inline">
            Press <kbd className="px-1.5 py-0.5 bg-white border border-slate-300 rounded text-[10px] shadow-xs">Ctrl+Enter</kbd> to execute
          </span>
          <button
            onClick={handleCopy}
            className="inline-flex items-center gap-1 px-2 py-1 rounded bg-white hover:bg-slate-100 text-slate-600 border border-slate-200 transition"
            title="Copy SQL"
          >
            {copied ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
          {onExecute && (
            <button
              onClick={onExecute}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-brand-600 hover:bg-brand-700 text-white font-medium shadow-xs transition"
            >
              <Play className="w-3 h-3 fill-current" />
              <span>Run</span>
            </button>
          )}
        </div>
      </div>

      {/* Editor Body */}
      <div style={{ height }}>
        {!editorError ? (
          <Editor
            height="100%"
            language="sql"
            value={value}
            onChange={(val) => onChange && onChange(val || '')}
            onMount={handleEditorMount}
            options={{
              minimap: { enabled: false },
              fontSize: 13,
              fontFamily: "'JetBrains Mono', Consolas, monospace",
              readOnly: readOnly,
              lineNumbers: 'on',
              scrollBeyondLastLine: false,
              wordWrap: 'on',
              automaticLayout: true,
              padding: { top: 8, bottom: 8 },
              tabSize: 2,
            }}
            loading={
              <div className="p-4 text-xs font-mono text-slate-400">Loading SQL editor...</div>
            }
          />
        ) : (
          <textarea
            value={value}
            onChange={(e) => onChange && onChange(e.target.value)}
            readOnly={readOnly}
            className="w-full h-full p-3 font-mono text-xs bg-slate-900 text-emerald-400 focus:outline-none resize-none"
          />
        )}
      </div>
    </div>
  );
};
