import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, PieChart as PieIcon, Award, Layers } from 'lucide-react';
import { useDatabase } from '../context/DatabaseContext';
import { queryService } from '../services/queryService';
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

const COLORS = ['#0284c7', '#0d9488', '#f59e0b', '#ec4899', '#8b5cf6', '#10b981'];

export const Analytics = () => {
  const { selectedConnection } = useDatabase();
  const [loading, setLoading] = useState(false);
  const [deptData, setDeptData] = useState([]);
  const [salesData, setSalesData] = useState([]);

  useEffect(() => {
    if (selectedConnection) {
      loadAnalyticsData();
    }
  }, [selectedConnection]);

  const loadAnalyticsData = async () => {
    setLoading(true);
    try {
      // 1. Department Budget / Employee count analysis
      const deptRes = await queryService.executeSql({
        connection_id: selectedConnection.id,
        sql: "SELECT name AS department, budget FROM departments ORDER BY budget DESC LIMIT 6",
        auto_explain: false,
      });
      if (deptRes.success) setDeptData(deptRes.rows);

      // 2. Monthly sales or order totals
      const salesRes = await queryService.executeSql({
        connection_id: selectedConnection.id,
        sql: "SELECT status, COUNT(*) AS count, SUM(total_amount) AS total_revenue FROM orders GROUP BY status",
        auto_explain: false,
      });
      if (salesRes.success) setSalesData(salesRes.rows);
    } catch (e) {
      console.error('Analytics load error:', e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-brand-600" />
            Visual Intelligence & Analytics
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Interactive charts generated dynamically from live business database records.
          </p>
        </div>
      </div>

      {/* Analytics Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Department Budget Bar Chart */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h4 className="text-sm font-bold text-slate-900">Department Budget Allocation</h4>
              <p className="text-xs text-slate-400">Aggregated from `departments` table</p>
            </div>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-brand-50 text-brand-700 border border-brand-200">
              Live DB
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={deptData} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="department" tick={{ fontSize: 11, fill: '#64748b' }} angle={-15} textAnchor="end" />
                <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
                <Tooltip formatter={(value) => `$${Number(value).toLocaleString()}`} />
                <Bar dataKey="budget" fill="#0284c7" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Order Revenue by Status Pie Chart */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h4 className="text-sm font-bold text-slate-900">Order Revenue by Status</h4>
              <p className="text-xs text-slate-400">Aggregated from `orders` table</p>
            </div>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
              Live DB
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Tooltip formatter={(value) => `$${Number(value).toLocaleString()}`} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Pie
                  data={salesData}
                  dataKey="total_revenue"
                  nameKey="status"
                  cx="50%"
                  cy="50%"
                  outerRadius={85}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {salesData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
