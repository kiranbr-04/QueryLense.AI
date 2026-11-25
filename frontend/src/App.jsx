import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { DatabaseProvider } from './context/DatabaseContext';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Overview } from './pages/Overview';
import { QueryWorkspace } from './pages/QueryWorkspace';
import { Connections } from './pages/Connections';
import { SchemaExplorer } from './pages/SchemaExplorer';
import { QueryHistory } from './pages/QueryHistory';
import { Analytics } from './pages/Analytics';
import { AgentsView } from './pages/AgentsView';
import { TeamManagement } from './pages/TeamManagement';
import { AuditLogs } from './pages/AuditLogs';
import { Settings } from './pages/Settings';

const DashboardContent = () => {
  const { user, loading } = useAuth();
  const [authView, setAuthView] = useState('login'); // 'login' | 'register'
  const [activeTab, setActiveTab] = useState('overview');
  const [workspaceParams, setWorkspaceParams] = useState({ prompt: '', sql: '' });

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-3 border-brand-600 border-t-transparent rounded-full animate-spin" />
          <p className="text-xs font-semibold text-slate-500">Loading QueryLens AI...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return authView === 'login' ? (
      <Login onSwitchToRegister={() => setAuthView('register')} />
    ) : (
      <Register onSwitchToLogin={() => setAuthView('login')} />
    );
  }

  const navigateTo = (tabId, params = {}) => {
    if (params.prompt || params.sql) {
      setWorkspaceParams(params);
    }
    setActiveTab(tabId);
  };

  return (
    <DatabaseProvider>
      <div className="flex h-screen bg-slate-50 overflow-hidden">
        {/* Navigation Sidebar */}
        <Sidebar activeTab={activeTab} onSelectTab={(tab) => navigateTo(tab)} />

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
          <Header onOpenAddConnection={() => setActiveTab('connections')} />

          <main className="flex-1 overflow-y-auto p-6">
            {activeTab === 'overview' && <Overview onNavigate={navigateTo} />}
            {activeTab === 'workspace' && (
              <QueryWorkspace
                initialPrompt={workspaceParams.prompt}
                initialSql={workspaceParams.sql}
              />
            )}
            {activeTab === 'connections' && <Connections />}
            {activeTab === 'schema' && <SchemaExplorer />}
            {activeTab === 'history' && <QueryHistory onReplay={navigateTo} />}
            {activeTab === 'analytics' && <Analytics />}
            {activeTab === 'agents' && <AgentsView />}
            {activeTab === 'team' && <TeamManagement />}
            {activeTab === 'audit' && <AuditLogs />}
            {activeTab === 'settings' && <Settings />}
          </main>
        </div>
      </div>
    </DatabaseProvider>
  );
};

export default function App() {
  return (
    <AuthProvider>
      <DashboardContent />
    </AuthProvider>
  );
}
