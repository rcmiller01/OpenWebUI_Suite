import React, { useEffect, useState } from "react";

type Project = { id: string; name: string; created_at: number };

interface ProjectsSidebarProps {
  onProjectSelect?: (projectId: string) => void;
  currentProjectId?: string;
}

export default function ProjectsSidebar({ 
  onProjectSelect, 
  currentProjectId 
}: ProjectsSidebarProps) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    try {
      setLoading(true);
      const r = await fetch("/projects");
      if (r.ok) {
        setProjects(await r.json());
        setError("");
      } else {
        setError("Failed to load projects");
      }
    } catch (err) {
      setError("Network error");
    } finally {
      setLoading(false);
    }
  };

  const create = async () => {
    if (!name.trim()) return;
    try {
      setLoading(true);
      const r = await fetch("/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name.trim() }),
      });
      if (r.ok) {
        setName("");
        await load();
        setError("");
      } else {
        setError("Failed to create project");
      }
    } catch (err) {
      setError("Network error");
    } finally {
      setLoading(false);
    }
  };

  const deleteProject = async (projectId: string) => {
    if (!confirm("Delete this project? This will remove all associated conversations.")) {
      return;
    }
    try {
      setLoading(true);
      const r = await fetch(`/projects/${projectId}`, {
        method: "DELETE",
      });
      if (r.ok) {
        await load();
        setError("");
      } else {
        setError("Failed to delete project");
      }
    } catch (err) {
      setError("Network error");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      create();
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <aside className="w-64 bg-gray-50 border-r border-gray-200 h-full flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-800 mb-3">Projects</h3>
        
        <div className="space-y-2">
          <input
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="New project name..."
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={loading}
          />
          <button
            className="w-full bg-blue-600 text-white px-3 py-2 rounded-md text-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            onClick={create}
            disabled={loading || !name.trim()}
          >
            {loading ? "Adding..." : "Add Project"}
          </button>
        </div>

        {error && (
          <div className="mt-2 text-sm text-red-600 bg-red-50 px-2 py-1 rounded">
            {error}
          </div>
        )}
      </div>

      <div className="flex-1 overflow-auto p-4">
        {loading && projects.length === 0 ? (
          <div className="text-sm text-gray-500">Loading projects...</div>
        ) : projects.length === 0 ? (
          <div className="text-sm text-gray-500">No projects yet. Create one above!</div>
        ) : (
          <ul className="space-y-2">
            {projects.map((project) => (
              <li
                key={project.id}
                className={`group relative p-3 rounded-lg border cursor-pointer transition-colors ${
                  currentProjectId === project.id
                    ? "bg-blue-100 border-blue-300"
                    : "bg-white border-gray-200 hover:bg-gray-50"
                }`}
                onClick={() => onProjectSelect?.(project.id)}
              >
                <div className="pr-6">
                  <div className="font-medium text-sm text-gray-900 truncate">
                    {project.name}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {new Date(project.created_at * 1000).toLocaleDateString()}
                  </div>
                </div>
                
                <button
                  className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-600 transition-opacity"
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteProject(project.id);
                  }}
                  title="Delete project"
                  disabled={loading}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="p-4 border-t border-gray-200 text-xs text-gray-500">
        {projects.length} project{projects.length !== 1 ? 's' : ''}
      </div>
    </aside>
  );
}
