import React, { useState } from 'react';
import { Table, Key, Link2, Search, Edit3, Check, RefreshCw, Layers } from 'lucide-react';
import { schemaService } from '../services/schemaService';

export const SchemaViewer = ({ schema = [], connectionId, onRefresh, loading }) => {
  const [filterText, setFilterText] = useState('');
  const [expandedTable, setExpandedTable] = useState(schema[0]?.table_name || null);
  const [editingTableId, setEditingTableId] = useState(null);
  const [descInput, setDescInput] = useState('');
  const [savingDesc, setSavingDesc] = useState(false);

  const filteredSchema = schema.filter((t) =>
    t.table_name.toLowerCase().includes(filterText.toLowerCase()) ||
    t.columns.some((c) => c.name.toLowerCase().includes(filterText.toLowerCase()))
  );

  const startEditDescription = (table) => {
    setEditingTableId(table.id);
    setDescInput(table.business_description || '');
  };

  const saveDescription = async (table) => {
    setSavingDesc(true);
    try {
      await schemaService.updateDescription(connectionId, table.id, descInput);
      table.business_description = descInput;
      setEditingTableId(null);
    } catch (e) {
      console.error('Failed to save description:', e);
    } finally {
      setSavingDesc(false);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs flex flex-col h-full">
      {/* Schema Header */}
      <div className="p-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Layers className="w-5 h-5 text-brand-600" />
          <h3 className="font-semibold text-slate-800 text-sm">Discovered Schema ({schema.length} tables)</h3>
        </div>
        <button
          onClick={onRefresh}
          disabled={loading}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-100 border border-slate-200 px-3 py-1.5 rounded-lg shadow-xs transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-brand-600' : ''}`} />
          <span>Refresh Schema</span>
        </button>
      </div>

      {/* Filter Input */}
      <div className="p-3 border-b border-slate-100 bg-white">
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search tables or columns..."
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
        </div>
      </div>

      {/* Tables Accordion List */}
      <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
        {filteredSchema.map((table) => {
          const isExpanded = expandedTable === table.table_name;
          const pks = new Set(table.primary_keys || []);
          const fks = table.foreign_keys || [];

          return (
            <div key={table.id} className="bg-white">
              {/* Table Bar */}
              <div
                onClick={() => setExpandedTable(isExpanded ? null : table.table_name)}
                className={`p-3.5 flex items-center justify-between cursor-pointer hover:bg-slate-50 transition ${
                  isExpanded ? 'bg-brand-50/30' : ''
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Table className={`w-4 h-4 ${isExpanded ? 'text-brand-600' : 'text-slate-400'}`} />
                  <div>
                    <span className="font-semibold text-xs text-slate-800">{table.table_name}</span>
                    <span className="text-[10px] text-slate-400 ml-2 font-mono">
                      {table.columns.length} columns {table.row_count_estimate !== null ? `• ~${table.row_count_estimate} rows` : ''}
                    </span>
                  </div>
                </div>
                <span className="text-xs text-slate-400 font-mono">{isExpanded ? '−' : '+'}</span>
              </div>

              {/* Table Details */}
              {isExpanded && (
                <div className="px-4 pb-4 pt-1 bg-slate-50/50 border-t border-slate-100 space-y-3">
                  {/* Business Description */}
                  <div className="p-2.5 bg-white rounded-lg border border-slate-200 text-xs">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-slate-600 text-[11px] uppercase tracking-wider">Business Meaning (RAG Context)</span>
                      {editingTableId !== table.id && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            startEditDescription(table);
                          }}
                          className="text-slate-400 hover:text-brand-600 inline-flex items-center gap-1 text-[11px]"
                        >
                          <Edit3 className="w-3 h-3" /> Edit
                        </button>
                      )}
                    </div>
                    {editingTableId === table.id ? (
                      <div className="flex items-center gap-2 mt-1">
                        <input
                          type="text"
                          value={descInput}
                          onChange={(e) => setDescInput(e.target.value)}
                          placeholder="e.g. Master record of customers and accounts..."
                          className="flex-1 bg-slate-50 border border-slate-300 rounded px-2 py-1 text-xs text-slate-800"
                        />
                        <button
                          onClick={() => saveDescription(table)}
                          disabled={savingDesc}
                          className="p-1 bg-brand-600 text-white rounded hover:bg-brand-700"
                        >
                          <Check className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ) : (
                      <p className="text-slate-600 text-xs italic">
                        {table.business_description || 'No business description added yet. Add one to help AI retrieve this table.'}
                      </p>
                    )}
                  </div>

                  {/* Columns Table */}
                  <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-100 text-slate-600 font-semibold text-[11px]">
                        <tr>
                          <th className="py-1.5 px-3">Column</th>
                          <th className="py-1.5 px-3">Type</th>
                          <th className="py-1.5 px-3 text-right">Attributes</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                        {table.columns.map((c) => {
                          const isPk = pks.has(c.name);
                          return (
                            <tr key={c.name} className="hover:bg-slate-50">
                              <td className="py-1.5 px-3 flex items-center gap-1.5 text-slate-800 font-semibold font-sans">
                                {isPk && <Key className="w-3 h-3 text-amber-500 shrink-0" />}
                                <span>{c.name}</span>
                              </td>
                              <td className="py-1.5 px-3 text-slate-500">{c.type}</td>
                              <td className="py-1.5 px-3 text-right text-slate-400 font-sans">
                                {isPk && (
                                  <span className="text-[10px] bg-amber-50 text-amber-700 px-1.5 py-0.5 rounded border border-amber-200 font-semibold mr-1">
                                    PK
                                  </span>
                                )}
                                {!c.nullable && <span className="text-[10px] text-slate-400">NOT NULL</span>}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>

                  {/* Foreign Keys / Relationships */}
                  {fks.length > 0 && (
                    <div className="text-xs bg-white p-2.5 rounded-lg border border-slate-200">
                      <span className="font-semibold text-slate-600 text-[11px] uppercase tracking-wider block mb-1">
                        Relationships (Foreign Keys)
                      </span>
                      <div className="space-y-1">
                        {fks.map((fk, idx) => (
                          <div key={idx} className="flex items-center gap-1.5 text-slate-700 font-mono text-[11px]">
                            <Link2 className="w-3.5 h-3.5 text-brand-600 shrink-0" />
                            <span>{fk.constrained_columns?.join(', ')}</span>
                            <span className="text-slate-400">→</span>
                            <span className="font-semibold text-brand-700">
                              {fk.referred_table}({fk.referred_columns?.join(', ')})
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
