import {
  Project,
  Finding,
  ScanRun,
  Investigation,
  ProposedPatch,
  SystemHealth,
  ModelMetrics,
} from '../types';

const API_BASE = 'http://127.0.0.1:8765/api/v1';

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers || {}),
      },
    });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`HTTP ${res.status}: ${errText}`);
    }
    return await res.json();
  } catch (err) {
    console.warn(`API Error [${endpoint}]:`, err);
    throw err;
  }
}

export const api = {
  // System Health
  async getHealth(): Promise<SystemHealth> {
    return fetchJson<SystemHealth>('/system/health');
  },

  async getScanners(): Promise<any[]> {
    return fetchJson<any[]>('/system/scanners');
  },

  // Projects
  async getProjects(): Promise<Project[]> {
    return fetchJson<Project[]>('/projects');
  },

  async createProject(name: string, root_path: string): Promise<Project> {
    return fetchJson<Project>('/projects', {
      method: 'POST',
      body: JSON.stringify({ name, path: root_path, root_path }),
    });
  },

  async browseFolder(): Promise<{ path: string; name: string; status: string }> {
    return fetchJson<{ path: string; name: string; status: string }>('/projects/browse-folder', {
      method: 'POST',
    });
  },

  async deleteProject(id: string): Promise<void> {
    await fetchJson(`/projects/${id}`, { method: 'DELETE' });
  },

  async startMonitoring(id: string): Promise<void> {
    await fetchJson(`/projects/${id}/monitor/start`, { method: 'POST' });
  },

  async stopMonitoring(id: string): Promise<void> {
    await fetchJson(`/projects/${id}/monitor/stop`, { method: 'POST' });
  },

  // Scans
  async getScans(project_id?: string): Promise<ScanRun[]> {
    const query = project_id ? `?project_id=${project_id}` : '';
    return fetchJson<ScanRun[]>(`/scans${query}`);
  },

  async triggerScan(project_id: string, scan_level = 1): Promise<ScanRun> {
    return fetchJson<ScanRun>('/scans', {
      method: 'POST',
      body: JSON.stringify({ project_id, scan_level }),
    });
  },

  // Findings
  async getFindings(project_id?: string): Promise<Finding[]> {
    const query = project_id ? `?project_id=${project_id}` : '';
    return fetchJson<Finding[]>(`/findings${query}`);
  },

  async updateFindingStatus(id: string, status: string): Promise<Finding> {
    return fetchJson<Finding>(`/findings/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  },

  // Investigations
  async triggerInvestigation(data: any): Promise<Investigation> {
    return fetchJson<Investigation>('/investigations', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async getInvestigations(project_id?: string): Promise<Investigation[]> {
    const query = project_id ? `?project_id=${project_id}` : '';
    return fetchJson<Investigation[]>(`/investigations${query}`);
  },

  // Patches
  async getPatches(): Promise<any[]> {
    return fetchJson<any[]>('/patches');
  },

  async generatePatch(data: any): Promise<ProposedPatch> {
    return fetchJson<ProposedPatch>('/patches/generate', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async approvePatch(patch_id: string, apply_immediately = true): Promise<any> {
    return fetchJson(`/patches/${patch_id}/approve?apply_immediately=${apply_immediately}`, {
      method: 'POST',
    });
  },

  async rollbackPatch(patch_id: string): Promise<any> {
    return fetchJson(`/patches/${patch_id}/rollback`, {
      method: 'POST',
    });
  },

  async rejectPatch(patch_id: string, reason?: string): Promise<any> {
    return fetchJson(`/patches/${patch_id}/reject`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  },

  // Optimization & Algorithmic Complexity
  async getProjectOptimization(project_id: string): Promise<any> {
    return fetchJson(`/projects/${project_id}/optimization`);
  },

  // Neural Models
  async getModelStatus(): Promise<any> {
    return fetchJson('/models/status');
  },

  async getModelMetrics(): Promise<ModelMetrics> {
    return fetchJson<ModelMetrics>('/models/metrics');
  },

  async runInference(code: string): Promise<any> {
    return fetchJson('/models/inference', {
      method: 'POST',
      body: JSON.stringify({ code }),
    });
  },

  // Providers & Settings
  async getProviders(): Promise<any> {
    return fetchJson('/providers');
  },

  async getProvidersStatus(): Promise<any> {
    return fetchJson('/providers/status');
  },

  async updateProviderSettings(data: any): Promise<any> {
    return fetchJson('/providers/settings', {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },
};
