import React, { useEffect } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { useAppStore } from './stores/appStore';

import { Dashboard } from './pages/Dashboard';
import { Projects } from './pages/Projects';
import { LiveMonitoring } from './pages/LiveMonitoring';
import { Findings } from './pages/Findings';
import { Investigations } from './pages/Investigations';
import { Optimization } from './pages/Optimization';
import { ProposedFixes } from './pages/ProposedFixes';
import { Reports } from './pages/Reports';
import { ModelInsights } from './pages/ModelInsights';
import { Settings } from './pages/Settings';

export const App: React.FC = () => {
  const { activeTab, fetchInitialData } = useAppStore();

  useEffect(() => {
    fetchInitialData();
  }, [fetchInitialData]);

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'projects':
        return <Projects />;
      case 'monitoring':
        return <LiveMonitoring />;
      case 'findings':
        return <Findings />;
      case 'investigations':
        return <Investigations />;
      case 'optimization':
        return <Optimization />;
      case 'fixes':
        return <ProposedFixes />;
      case 'reports':
        return <Reports />;
      case 'insights':
        return <ModelInsights />;
      case 'settings':
        return <Settings />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#0B1020] text-gray-100 antialiased font-sans">
      {/* Sidebar Navigation */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        <Header />
        <main className="flex-1 p-8 overflow-y-auto bg-[#0B1020]">
          <div className="max-w-7xl mx-auto">{renderContent()}</div>
        </main>
      </div>
    </div>
  );
};

export default App;
