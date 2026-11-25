import React from 'react';
import { 
  Sparkles, 
  Database, 
  Terminal, 
  GitBranch, 
  Clock, 
  BarChart3, 
  Users, 
  ShieldCheck, 
  Settings as SettingsIcon, 
  Radio, 
  Layers,
  LogOut
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const Sidebar = ({ activeTab, onSelectTab }) => {
  const { user, logout } = useAuth();

  const navItems = [
    { id: 'overview', label: 'Overview', icon: Layers },
    { id: 'workspace', label: 'AI Query Workspace', icon: Sparkles, badge: 'AI' },
    { id: 'connections', label: 'Database Connections', icon: Database },
    { id: 'schema', label: 'Schema Explorer', icon: GitBranch },
    { id: 'history', label: 'Query History', icon: Clock },
    { id: 'analytics', label: 'Visualizations', icon: BarChart3 },
    { id: 'agents', label: 'Connector Agents', icon: Radio },
    { id: 'team', label: 'Team & Access', icon: Users },
    { id: 'audit', label: 'Audit Logs', icon: ShieldCheck },
    { id: 'settings', label: 'Settings', icon: SettingsIcon },
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col h-screen select-none shrink-0">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-100 flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-brand-400 flex items-center justify-center text-white shadow-sm shadow-brand-500/20">
          <Sparkles className="w-5 h-5" />
        </div>
        <div>
          <h1 className="font-bold text-slate-900 tracking-tight text-base leading-none">
            QueryLens<span className="text-brand-600">.AI</span>
          </h1>
          <p className="text-[11px] text-slate-400 font-medium mt-1">Multi-DB Intelligence</p>
        </div>
      </div>

      {/* Organization Badge */}
      <div className="px-4 py-3 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
        <div className="truncate">
          <p className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Organization</p>
          <p className="text-xs font-semibold text-slate-800 truncate">{user?.organization_name || 'My Business'}</p>
        </div>
        <span className="text-[10px] font-semibold bg-brand-50 text-brand-700 px-2 py-0.5 rounded border border-brand-200">
          Enterprise
        </span>
      </div>

      {/* Nav List */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? 'bg-brand-50 text-brand-700 font-semibold shadow-xs'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 ${isActive ? 'text-brand-600' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className="text-[10px] font-bold bg-brand-600 text-white px-1.5 py-0.2 rounded-full uppercase">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* User Footer */}
      <div className="p-3 border-t border-slate-100 bg-slate-50/50">
        <div className="flex items-center justify-between p-2 rounded-lg bg-white border border-slate-200/80 shadow-xs">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center font-bold text-slate-600 text-xs shrink-0">
              {user?.full_name ? user.full_name.charAt(0).toUpperCase() : user?.email?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="truncate">
              <p className="text-xs font-semibold text-slate-800 truncate">{user?.full_name || user?.email}</p>
              <p className="text-[11px] text-slate-400 capitalize">{user?.role || 'Member'}</p>
            </div>
          </div>
          <button
            onClick={logout}
            title="Log Out"
            className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
};
