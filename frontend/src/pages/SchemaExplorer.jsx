import React from 'react';
import { GitBranch, Database, AlertCircle } from 'lucide-react';
import { useDatabase } from '../context/DatabaseContext';
import { SchemaViewer } from '../components/SchemaViewer';

export const SchemaExplorer = () => {
  const { selectedConnection, schema, schemaLoading, fetchSchema } = useDatabase();

  return (
    <div className="space-y-6 h-[calc(100vh-130px)] flex flex-col">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white p-5 rounded-xl border border-slate-200 shadow-xs shrink-0">
        <div>
          <h2 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <GitBranch className="w-5 h-5 text-brand-600" />
            Dynamic Schema Explorer
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Browse discovered tables, columns, constraints, foreign keys, and enrich business descriptions for RAG.
          </p>
        </div>

        {selectedConnection && (
          <div className="flex items-center gap-2 text-xs font-mono bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200">
            <Database className="w-4 h-4 text-slate-400" />
            <span className="font-semibold text-slate-800">{selectedConnection.name}</span>
            <span className="text-slate-400">({selectedConnection.dialect.toUpperCase()})</span>
          </div>
        )}
      </div>

      {/* Explorer Content */}
      <div className="flex-1 min-h-0">
        {selectedConnection ? (
          <SchemaViewer
            schema={schema}
            connectionId={selectedConnection.id}
            onRefresh={fetchSchema}
            loading={schemaLoading}
          />
        ) : (
          <div className="border border-slate-200 rounded-xl p-10 bg-white text-center">
            <AlertCircle className="w-8 h-8 text-amber-500 mx-auto mb-2" />
            <h4 className="text-sm font-semibold text-slate-800">No Target Database Selected</h4>
            <p className="text-xs text-slate-500 mt-1">
              Select or connect a database to explore its tables and schema relationships.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
