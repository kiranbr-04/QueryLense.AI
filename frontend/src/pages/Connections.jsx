import React, { useState } from 'react';
import { 
  Database, 
  Plus, 
  CheckCircle2, 
  AlertCircle, 
  RefreshCw, 
  Trash2, 
  ShieldCheck, 
  Radio, 
  Globe, 
  X,
  Play
} from 'lucide-react';
import { useDatabase } from '../context/DatabaseContext';
import { connectionService } from '../services/connectionService';

export const Connections = () => {
  const { connections, fetchConnections, setSelectedConnection, selectedConnection } = useDatabase();

  const [showModal, setShowModal] = useState(false);
  const [activeTab, setActiveTab] = useState('direct'); // 'direct' | 'agent' | 'api'
  
  // Direct form
  const [name, setName] = useState('');
  const [dialect, setDialect] = useState('postgresql');
  const [host, setHost] = useState('localhost');
  const [port, setPort] = useState(5432);
  const [databaseName, setDatabaseName] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [sslEnabled, setSslEnabled] = useState(false);

  // Testing & Saving states
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  // Auto-adjust default ports
  const handleDialectChange = (newDialect) => {
    setDialect(newDialect);
    if (newDialect === 'postgresql') setPort(5432);
    else if (newDialect === 'mysql') setPort(3306);
    else if (newDialect === 'oracle') setPort(1521);
    else if (newDialect === 'mssql') setPort(1433);
    else if (newDialect === 'sqlite') setPort(0);
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    setError(null);
    try {
      const res = await connectionService.testNew({
        dialect,
        host,
        port: Number(port),
        database_name: databaseName,
        username,
        password,
        ssl_enabled: sslEnabled,
      });
      setTestResult(res);
    } catch (e) {
      setTestResult({
        success: false,
        message: e.response?.data?.detail || 'Connection test failed.',
      });
    } finally {
      setTesting(false);
    }
  };

  const handleSaveConnection = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const created = await connectionService.create({
        name,
        connection_type: activeTab,
        dialect,
        host: dialect === 'sqlite' ? null : host,
        port: dialect === 'sqlite' ? null : Number(port),
        database_name: databaseName,
        username: dialect === 'sqlite' ? null : username,
        password: dialect === 'sqlite' ? null : password,
        ssl_enabled: sslEnabled,
      });
      await fetchConnections();
      setSelectedConnection(created);
      setShowModal(false);
      resetForm();
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to save database connection.');
    } finally {
      setSaving(false);
    }
  };

  const resetForm = () => {
    setName('');
    setDialect('postgresql');
    setHost('localhost');
    setPort(5432);
    setDatabaseName('');
    setUsername('');
    setPassword('');
    setSslEnabled(false);
    setTestResult(null);
    setError(null);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this database connection? Discovered schema metadata will be removed.')) return;
    try {
      await connectionService.delete(id);
      await fetchConnections();
    } catch (e) {
      alert('Failed to delete connection.');
    }
  };

  const handleTestExisting = async (id) => {
    try {
      const res = await connectionService.testExisting(id);
      alert(res.message);
      await fetchConnections();
    } catch (e) {
      alert('Test failed.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
        <div>
          <h2 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Database className="w-5 h-5 text-brand-600" />
            Database Connections
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Connect and manage company databases across multiple environments, networks, and cloud providers.
          </p>
        </div>

        <button
          onClick={() => {
            resetForm();
            setShowModal(true);
          }}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold shadow-xs transition"
        >
          <Plus className="w-4 h-4" /> Add Connection
        </button>
      </div>

      {/* Connections Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {connections.map((c) => {
          const isSelected = selectedConnection?.id === c.id;
          return (
            <div
              key={c.id}
              className={`bg-white border rounded-xl p-5 shadow-xs flex flex-col justify-between transition-all ${
                isSelected ? 'border-brand-500 ring-2 ring-brand-500/10' : 'border-slate-200 hover:border-slate-300'
              }`}
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div className="flex items-center gap-2.5">
                    <div className="w-9 h-9 rounded-lg bg-slate-100 border border-slate-200 flex items-center justify-center font-bold text-slate-700 text-xs">
                      {c.dialect.slice(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-slate-900 leading-snug">{c.name}</h4>
                      <span className="text-[11px] font-mono uppercase text-slate-400">
                        {c.dialect} • {c.connection_type}
                      </span>
                    </div>
                  </div>

                  <div>
                    {c.status === 'connected' ? (
                      <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                        <CheckCircle2 className="w-3 h-3" /> Online
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full border border-rose-200">
                        <AlertCircle className="w-3 h-3" /> Error
                      </span>
                    )}
                  </div>
                </div>

                <div className="bg-slate-50 rounded-lg p-2.5 font-mono text-[11px] text-slate-600 space-y-1 mb-4 border border-slate-100">
                  <div className="flex justify-between">
                    <span className="text-slate-400 font-sans">Host:</span>
                    <span className="truncate">{c.host || (c.dialect === 'sqlite' ? 'Local file' : 'Agent')}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400 font-sans">Database:</span>
                    <span className="truncate font-semibold text-slate-800">{c.database_name || 'default'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400 font-sans">Username:</span>
                    <span>{c.username || 'default'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400 font-sans">SSL / TLS:</span>
                    <span>{c.ssl_enabled ? 'Enabled' : 'Disabled'}</span>
                  </div>
                </div>

                {c.error_message && (
                  <p className="text-[11px] text-rose-600 font-medium mb-3 line-clamp-2">
                    {c.error_message}
                  </p>
                )}
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-slate-100 text-xs">
                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => setSelectedConnection(c)}
                    className={`px-3 py-1 rounded-md font-semibold text-[11px] transition ${
                      isSelected
                        ? 'bg-brand-600 text-white'
                        : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                    }`}
                  >
                    {isSelected ? 'Active Target' : 'Select'}
                  </button>
                  <button
                    onClick={() => handleTestExisting(c.id)}
                    className="p-1 text-slate-400 hover:text-slate-700 rounded hover:bg-slate-100 transition"
                    title="Ping Connection"
                  >
                    <Play className="w-3.5 h-3.5" />
                  </button>
                </div>

                <button
                  onClick={() => handleDelete(c.id)}
                  className="p-1 text-slate-400 hover:text-rose-600 rounded hover:bg-rose-50 transition"
                  title="Delete Connection"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          );
        })}

        {/* Empty state */}
        {connections.length === 0 && (
          <div className="col-span-full border-2 border-dashed border-slate-200 rounded-xl p-10 text-center bg-white">
            <Database className="w-10 h-10 text-slate-300 mx-auto mb-3" />
            <h3 className="text-base font-bold text-slate-800">No databases connected yet</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
              Connect an existing PostgreSQL, MySQL, Oracle, SQL Server, or SQLite database to start asking conversational questions.
            </p>
            <button
              onClick={() => setShowModal(true)}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold rounded-lg shadow-sm transition"
            >
              <Plus className="w-4 h-4" /> Add First Connection
            </button>
          </div>
        )}
      </div>

      {/* Add Connection Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-base font-bold text-slate-900">Add New Database Connection</h3>
              <button
                onClick={() => setShowModal(false)}
                className="p-1 text-slate-400 hover:text-slate-600 rounded"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Connectivity Method Tabs */}
            <div className="flex border-b border-slate-200 mt-4 text-xs font-semibold">
              <button
                onClick={() => setActiveTab('direct')}
                className={`py-2 px-3 border-b-2 flex items-center gap-1.5 transition ${
                  activeTab === 'direct'
                    ? 'border-brand-600 text-brand-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <Database className="w-3.5 h-3.5" /> Method 1: Direct Connection
              </button>
              <button
                onClick={() => setActiveTab('agent')}
                className={`py-2 px-3 border-b-2 flex items-center gap-1.5 transition ${
                  activeTab === 'agent'
                    ? 'border-brand-600 text-brand-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <Radio className="w-3.5 h-3.5" /> Method 2: On-Prem Agent
              </button>
              <button
                onClick={() => setActiveTab('api')}
                className={`py-2 px-3 border-b-2 flex items-center gap-1.5 transition ${
                  activeTab === 'api'
                    ? 'border-brand-600 text-brand-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <Globe className="w-3.5 h-3.5" /> Method 3: Business API
              </button>
            </div>

            {error && (
              <div className="mt-4 p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-xs">
                {error}
              </div>
            )}

            <form onSubmit={handleSaveConnection} className="mt-4 space-y-3.5">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Friendly Connection Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Production Analytics DB"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-1.5 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Database Technology / Dialect</label>
                <select
                  value={dialect}
                  onChange={(e) => handleDialectChange(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-1.5 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-brand-500"
                >
                  <option value="postgresql">PostgreSQL (psycopg)</option>
                  <option value="mysql">MySQL (PyMySQL)</option>
                  <option value="oracle">Oracle Database (python-oracledb)</option>
                  <option value="mssql">Microsoft SQL Server (pyodbc)</option>
                  <option value="sqlite">SQLite (Local / Testing)</option>
                </select>
              </div>

              {dialect !== 'sqlite' ? (
                <>
                  <div className="grid grid-cols-3 gap-2">
                    <div className="col-span-2">
                      <label className="block text-xs font-semibold text-slate-700 mb-1">Host or IP Address</label>
                      <input
                        type="text"
                        required
                        placeholder="db.company.com or 192.168.1.50"
                        value={host}
                        onChange={(e) => setHost(e.target.value)}
                        className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-1.5 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-brand-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">Port</label>
                      <input
                        type="number"
                        required
                        value={port}
                        onChange={(e) => setPort(e.target.value)}
                        className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-1.5 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-brand-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Database Name / Service Name</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. analytics or ORCLPDB1"
                      value={databaseName}
                      onChange={(e) => setDatabaseName(e.target.value)}
                      className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-1.5 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-brand-500"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">Database Username</label>
                      <input
                        type="text"
                        required
                        placeholder="readonly_user"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-1.5 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-brand-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">Password</label>
                      <input
                        type="password"
                        placeholder="••••••••"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-1.5 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-brand-500"
                      />
                    </div>
                  </div>

                  <div className="flex items-center gap-2 pt-1">
                    <input
                      type="checkbox"
                      id="sslCheck"
                      checked={sslEnabled}
                      onChange={(e) => setSslEnabled(e.target.checked)}
                      className="rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                    />
                    <label htmlFor="sslCheck" className="text-xs text-slate-700 select-none">
                      Enable SSL / TLS encryption for transit security
                    </label>
                  </div>
                </>
              ) : (
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">SQLite Database File Path</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. sample-databases/ecommerce_sample.db"
                    value={databaseName}
                    onChange={(e) => setDatabaseName(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-1.5 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">
                    Tip: Enter <span className="font-mono text-slate-700">sample-databases/ecommerce_sample.db</span> for the pre-seeded sample data.
                  </p>
                </div>
              )}

              {/* Test feedback */}
              {testResult && (
                <div
                  className={`p-3 rounded-lg text-xs flex items-center gap-2 ${
                    testResult.success
                      ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                      : 'bg-rose-50 text-rose-800 border border-rose-200'
                  }`}
                >
                  {testResult.success ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                  )}
                  <span>{testResult.message}</span>
                </div>
              )}

              {/* Actions */}
              <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-3">
                <button
                  type="button"
                  onClick={handleTestConnection}
                  disabled={testing || saving}
                  className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition disabled:opacity-50"
                >
                  {testing ? 'Testing...' : 'Test Connection'}
                </button>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-3 py-2 text-slate-500 hover:text-slate-700 text-xs font-semibold"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={saving}
                    className="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold rounded-lg shadow-sm transition disabled:opacity-50"
                  >
                    {saving ? 'Connecting...' : 'Connect Database'}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
