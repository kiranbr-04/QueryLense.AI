import React, { useState, useEffect } from 'react';
import { Clock, Search, ChevronRight, Hash, Play, CheckCircle2, AlertCircle, Sparkles, Filter } from 'lucide-react';
import { queryService } from '../services/queryService';
import { StatusBadge } from '../components/StatusBadge';

export const QueryHistory = ({ onReplay }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterText, setFilterText] = useState('');
  const [selectedItem, setSelectedItem] = useState(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const data = await queryService.getHistory({ limit: 100 });
      setHistory(data);
      if (data.length > 0 && !selectedItem) {
        setSelectedItem(data[0]);
      }
    } catch (e) {
      console.error('Failed to load history:', e);
    } finally {
      setLoading(false);
    }
  };

  const filtered = history.filter((h) =>
    h.question.toLowerCase().includes(filterText.toLowerCase()) ||
    h.executed_sql.toLowerCase().includes(filterText.toLowerCase())
  );

  return (
    <div className="space-y-6 h-[calc(100vh-130px)] flex flex-col">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white p-5 rounded-xl border border-slate-200 shadow-xs shrink-0">
        <div>
          <h2 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Clock className="w-5 h-5 text-brand-600" />
            Query Execution History & Audit
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Complete record of conversational queries, generated SQL, execution metrics, and AI explanations.
          </p>
        </div>

        {/* Filter Input */}
        <div className="relative w-64">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search questions or SQL..."
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            className="w-full bg-slate-50 border border-slate-300 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
        </div>
      </div>

      {/* Main Split: List + Details */}
      <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* History List */}
        <div className="lg:col-span-5 bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs flex flex-col">
          <div className="p-3 bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-600 flex justify-between">
            <span>Executed Queries ({filtered.length})</span>
            <button onClick={fetchHistory} className="text-brand-600 hover:underline">
              Refresh
            </button>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
            {filtered.map((item) => {
              const isSelected = selectedItem?.id === item.id;
              return (
                <div
                  key={item.id}
                  onClick={() => setSelectedItem(item)}
                  className={`p-3.5 cursor-pointer hover:bg-slate-50 transition ${
                    isSelected ? 'bg-brand-50/40 border-l-4 border-brand-600' : ''
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold text-slate-900 line-clamp-1">{item.question}</span>
                    <StatusBadge status={item.status} />
                  </div>
                  <p className="text-[11px] font-mono text-slate-500 truncate mb-1.5">{item.executed_sql}</p>
                  <div className="flex items-center justify-between text-[10px] text-slate-400">
                    <span className="font-mono">{item.row_count} rows • {item.execution_time_ms}ms</span>
                    <span>{new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                </div>
              );
            })}

            {filtered.length === 0 && (
              <div className="p-8 text-center text-xs text-slate-400">No query history found.</div>
            )}
          </div>
        </div>

        {/* Selected Item Detail */}
        <div className="lg:col-span-7 bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs flex flex-col">
          {selectedItem ? (
            <div className="p-6 flex-1 overflow-y-auto space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                <div>
                  <h3 className="text-base font-bold text-slate-900">{selectedItem.question}</h3>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Executed on {new Date(selectedItem.created_at).toLocaleString()}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status={selectedItem.status} />
                  {onReplay && (
                    <button
                      onClick={() => onReplay('workspace', { prompt: selectedItem.question, sql: selectedItem.executed_sql })}
                      className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold shadow-xs transition"
                    >
                      <Play className="w-3 h-3 fill-current" /> Open in Workspace
                    </button>
                  )}
                </div>
              </div>

              {/* Metrics */}
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase">Status</span>
                  <p className="text-sm font-bold text-slate-800 capitalize mt-0.5">{selectedItem.status}</p>
                </div>
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase">Execution Time</span>
                  <p className="text-sm font-bold text-slate-800 font-mono mt-0.5">{selectedItem.execution_time_ms} ms</p>
                </div>
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase">Rows Retrieved</span>
                  <p className="text-sm font-bold text-slate-800 font-mono mt-0.5">{selectedItem.row_count} rows</p>
                </div>
              </div>

              {/* SQL Statement */}
              <div>
                <span className="text-xs font-semibold text-slate-700 block mb-1">Executed SQL Query:</span>
                <pre className="p-3.5 bg-slate-900 text-emerald-400 rounded-lg font-mono text-xs overflow-x-auto leading-relaxed">
                  {selectedItem.executed_sql}
                </pre>
              </div>

              {/* AI Explanation */}
              {selectedItem.ai_explanation && (
                <div>
                  <span className="text-xs font-semibold text-slate-700 flex items-center gap-1.5 mb-1">
                    <Sparkles className="w-3.5 h-3.5 text-brand-600" />
                    AI Result Explanation:
                  </span>
                  <div className="p-3.5 bg-brand-50/60 border border-brand-200/70 rounded-lg text-xs text-slate-800 leading-relaxed font-medium">
                    {selectedItem.ai_explanation}
                  </div>
                </div>
              )}

              {/* Sample Data Preview */}
              {selectedItem.result_data && selectedItem.result_data.length > 0 && (
                <div>
                  <span className="text-xs font-semibold text-slate-700 block mb-1">Sample Records Preview:</span>
                  <div className="border border-slate-200 rounded-lg overflow-x-auto max-h-48 text-xs">
                    <table className="w-full text-left">
                      <thead className="bg-slate-100 border-b border-slate-200 text-slate-700">
                        <tr>
                          {Object.keys(selectedItem.result_data[0] || {}).map((col) => (
                            <th key={col} className="p-2 font-mono font-medium">
                              {col}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                        {selectedItem.result_data.slice(0, 10).map((row, rIdx) => (
                          <tr key={rIdx} className="hover:bg-slate-50">
                            {Object.values(row).map((val, cIdx) => (
                              <td key={cIdx} className="p-2 whitespace-nowrap">
                                {String(val)}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="p-8 text-center text-xs text-slate-400 flex items-center justify-center flex-1">
              Select a query from the list to view execution details.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
