import React, { useState, useEffect } from 'react';
import { Radio, Plus, CheckCircle2, AlertCircle, Copy, Check, Terminal, Shield, Trash2 } from 'lucide-react';
import { agentService } from '../services/agentService';

export const AgentsView = () => {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [agentName, setAgentName] = useState('');
  const [registeredToken, setRegisteredToken] = useState(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchAgents();
  }, []);

  const fetchAgents = async () => {
    setLoading(true);
    try {
      const data = await agentService.list();
      setAgents(data);
    } catch (e) {
      console.error('Failed to load agents:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    if (!agentName) return;
    try {
      const data = await agentService.register(agentName);
      setRegisteredToken(data.agent_token);
      setAgentName('');
      await fetchAgents();
    } catch (e) {
      alert('Failed to register agent.');
    }
  };

  const handleRevoke = async (id) => {
    if (!window.confirm('Revoke access for this agent? Its connection will be terminated.')) return;
    try {
      await agentService.revoke(id);
      await fetchAgents();
    } catch (e) {
      alert('Failed to revoke agent.');
    }
  };

  const copyToken = (tok) => {
    navigator.clipboard.writeText(tok);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Radio className="w-5 h-5 text-brand-600" />
            QueryLens Connector Agents (On-Premise)
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Bridge internal, firewalled databases to QueryLens AI without opening inbound firewall ports or public IPs.
          </p>
        </div>

        {/* Register Agent Form */}
        <form onSubmit={handleRegister} className="flex items-center gap-2">
          <input
            type="text"
            required
            placeholder="e.g. HQ-Internal-Agent"
            value={agentName}
            onChange={(e) => setAgentName(e.target.value)}
            className="bg-slate-50 border border-slate-300 rounded-lg px-3 py-1.5 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
          <button
            type="submit"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold rounded-lg shadow-xs transition shrink-0"
          >
            <Plus className="w-4 h-4" /> Register Agent
          </button>
        </form>
      </div>

      {/* Newly Registered Token Banner */}
      {registeredToken && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2 text-emerald-800 text-xs font-bold">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Agent Registered Successfully! Copy the authentication token below:</span>
            </div>
            <button
              onClick={() => copyToken(registeredToken)}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-white border border-emerald-300 text-emerald-700 text-xs font-semibold hover:bg-emerald-100 transition"
            >
              {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied' : 'Copy Token'}</span>
            </button>
          </div>
          <p className="font-mono text-xs bg-white p-2.5 rounded border border-emerald-200 text-slate-800 break-all select-all">
            {registeredToken}
          </p>
          <p className="text-[11px] text-emerald-700 mt-2">
            Add this token to your agent's <code className="font-mono font-semibold">.env</code> file under <code className="font-mono font-semibold">AGENT_TOKEN=...</code>
          </p>
        </div>
      )}

      {/* Architecture Card */}
      <div className="bg-slate-900 text-slate-200 rounded-xl p-5 shadow-xs">
        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
          <Shield className="w-4 h-4 text-brand-400" /> Secure Outbound Agent Architecture
        </h4>
        <p className="text-xs text-slate-300 leading-relaxed mb-3">
          The QueryLens Connector Agent connects outbound via encrypted WebSockets to QueryLens Cloud. Your database remains 100% inside your private VPC. Incoming commands are strictly checked by on-premise local policy for read-only SELECT validation.
        </p>
        <div className="bg-slate-950 p-3 rounded-lg font-mono text-[11px] text-emerald-400 flex items-center justify-between overflow-x-auto">
          <code>cd connector-agent &amp;&amp; python -m app.main</code>
          <button
            onClick={() => copyToken('cd connector-agent && python -m app.main')}
            className="text-slate-400 hover:text-white px-2 py-0.5"
            title="Copy Command"
          >
            <Copy className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Agents Table */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
        <div className="p-4 bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-700">
          Configured Agents ({agents.length})
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100 text-slate-600 font-semibold border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-4">Agent Name</th>
                <th className="py-2.5 px-4">Status</th>
                <th className="py-2.5 px-4">Remote IP</th>
                <th className="py-2.5 px-4">Last Heartbeat</th>
                <th className="py-2.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-sans">
              {agents.map((a) => (
                <tr key={a.id} className="hover:bg-slate-50">
                  <td className="py-3 px-4 font-semibold text-slate-800">
                    <div className="flex items-center gap-2">
                      <Radio className="w-3.5 h-3.5 text-slate-400" />
                      <span>{a.name}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    {a.status === 'online' ? (
                      <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                        <CheckCircle2 className="w-3 h-3" /> Online
                      </span>
                    ) : a.status === 'revoked' ? (
                      <span className="text-[11px] font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full border border-slate-200">
                        Revoked
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full border border-slate-200">
                        <AlertCircle className="w-3 h-3" /> Offline
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4 font-mono text-slate-500">{a.ip_address || '—'}</td>
                  <td className="py-3 px-4 text-slate-500">
                    {a.last_heartbeat ? new Date(a.last_heartbeat).toLocaleString() : 'Never'}
                  </td>
                  <td className="py-3 px-4 text-right">
                    {!a.is_revoked && (
                      <button
                        onClick={() => handleRevoke(a.id)}
                        className="text-rose-600 hover:text-rose-800 font-semibold"
                      >
                        Revoke
                      </button>
                    )}
                  </td>
                </tr>
              ))}

              {agents.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-400">
                    No on-premise agents registered yet. Register an agent above to bridge internal databases.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
