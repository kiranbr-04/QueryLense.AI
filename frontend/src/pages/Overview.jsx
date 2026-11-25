import React, { useState, useEffect } from 'react';
import { 
  Database, 
  Sparkles, 
  Layers, 
  Zap, 
  ArrowRight, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  FileCode2,
  HardDrive
} from 'lucide-react';
import { useDatabase } from '../context/DatabaseContext';
import { queryService } from '../services/queryService';

export const Overview = ({ onNavigate }) => {
  const { connections, schema } = useDatabase();
  const [history, setHistory] = useState([]);
  const [quickQuestion, setQuickQuestion] = useState('');

  useEffect(() => {
    queryService.getHistory({ limit: 5 })
      .then((data) => setHistory(data))
      .catch((e) => console.error(e));
  }, []);

  const handleQuickSubmit = (e) => {
    e.preventDefault();
    if (!quickQuestion) return;
    onNavigate('workspace', { prompt: quickQuestion });
  };

  const totalConnected = connections.filter((c) => c.status === 'connected').length;
  const avgSpeed = history.length > 0
    ? (history.reduce((acc, h) => acc + (h.execution_time_ms || 0), 0) / history.length).toFixed(1)
    : '0';

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-brand-900 via-brand-800 to-slate-900 rounded-2xl p-6 text-white shadow-md relative overflow-hidden">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-500/20 text-brand-300 text-xs font-semibold mb-3 border border-brand-400/30">
            <Sparkles className="w-3.5 h-3.5" /> Generative AI Natural Language to SQL
          </div>
          <h2 className="text-2xl font-bold tracking-tight mb-2">
            Ask any question. Get verified database records.
          </h2>
          <p className="text-slate-300 text-xs sm:text-sm leading-relaxed mb-6">
            Query across PostgreSQL, MySQL, Oracle, SQL Server, or on-premise databases without writing manual SQL. Validated read-only execution with zero hallucinations.
          </p>

          {/* Quick Query Bar */}
          <form onSubmit={handleQuickSubmit} className="flex items-center gap-2 max-w-xl">
            <div className="relative flex-1">
              <Sparkles className="w-4 h-4 text-brand-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Ask e.g. 'Show the top five employees with the highest salary'..."
                value={quickQuestion}
                onChange={(e) => setQuickQuestion(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-white/10 hover:bg-white/15 focus:bg-white text-white focus:text-slate-900 rounded-xl text-xs sm:text-sm border border-white/20 focus:border-white focus:outline-none placeholder-slate-400 transition"
              />
            </div>
            <button
              type="submit"
              className="px-5 py-2.5 bg-brand-500 hover:bg-brand-400 text-white font-semibold rounded-xl text-xs sm:text-sm shadow-sm transition shrink-0 flex items-center gap-2"
            >
              <span>Ask AI</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Connected Databases</span>
            <Database className="w-4 h-4 text-brand-600" />
          </div>
          <p className="text-2xl font-bold text-slate-900 font-mono">{totalConnected} <span className="text-xs text-slate-400 font-sans font-normal">/ {connections.length} registered</span></p>
          <div className="mt-2 flex items-center gap-1.5 text-xs text-emerald-600 font-medium">
            <CheckCircle2 className="w-3.5 h-3.5" /> Direct & On-Prem Agents
          </div>
        </div>

        <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Schema Tables</span>
            <Layers className="w-4 h-4 text-indigo-600" />
          </div>
          <p className="text-2xl font-bold text-slate-900 font-mono">{schema.length}</p>
          <div className="mt-2 text-xs text-slate-400">
            Introspected & indexed for RAG
          </div>
        </div>

        <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Executed Queries</span>
            <FileCode2 className="w-4 h-4 text-emerald-600" />
          </div>
          <p className="text-2xl font-bold text-slate-900 font-mono">{history.length}</p>
          <div className="mt-2 text-xs text-slate-400">
            Audit-logged & validated
          </div>
        </div>

        <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Avg Response Time</span>
            <Zap className="w-4 h-4 text-amber-500" />
          </div>
          <p className="text-2xl font-bold text-slate-900 font-mono">{avgSpeed} <span className="text-xs text-slate-400 font-sans font-normal">ms</span></p>
          <div className="mt-2 text-xs text-emerald-600 font-medium">
            High performance direct execution
          </div>
        </div>
      </div>

      {/* Grid: Connected Databases & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Databases List */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-sm text-slate-900">Database Connection Status</h3>
            <button
              onClick={() => onNavigate('connections')}
              className="text-xs text-brand-600 hover:text-brand-700 font-semibold"
            >
              Manage all →
            </button>
          </div>

          <div className="flex-1 space-y-2.5">
            {connections.length > 0 ? (
              connections.map((conn) => (
                <div
                  key={conn.id}
                  className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-100 hover:border-slate-200 transition"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-white border border-slate-200 flex items-center justify-center">
                      <HardDrive className="w-4 h-4 text-slate-600" />
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-slate-800">{conn.name}</p>
                      <p className="text-[11px] text-slate-400 font-mono uppercase">
                        {conn.dialect} • {conn.connection_type}
                      </p>
                    </div>
                  </div>
                  <div>
                    {conn.status === 'connected' ? (
                      <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                        <CheckCircle2 className="w-3 h-3" /> Online
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full border border-rose-200">
                        <AlertCircle className="w-3 h-3" /> {conn.status}
                      </span>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-xs text-slate-400">
                No database registered yet.{' '}
                <button
                  onClick={() => onNavigate('connections')}
                  className="text-brand-600 font-semibold hover:underline"
                >
                  Connect your first database
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Recent Queries */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-sm text-slate-900">Recent Natural Language Queries</h3>
            <button
              onClick={() => onNavigate('history')}
              className="text-xs text-brand-600 hover:text-brand-700 font-semibold"
            >
              Full history →
            </button>
          </div>

          <div className="flex-1 space-y-2.5">
            {history.length > 0 ? (
              history.map((h) => (
                <div
                  key={h.id}
                  onClick={() => onNavigate('workspace', { prompt: h.question, sql: h.executed_sql })}
                  className="p-3 rounded-lg bg-slate-50 border border-slate-100 hover:border-slate-200 hover:bg-slate-100/60 cursor-pointer transition"
                >
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-semibold text-slate-800 line-clamp-1">{h.question}</span>
                    <span className="font-mono text-[10px] text-slate-400 shrink-0">
                      {h.execution_time_ms} ms
                    </span>
                  </div>
                  <p className="text-[11px] font-mono text-slate-500 truncate">{h.executed_sql}</p>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-xs text-slate-400">
                No queries executed yet. Try asking your first question!
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
