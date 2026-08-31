'use client';
import { useEffect, useState, useCallback } from 'react';
import { apiGet } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useParams } from 'next/navigation';
import { GitBranch, ChevronRight, ChevronDown, Network } from 'lucide-react';

interface GraphNode {
  id: string;
  label: string;
  node_type: string;
  properties: Record<string, unknown> | null;
  temporal_status: string;
}

interface GraphEdge {
  id: string;
  source_node_id: string;
  target_node_id: string;
  relationship_type: string;
  properties: Record<string, unknown> | null;
  confidence: number;
}

interface GraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export default function GraphPage() {
  const { user } = useAuth();
  const params = useParams();
  const projectId = params.id as string;
  const [data, setData] = useState<GraphResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [showHistorical, setShowHistorical] = useState(false);

  const loadData = useCallback(async () => {
    if (!user) return;
    try {
      const url = `/api/v1/ingest/graph?project_id=${encodeURIComponent(projectId)}&include_historical=${showHistorical}`;
      const result = await apiGet<GraphResponse>(url);
      setData(result);
    } catch {}
    finally { setLoading(false); }
  }, [user, projectId, showHistorical]);

  useEffect(() => { loadData(); }, [loadData]);

  if (loading) return <div className="flex items-center justify-center h-full"><div className="text-sm text-gray-500">Loading…</div></div>;

  const nodes = data?.nodes || [];
  const edges = data?.edges || [];
  const nodeMap = new Map(nodes.map(n => [n.id, n]));

  // Build adjacency: node_id -> [{ edge, neighbor }]
  const adjacency = new Map<string, { edge: GraphEdge; neighbor: GraphNode }[]>();
  for (const edge of edges) {
    const source = nodeMap.get(edge.source_node_id);
    const target = nodeMap.get(edge.target_node_id);
    if (source) {
      const list = adjacency.get(source.id) || [];
      list.push({ edge, neighbor: target! });
      adjacency.set(source.id, list);
    }
  }

  return (
    <div className="max-w-5xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold">Knowledge Graph</h1>
          <p className="text-sm text-gray-500">{nodes.length} nodes, {edges.length} relationships</p>
        </div>
        <label className="flex items-center gap-2 text-sm text-gray-400">
          <input type="checkbox" checked={showHistorical} onChange={(e) => setShowHistorical(e.target.checked)} className="rounded border-[var(--border)]" />
          Include historical
        </label>
      </div>

      {nodes.length === 0 ? (
        <div className="text-center py-20">
          <Network size={40} className="mx-auto text-gray-600 mb-3" />
          <p className="text-sm text-gray-500">No graph data yet. Ingest conversations to build the knowledge graph.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Node list */}
          <div className="lg:col-span-2 space-y-2">
            {nodes.map((node) => {
              const neighbors = adjacency.get(node.id) || [];
              const isSelected = selectedNode?.id === node.id;
              return (
                <div key={node.id}
                  onClick={() => setSelectedNode(node)}
                  className={`bg-[var(--bg-secondary)] border rounded-lg p-3 cursor-pointer transition-colors ${isSelected ? 'border-[var(--accent)]' : 'border-[var(--border)] hover:border-[var(--accent)]/30'}`}>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-[var(--accent)] shrink-0" />
                    <p className="text-sm font-medium flex-1 truncate">{node.label}</p>
                    <span className="text-xs text-gray-500">{node.node_type}</span>
                    {node.temporal_status !== 'current' && (
                      <span className="text-xs text-yellow-400">{node.temporal_status}</span>
                    )}
                  </div>
                  {isSelected && neighbors.length > 0 && (
                    <div className="mt-3 ml-4 space-y-1.5 border-l border-[var(--border)] pl-3">
                      {neighbors.map(({ edge, neighbor }) => (
                        <div key={edge.id} className="flex items-center gap-2 text-xs">
                          <span className="text-gray-500">{edge.relationship_type}</span>
                          <ChevronRight size={10} className="text-gray-600" />
                          <span className="text-gray-400">{neighbor?.label || 'unknown'}</span>
                          <span className="text-gray-600">{edge.confidence ? `${Math.round(edge.confidence * 100)}%` : ''}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Detail panel */}
          <div className="space-y-3">
            {selectedNode ? (
              <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
                <h3 className="text-sm font-medium mb-3">{selectedNode.label}</h3>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Type</span>
                    <span className="text-gray-400">{selectedNode.node_type}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Status</span>
                    <span className={selectedNode.temporal_status === 'current' ? 'text-green-400' : 'text-yellow-400'}>{selectedNode.temporal_status}</span>
                  </div>
                  {selectedNode.properties && Object.keys(selectedNode.properties).length > 0 && (
                    <div>
                      <span className="text-gray-500 block mb-1">Properties</span>
                      <pre className="bg-[var(--bg-tertiary)] rounded p-2 text-xs text-gray-400 overflow-auto max-h-40">
                        {JSON.stringify(selectedNode.properties, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-xs text-gray-500 text-center py-8">Click a node to see its relationships.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
