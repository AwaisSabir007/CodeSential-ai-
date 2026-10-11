import { create } from 'zustand';
import { Project, Finding, ScanRun, Investigation, ProposedPatch, SystemHealth } from '../types';
import { api } from '../services/api';
import { WsEvent, wsClient } from '../services/wsClient';

export type NavigationTab =
  | 'dashboard'
  | 'projects'
  | 'monitoring'
  | 'findings'
  | 'investigations'
  | 'optimization'
  | 'fixes'
  | 'reports'
  | 'insights'
  | 'settings';

interface AppState {
  activeTab: NavigationTab;
  setActiveTab: (tab: NavigationTab) => void;

  projects: Project[];
  activeProject: Project | null;
  setActiveProject: (p: Project | null) => void;

  findings: Finding[];
  selectedFinding: Finding | null;
  setSelectedFinding: (f: Finding | null) => void;

  scans: ScanRun[];
  investigations: Investigation[];
  activeInvestigation: Investigation | null;
  setActiveInvestigation: (inv: Investigation | null) => void;

  patches: ProposedPatch[];
  systemHealth: SystemHealth | null;
  isBackendConnected: boolean;

  liveEvents: WsEvent[];
  wsConnected: boolean;
  initWebSocket: () => void;
  fetchFindings: (projectId: string) => Promise<void>;

  fetchInitialData: () => Promise<void>;
  triggerScan: (projectId: string, level?: number) => Promise<void>;
  startMonitoring: (projectId: string) => Promise<void>;
  stopMonitoring: (projectId: string) => Promise<void>;
  deleteProject: (projectId: string) => Promise<void>;
}

export const useAppStore = create<AppState>((set, get) => ({
  activeTab: 'dashboard',
  setActiveTab: (tab) => set({ activeTab: tab }),

  projects: [],
  activeProject: null,
  setActiveProject: async (p) => {
    set({ activeProject: p });
    if (p) {
      try {
        const [findings, scans, investigations] = await Promise.all([
          api.getFindings(p.id),
          api.getScans(p.id),
          api.getInvestigations(p.id),
        ]);
        set({ findings, scans, investigations });
      } catch (err) {
        console.warn('Failed to load project details', err);
      }
    }
  },

  findings: [],
  selectedFinding: null,
  setSelectedFinding: (f) => set({ selectedFinding: f }),

  scans: [],
  investigations: [],
  activeInvestigation: null,
  setActiveInvestigation: (inv) => set({ activeInvestigation: inv }),

  patches: [],
  systemHealth: null,
  isBackendConnected: false,

  liveEvents: [],
  wsConnected: false,

  fetchFindings: async (projectId: string) => {
    try {
      const findings = await api.getFindings(projectId);
      set({ findings });
    } catch (_) {}
  },

  initWebSocket: () => {
    wsClient.onMessage((event: WsEvent) => {
      if (event.type === 'ws_connected') {
        set({ wsConnected: true });
      } else if (event.type === 'ws_disconnected') {
        set({ wsConnected: false });
      } else {
        set((state) => ({
          liveEvents: [event, ...state.liveEvents].slice(0, 100),
        }));
        if (event.type === 'scan_completed') {
          const { activeProject } = get();
          if (activeProject) {
            get().fetchFindings(activeProject.id);
            api.getScans(activeProject.id).then((scans) => set({ scans })).catch(() => {});
          }
        }
      }
    });
  },

  fetchInitialData: async () => {
    try {
      const health = await api.getHealth();
      set({ systemHealth: health, isBackendConnected: true });

      const projects = await api.getProjects();
      set({
        projects,
        activeProject: projects.length > 0 ? projects[0] : null,
      });

      if (projects.length > 0) {
        const [findings, scans, investigations] = await Promise.all([
          api.getFindings(projects[0].id),
          api.getScans(projects[0].id),
          api.getInvestigations(projects[0].id),
        ]);
        set({ findings, scans, investigations });
      }

      get().initWebSocket();
    } catch (e) {
      console.warn('Backend unavailable, using preview state');
      set({ isBackendConnected: false });
    }
  },

  triggerScan: async (projectId: string, level = 1) => {
    try {
      const scan = await api.triggerScan(projectId, level);
      set((state) => ({ scans: [scan, ...state.scans] }));
      setTimeout(async () => {
        try {
          const [findings, scans] = await Promise.all([
            api.getFindings(projectId),
            api.getScans(projectId),
          ]);
          set({ findings, scans });
        } catch (_) {}
      }, 1500);
      setTimeout(async () => {
        try {
          const [findings, scans] = await Promise.all([
            api.getFindings(projectId),
            api.getScans(projectId),
          ]);
          set({ findings, scans });
        } catch (_) {}
      }, 4000);
    } catch (e) {
      console.error('Scan trigger failed', e);
    }
  },

  startMonitoring: async (projectId: string) => {
    try {
      await api.startMonitoring(projectId);
      set((state) => ({
        projects: state.projects.map((p) =>
          p.id === projectId ? { ...p, is_monitored: true } : p
        ),
      }));
    } catch (e) {
      console.error('Start monitoring failed', e);
    }
  },

  stopMonitoring: async (projectId: string) => {
    try {
      await api.stopMonitoring(projectId);
      set((state) => ({
        projects: state.projects.map((p) =>
          p.id === projectId ? { ...p, is_monitored: false } : p
        ),
      }));
    } catch (e) {
      console.error('Stop monitoring failed', e);
    }
  },

  deleteProject: async (projectId: string) => {
    try {
      await api.deleteProject(projectId);
      set((state) => {
        const remaining = state.projects.filter((p) => p.id !== projectId);
        return {
          projects: remaining,
          activeProject:
            state.activeProject?.id === projectId
              ? remaining.length > 0
                ? remaining[0]
                : null
              : state.activeProject,
        };
      });
      await get().fetchInitialData();
    } catch (e) {
      console.error('Delete project failed', e);
      throw e;
    }
  },
}));
