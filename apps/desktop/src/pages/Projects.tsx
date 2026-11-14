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
          <h1 className="text-xl font-semibold text-gray-900">Monitored Projects</h1>
          <p className="text-sm text-gray-500 mt-0.5">
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
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Add Project
          </button>
        </div>
      </div>

      {/* Projects List */}
      <div className="grid grid-cols-1 gap-5">
        {projects.length === 0 ? (
          <div className="bg-white border border-gray-200 rounded-xl p-12 text-center">
            <FolderSearch className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <h3 className="text-base font-medium text-gray-900">No Projects Configured</h3>
            <p className="text-sm text-gray-500 max-w-sm mx-auto mt-1">
              Add your repository directory to begin real-time code change detection and automated security analysis.
            </p>
          </div>
        ) : (
          projects.map((p) => (
            <div
              key={p.id}
              className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm hover:border-gray-300 transition-colors flex items-center justify-between"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-3">
                  <h3 className="text-sm font-semibold text-gray-900">{p.name}</h3>
                  {p.is_monitored ? (
                    <span className="badge bg-emerald-50 text-emerald-700 border border-emerald-100 flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                      Live Watchdog
                    </span>
                  ) : (
                    <span className="badge bg-gray-100 text-gray-500 border border-gray-200">
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
                  className="p-2 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-700 transition-colors"
                  title="Run Scan"
                >
                  <Play className="w-4 h-4" />
                </button>
                {p.is_monitored ? (
                  <button
                    onClick={() => stopMonitoring(p.id)}
                    className="p-2 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-amber-600 transition-colors"
                    title="Pause Monitoring"
                  >
                    <Pause className="w-4 h-4" />
                  </button>
                ) : (
                  <button
                    onClick={() => startMonitoring(p.id)}
                    className="p-2 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-700 transition-colors"
                    title="Start Monitoring"
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                )}
                <button
                  onClick={() => setProjectToDelete(p)}
                  className="p-2 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-600 transition-colors"
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
        <div className="fixed inset-0 bg-black/20 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="w-full max-w-md bg-white border border-gray-200 rounded-2xl p-6 shadow-xl">
            <h2 className="text-base font-semibold text-gray-900 mb-4">Register New Project</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Project Name</label>
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
                  <label className="block text-xs font-medium text-gray-700">
                    Project Directory Path
                  </label>
                  <button
                    type="button"
                    onClick={handleBrowseFolder}
                    disabled={isBrowsing}
                    className="text-xs text-gray-500 hover:text-gray-900 flex items-center gap-1 font-medium"
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
                  className="btn-primary disabled:opacity-50"
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
        <div className="fixed inset-0 bg-black/20 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="w-full max-w-sm bg-white border border-gray-200 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-red-50 border border-red-100 text-red-600">
                <Trash2 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-gray-900">Remove Project</h3>
                <p className="text-xs text-gray-500">Remove from monitoring &amp; scan queue</p>
              </div>
            </div>

            <div className="p-3 bg-gray-50 rounded-xl border border-gray-100 space-y-1">
              <div className="text-xs font-semibold text-gray-900">{projectToDelete.name}</div>
              <div className="text-[11px] text-gray-500 font-mono truncate">
                {projectToDelete.root_path || projectToDelete.path}
              </div>
            </div>

            <p className="text-xs text-gray-600 leading-relaxed">
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
                className="bg-red-600 hover:bg-red-700 text-white text-xs font-semibold rounded-lg px-5 py-2 transition-colors disabled:opacity-50"
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
