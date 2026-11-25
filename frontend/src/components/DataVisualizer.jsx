import React, { useState, useMemo } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from 'recharts';
import { BarChart3, LineChart as LineIcon, PieChart as PieIcon, Award, Sliders } from 'lucide-react';

const COLORS = ['#0284c7', '#0d9488', '#f59e0b', '#ec4899', '#8b5cf6', '#10b981', '#6366f1', '#f97316'];

export const DataVisualizer = ({ columns = [], rows = [], suggestion = {} }) => {
  const [chartType, setChartType] = useState(suggestion?.type || 'bar');
  const [xAxisKey, setXAxisKey] = useState(suggestion?.x_axis || '');
  const [yAxisKey, setYAxisKey] = useState(suggestion?.y_axis || '');

  // Detect candidates if not configured
  const numCols = useMemo(() => columns.filter((c) => c.type === 'number').map((c) => c.name), [columns]);
  const strCols = useMemo(() => columns.filter((c) => c.type === 'string' || c.type === 'datetime').map((c) => c.name), [columns]);

  const activeX = xAxisKey || strCols[0] || (columns[0]?.name ?? '');
  const activeY = yAxisKey || numCols[0] || (columns[1]?.name ?? '');

  // Filter rows for chart (limit to first 30 for clear readability)
  const chartData = useMemo(() => {
    return rows.slice(0, 30).map((r) => ({
      ...r,
      [activeY]: typeof r[activeY] === 'number' ? r[activeY] : parseFloat(r[activeY]) || 0,
    }));
  }, [rows, activeY]);

  if (!rows || rows.length === 0 || !numCols.length) {
    return (
      <div className="border border-slate-200 rounded-lg p-6 bg-slate-50 text-center text-xs text-slate-500">
        No numeric metrics available to visualize in this dataset.
      </div>
    );
  }

  // Summary / Metric KPI card
  if (chartType === 'metric' || (rows.length === 1 && numCols.length === 1)) {
    const val = rows[0][activeY];
    return (
      <div className="border border-slate-200 rounded-lg p-6 bg-gradient-to-tr from-brand-50 to-white text-center shadow-xs">
        <Award className="w-8 h-8 text-brand-600 mx-auto mb-2" />
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">{activeY.replace(/_/g, ' ')}</p>
        <p className="text-4xl font-extrabold text-slate-900 mt-2 font-mono">
          {typeof val === 'number' ? val.toLocaleString() : val}
        </p>
        <p className="text-xs text-slate-400 mt-1">Single metric aggregate from query result</p>
      </div>
    );
  }

  return (
    <div className="border border-slate-200 rounded-lg overflow-hidden bg-white shadow-xs">
      {/* Controls Bar */}
      <div className="bg-slate-50 border-b border-slate-200 px-4 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-1 bg-white border border-slate-200 p-0.5 rounded-lg shadow-xs">
          <button
            onClick={() => setChartType('bar')}
            className={`flex items-center gap-1 px-2.5 py-1 rounded font-medium transition ${
              chartType === 'bar' ? 'bg-brand-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" /> Bar
          </button>
          <button
            onClick={() => setChartType('line')}
            className={`flex items-center gap-1 px-2.5 py-1 rounded font-medium transition ${
              chartType === 'line' ? 'bg-brand-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <LineIcon className="w-3.5 h-3.5" /> Line
          </button>
          <button
            onClick={() => setChartType('pie')}
            className={`flex items-center gap-1 px-2.5 py-1 rounded font-medium transition ${
              chartType === 'pie' ? 'bg-brand-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <PieIcon className="w-3.5 h-3.5" /> Pie
          </button>
        </div>

        {/* Axis Pickers */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="text-slate-500 font-medium">Category (X):</span>
            <select
              value={activeX}
              onChange={(e) => setXAxisKey(e.target.value)}
              className="bg-white border border-slate-300 rounded px-2 py-1 text-slate-700 focus:outline-none"
            >
              {columns.map((c) => (
                <option key={c.name} value={c.name}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-500 font-medium">Value (Y):</span>
            <select
              value={activeY}
              onChange={(e) => setYAxisKey(e.target.value)}
              className="bg-white border border-slate-300 rounded px-2 py-1 text-slate-700 focus:outline-none"
            >
              {numCols.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Chart Canvas */}
      <div className="p-4 h-[320px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          {chartType === 'line' ? (
            <LineChart data={chartData} margin={{ top: 15, right: 25, left: 10, bottom: 25 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey={activeX} tick={{ fontSize: 11, fill: '#64748b' }} angle={-25} textAnchor="end" />
              <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
              <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderRadius: 8, border: '1px solid #e2e8f0', fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 12, paddingTop: 10 }} />
              <Line type="monotone" dataKey={activeY} stroke="#0284c7" strokeWidth={2.5} dot={{ r: 4 }} activeDot={{ r: 6 }} />
            </LineChart>
          ) : chartType === 'pie' ? (
            <PieChart>
              <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderRadius: 8, border: '1px solid #e2e8f0', fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Pie
                data={chartData.slice(0, 8)}
                dataKey={activeY}
                nameKey={activeX}
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {chartData.slice(0, 8).map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
            </PieChart>
          ) : (
            <BarChart data={chartData} margin={{ top: 15, right: 25, left: 10, bottom: 25 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey={activeX} tick={{ fontSize: 11, fill: '#64748b' }} angle={-25} textAnchor="end" />
              <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
              <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderRadius: 8, border: '1px solid #e2e8f0', fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 12, paddingTop: 10 }} />
              <Bar dataKey={activeY} fill="#0284c7" radius={[4, 4, 0, 0]} />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
};
