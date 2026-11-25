import React from 'react';
import { Database, ChevronDown, CheckCircle2, AlertCircle, RefreshCw, Plus } from 'lucide-react';
import { useDatabase } from '../context/DatabaseContext';

export const Header = ({ onOpenAddConnection }) => {
  const { connections, selectedConnection, setSelectedConnection, schemaLoading, fetchSchema } = useDatabase();

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between shrink-0">
      {/* Database Context Selector */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 text-slate-500 text-xs font-semibold uppercase tracking-wider">
          <Database className="w-4 h-4 text-brand-600" />
          <span>Active Target:</span>
        </div>

        {connections.length > 0 ? (
          <div className="relative flex items-center gap-2">
            <select
              value={selectedConnection?.id || ''}
              onChange={(e) => {
                const conn = connections.find((c) => c.id === e.target.value);
                if (conn) setSelectedConnection(conn);
              }}
              className="appearance-none bg-slate-50 border border-slate-300 text-slate-900 text-sm font-semibold rounded-lg pl-3 pr-8 py-1.5 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 cursor-pointer shadow-xs"
            >
              {connections.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.dialect.toUpperCase()})
                </option>
              ))}
            </select>
            <ChevronDown className="w-4 h-4 text-slate-400 absolute right-2.5 pointer-events-none" />

            {/* Health & Dialect Badges */}
            {selectedConnection && (
              <div className="flex items-center gap-2 ml-2">
                <span className="text-xs font-mono font-medium uppercase px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                  {selectedConnection.dialect}
                </span>

                {selectedConnection.status === 'connected' ? (
                  <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Connected
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-xs font-medium text-rose-600 bg-rose-50 px-2 py-0.5 rounded-full border border-rose-200">
                    <AlertCircle className="w-3.5 h-3.5" />
                    {selectedConnection.status}
                  </span>
                )}

                <button
                  onClick={fetchSchema}
                  disabled={schemaLoading}
                  title="Synchronize schema from database"
                  className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded transition"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${schemaLoading ? 'animate-spin text-brand-600' : ''}`} />
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <span className="text-xs text-amber-700 bg-amber-50 px-2.5 py-1 rounded-md border border-amber-200">
              No database connected
            </span>
            <button
              onClick={onOpenAddConnection}
              className="inline-flex items-center gap-1.5 text-xs font-medium text-brand-700 bg-brand-50 hover:bg-brand-100 px-3 py-1 rounded-md border border-brand-200 transition"
            >
              <Plus className="w-3.5 h-3.5" /> Connect Database
            </button>
          </div>
        )}
      </div>

      {/* Action shortcuts */}
      <div className="flex items-center gap-3">
        {connections.length > 0 && (
          <button
            onClick={onOpenAddConnection}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg shadow-xs transition"
          >
            <Plus className="w-3.5 h-3.5 text-brand-600" /> New Connection
          </button>
        )}
      </div>
    </header>
  );
};
