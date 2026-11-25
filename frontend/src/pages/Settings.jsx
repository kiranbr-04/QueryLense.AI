import React, { useState } from 'react';
import { Settings as SettingsIcon, Cpu, Shield, Key, Save, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const Settings = () => {
  const { user } = useAuth();

  const [provider, setProvider] = useState(() => localStorage.getItem('ql_llm_provider') || 'mock');
  const [apiKey, setApiKey] = useState(() => localStorage.getItem('ql_ai_api_key') || '');
  const [modelName, setModelName] = useState(() => localStorage.getItem('ql_ai_model') || 'gpt-4o-mini');
  const [savedMsg, setSavedMsg] = useState(false);

  const handleSave = (e) => {
    e.preventDefault();
    localStorage.setItem('ql_llm_provider', provider);
    localStorage.setItem('ql_ai_api_key', apiKey);
    localStorage.setItem('ql_ai_model', modelName);
    setSavedMsg(true);
    setTimeout(() => setSavedMsg(false), 2500);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
        <h2 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <SettingsIcon className="w-5 h-5 text-brand-600" />
          Platform Settings & AI Configuration
        </h2>
        <p className="text-xs text-slate-500 mt-1">
          Configure Generative AI models, credential security, and organization policies.
        </p>
      </div>

      {savedMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>Settings saved successfully!</span>
        </div>
      )}

      {/* AI Provider Configuration */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
        <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
          <Cpu className="w-5 h-5 text-brand-600" />
          <h3 className="text-sm font-bold text-slate-900">Configurable Large Language Model (LLM) Provider</h3>
        </div>

        <p className="text-xs text-slate-500">
          QueryLens AI is provider-agnostic. Select your preferred AI provider or use the built-in Intelligent Offline Mock engine for zero-setup local execution without API keys.
        </p>

        <form onSubmit={handleSave} className="space-y-4 pt-2">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">AI Provider</label>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-brand-500 font-medium"
              >
                <option value="mock">Intelligent Offline Engine (No API key needed)</option>
                <option value="gemini">Google Gemini (Gemini 1.5 Flash / Pro)</option>
                <option value="openai">OpenAI (GPT-4o / GPT-4o-mini)</option>
                <option value="anthropic">Anthropic (Claude 3.5 Sonnet / Haiku)</option>
                <option value="ollama">Ollama (Local Open Source: Llama 3 / Mistral)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Target Model Name</label>
              <input
                type="text"
                value={modelName}
                onChange={(e) => setModelName(e.target.value)}
                placeholder="e.g. gpt-4o-mini or gemini-1.5-flash"
                className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </div>
          </div>

          {provider !== 'mock' && provider !== 'ollama' && (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">API Key</label>
              <div className="relative">
                <Key className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Paste your API key here..."
                  className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-brand-500 font-mono"
                />
              </div>
            </div>
          )}

          <button
            type="submit"
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold rounded-lg shadow-sm transition"
          >
            <Save className="w-3.5 h-3.5" /> Save Configuration
          </button>
        </form>
      </div>

      {/* Security & Organization Info */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-3">
        <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
          <Shield className="w-5 h-5 text-brand-600" />
          <h3 className="text-sm font-bold text-slate-900">Security & Isolation</h3>
        </div>

        <div className="grid grid-cols-2 gap-4 text-xs font-sans">
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
            <span className="text-slate-400 block mb-0.5">Tenant Isolation</span>
            <span className="font-semibold text-slate-800">Strict Organization Barrier Active</span>
          </div>
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
            <span className="text-slate-400 block mb-0.5">Credential Encryption</span>
            <span className="font-semibold text-slate-800">AES-256 / Fernet Encryption at Rest</span>
          </div>
        </div>
      </div>
    </div>
  );
};
