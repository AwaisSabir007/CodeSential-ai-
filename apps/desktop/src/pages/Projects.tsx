import React, { useState } from 'react';
import { FolderGit2, Plus, Play, Pause, Trash2, FolderSearch, Eye } from 'lucide-react';
import { useAppStore } from '../stores/appStore';
import { api } from '../services/api';

export const Projects: React.FC = () => {
  const {
    projects,
    startMonitoring,
    stopMonitoring,
    triggerScan,
    fetchInitialData,
    setActiveProject,
    deleteProject,
  } = useAppStore();
  const [showAddModal, setShowAddModal] = useState(false);
  const [projectToDelete, setProjectToDelete] = useState<any | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [name, setName] = useState('');
  const [rootPath, setRootPath] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isBrowsing, setIsBrowsing] = useState(false);

  const handleBrowseFolder = async () => {
    setIsBrowsing(true);
    try {
      const res = await api.browseFolder();
      if (res && res.status === 'selected' && res.path) {
        setRootPath(res.path);
        if (!name || name === '') {
          setName(res.name || 'my-project');
        }
        setShowAddModal(true);
      }
    } catch (err: any) {
      console.warn('Browse folder failed:', err);
    } finally {
      setIsBrowsing(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !rootPath) return;
    setIsSubmitting(true);
    try {
      const created = await api.createProject(name, rootPath);
      await fetchInitialData();
      if (created) {
        setActiveProject(created);
      }
      setShowAddModal(false);
      setName('');
      setRootPath('');
    } catch (err: any) {
      alert(`Error creating project: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const confirmDelete = async () => {
    if (!projectToDelete) return;
    setIsDeleting(true);
    try {
      await deleteProject(projectToDelete.id);
      setProjectToDelete(null);
    } catch (err: any) {
      alert(`Error deleting project: ${err.message}`);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white tracking-tight">Monitored Projects</h1>
          <p className="text-sm text-gray-400 font-light mt-0.5">
            Register local repositories to enable filesystem watching, debouncing, and automated scanning.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleBrowseFolder}
            disabled={isBrowsing}
            className="btn-secondary flex items-center gap-2 disabled:opacity-50"
          >
            <FolderSearch className="w-4 h-4" />
            {isBrowsing ? 'Selecting Folder...' : 'Open Folder to Monitor'}
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="btn-primary flex items-center gap-2 shadow-glow"
          >
            <Plus className="w-4 h-4" />
            Add Project
          </button>
        </div>
      </div>

      {/* Projects List */}
      <div className="grid grid-cols-1 gap-5">
        {projects.length === 0 ? (
          <div className="p-12 text-center rounded-2xl bg-[#111827] border border-white/[0.08]">
            <FolderSearch className="w-12 h-12 text-gray-600 mx-auto mb-3" />
            <h3 className="text-base font-medium text-white">No Projects Configured</h3>
            <p className="text-sm text-gray-500 max-w-sm mx-auto mt-1">
              Add your repository directory to begin real-time code change detection and automated security analysis.
            </p>
          </div>
        ) : (
          projects.map((p) => (
            <div
              key={p.id}
              className="p-6 rounded-2xl bg-[#111827] border border-white/[0.08] flex items-center justify-between glow-card hover:scale-[1.01] transition-all duration-200 backdrop-blur-sm"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-3">
                  <h3 className="text-sm font-semibold text-white">{p.name}</h3>
                  {p.is_monitored ? (
                    <span className="badge flex items-center gap-1.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                      Live Watchdog
                    </span>
                  ) : (
                    <span className="badge bg-gray-800 text-gray-400 border border-white/5">
                      Paused
                    </span>
                  )}
                </div>
                <div className="text-xs text-gray-400 font-mono">{p.root_path}</div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => triggerScan(p.id, 1)}
                  className="p-2 rounded-full bg-white/[0.05] hover:bg-white/10 text-gray-300 hover:text-white transition-all duration-200"
                  title="Run Scan"
                >
                  <Play className="w-4 h-4" />
                </button>
                {p.is_monitored ? (
                  <button
                    onClick={() => stopMonitoring(p.id)}
                    className="p-2 rounded-full bg-white/[0.05] hover:bg-white/10 text-amber-400 transition-all duration-200"
                    title="Pause Monitoring"
                  >
                    <Pause className="w-4 h-4" />
                  </button>
                ) : (
                  <button
                    onClick={() => startMonitoring(p.id)}
                    className="p-2 rounded-full bg-white/[0.05] hover:bg-white/10 text-emerald-400 transition-all duration-200"
                    title="Start Monitoring"
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                )}
                <button
                  onClick={() => setProjectToDelete(p)}
                  className="p-2 rounded-full bg-white/[0.05] hover:bg-red-500/20 text-gray-400 hover:text-red-400 transition-all duration-200"
                  title="Delete Project"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Add Project Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-xl flex items-center justify-center z-50 p-4">
          <div className="w-full max-w-md bg-[#111827] border border-white/10 rounded-3xl p-6 shadow-2xl">
            <h2 className="text-base font-bold text-white mb-4">Register New Project</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">Project Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. backend-service"
                  className="input w-full"
                  required
                />
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-xs font-medium text-gray-300">
                    Project Directory Path
                  </label>
                  <button
                    type="button"
                    onClick={handleBrowseFolder}
                    disabled={isBrowsing}
                    className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-medium"
                  >
                    <FolderSearch className="w-3.5 h-3.5" />
                    {isBrowsing ? 'Selecting...' : 'Select Folder'}
                  </button>
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={rootPath}
                    onChange={(e) => setRootPath(e.target.value)}
                    placeholder="/Users/username/work/project"
                    className="input flex-1 font-mono"
                    required
                  />
                  <button
                    type="button"
                    onClick={handleBrowseFolder}
                    disabled={isBrowsing}
                    className="btn-secondary px-3 py-2"
                  >
                    Browse
                  </button>
                </div>
              </div>
              <div className="flex items-center justify-end gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="btn-primary shadow-glow disabled:opacity-50"
                >
                  Register Project
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {projectToDelete && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-xl flex items-center justify-center z-50 p-4">
          <div className="w-full max-w-sm bg-[#111827] border border-red-500/30 rounded-3xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-400">
                <Trash2 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Remove Project</h3>
                <p className="text-xs text-gray-400">Remove from monitoring & scan queue</p>
              </div>
            </div>

            <div className="p-3 bg-white/[0.03] rounded-2xl border border-white/[0.08] space-y-1">
              <div className="text-xs font-semibold text-white">{projectToDelete.name}</div>
              <div className="text-[11px] text-gray-400 font-mono truncate">
                {projectToDelete.root_path || projectToDelete.path}
              </div>
            </div>

            <p className="text-xs text-gray-300 leading-relaxed">
              Are you sure you want to delete this project? All associated security findings and scan histories will be cleaned.
            </p>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setProjectToDelete(null)}
                disabled={isDeleting}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={confirmDelete}
                disabled={isDeleting}
                className="rounded-full bg-red-600 hover:bg-red-500 text-xs font-semibold text-white px-5 py-2 shadow-glow transition-all duration-200 active:scale-95 disabled:opacity-50"
              >
                {isDeleting ? 'Removing...' : 'Yes, Delete Project'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
