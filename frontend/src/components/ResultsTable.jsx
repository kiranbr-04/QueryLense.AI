import React, { useState, useMemo } from 'react';
import { Download, Search, ChevronLeft, ChevronRight, Hash, Clock, FileText } from 'lucide-react';

export const ResultsTable = ({ columns = [], rows = [], executionTimeMs, rowCount, truncated }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Filter rows by search term
  const filteredRows = useMemo(() => {
    if (!searchTerm) return rows;
    const term = searchTerm.toLowerCase();
    return rows.filter((row) =>
      Object.values(row).some((val) =>
        val !== null && val !== undefined && String(val).toLowerCase().includes(term)
      )
    );
  }, [rows, searchTerm]);

  // Paginated slice
  const totalPages = Math.ceil(filteredRows.length / pageSize) || 1;
  const paginatedRows = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredRows.slice(start, start + pageSize);
  }, [filteredRows, currentPage, pageSize]);

  // CSV Export
  const exportToCsv = () => {
    if (!rows.length || !columns.length) return;
    const headerRow = columns.map((c) => `"${c.name}"`).join(',');
    const bodyRows = rows.map((row) =>
      columns.map((c) => {
        const val = row[c.name];
        return val !== null && val !== undefined ? `"${String(val).replace(/"/g, '""')}"` : '""';
      }).join(',')
    );
    const csvContent = [headerRow, ...bodyRows].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `querylens_export_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (!rows || rows.length === 0) {
    return (
      <div className="border border-slate-200 rounded-lg p-8 text-center bg-white">
        <FileText className="w-8 h-8 text-slate-300 mx-auto mb-2" />
        <h4 className="text-sm font-semibold text-slate-700">No database records returned</h4>
        <p className="text-xs text-slate-400 mt-1">The query executed cleanly but 0 rows matched the condition.</p>
      </div>
    );
  }

  return (
    <div className="border border-slate-200 rounded-lg overflow-hidden bg-white shadow-xs">
      {/* Table Header Controls */}
      <div className="bg-slate-50 border-b border-slate-200 p-3 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-3">
          <span className="font-semibold text-slate-800">Actual Database Records:</span>
          <span className="inline-flex items-center gap-1 font-mono text-slate-600 bg-white border border-slate-200 px-2 py-0.5 rounded shadow-xs">
            <Hash className="w-3 h-3 text-slate-400" />
            {rowCount ?? rows.length} {rowCount === 1 ? 'row' : 'rows'}
          </span>
          {executionTimeMs !== undefined && (
            <span className="inline-flex items-center gap-1 font-mono text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded">
              <Clock className="w-3 h-3" />
              {executionTimeMs} ms
            </span>
          )}
          {truncated && (
            <span className="text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded font-medium">
              Capped at display limit
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Quick Filter */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search records..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="bg-white border border-slate-300 text-slate-800 pl-8 pr-2.5 py-1 rounded-md text-xs focus:outline-none focus:ring-1 focus:ring-brand-500 w-44"
            />
          </div>

          <button
            onClick={exportToCsv}
            className="inline-flex items-center gap-1 bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 px-2.5 py-1 rounded-md font-medium transition shadow-xs"
            title="Export exact results to CSV"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Table Data */}
      <div className="overflow-x-auto max-h-[380px]">
        <table className="w-full text-left text-xs border-collapse">
          <thead className="bg-slate-100/80 sticky top-0 border-b border-slate-200 z-10 text-slate-700 font-semibold">
            <tr>
              <th className="py-2.5 px-3 text-slate-400 w-12 text-center font-mono font-normal">#</th>
              {columns.map((col) => (
                <th key={col.name} className="py-2.5 px-3 font-semibold whitespace-nowrap">
                  <div className="flex items-center gap-1.5">
                    <span>{col.name}</span>
                    {col.type && (
                      <span className="text-[10px] uppercase font-mono font-normal text-slate-400 px-1 rounded bg-slate-200/60">
                        {col.type}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 font-sans">
            {paginatedRows.map((row, idx) => {
              const rowNum = (currentPage - 1) * pageSize + idx + 1;
              return (
                <tr key={idx} className="hover:bg-brand-50/40 transition-colors">
                  <td className="py-2 px-3 text-slate-400 text-center font-mono text-[11px] select-none">
                    {rowNum}
                  </td>
                  {columns.map((col) => {
                    const val = row[col.name];
                    const isNull = val === null || val === undefined;
                    return (
                      <td key={col.name} className="py-2 px-3 whitespace-nowrap text-slate-800">
                        {isNull ? (
                          <span className="text-slate-300 italic font-mono text-[11px]">NULL</span>
                        ) : typeof val === 'number' ? (
                          <span className="font-mono text-slate-900">{val.toLocaleString()}</span>
                        ) : (
                          <span>{String(val)}</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Table Footer Pagination */}
      <div className="bg-slate-50 border-t border-slate-200 px-3 py-2 flex items-center justify-between text-xs text-slate-500">
        <div>
          Showing {paginatedRows.length > 0 ? (currentPage - 1) * pageSize + 1 : 0} to{' '}
          {Math.min(currentPage * pageSize, filteredRows.length)} of {filteredRows.length} entries
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1">
            <span>Rows:</span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setCurrentPage(1);
              }}
              className="bg-white border border-slate-300 rounded px-1.5 py-0.5 text-xs text-slate-700"
            >
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="p-1 rounded bg-white border border-slate-200 disabled:opacity-40 hover:bg-slate-100"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>
            <span className="font-mono px-2 text-slate-700">
              {currentPage} / {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="p-1 rounded bg-white border border-slate-200 disabled:opacity-40 hover:bg-slate-100"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
