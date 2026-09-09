'use client';
import { useEffect, useState, useCallback } from 'react';
import { apiGet } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useParams } from 'next/navigation';
import { GitBranch, ChevronRight, Network, ChevronDown } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorAlert } from '@/components/ui/ErrorAlert';
import { Collapsible } from '@/components/ui/Collapsible';

interface GraphNode {
  id: string;
  label: string;
  node_type: string;
  properties: Record<string, unknown> | null;
  temporal_status: string;
  created_at: string;
}

interface GraphEdge {
  id: string;
  source_node_id: string;
  target_node_id: string;
  relationship_type: string;
  properties: Record<string, unknown> | null;
  temporal_status: string;
  confidence: number;
  created_at: string;
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
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    setError(null);
    try {
      const result = await apiGet<GraphResponse>(`/api/v1/ingest/graph?project_id=${encodeURIComponent(projectId)}`);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load graph');
    } finally { setLoading(false); }
  }, [user, projectId]);

  useEffect(() => { loadData(); }, [loadData]);

  if (!user) {
    return <div className="flex items-center justify-center h-full"><p className="text-sm text-[var(--sv-text-tertiary)]">Sign in to view graph.</p></div>;
  }

  const nodes = data?.nodes || [];
  const edges = data?.edges || [];
  const nodeMap = new Map(nodes.map(n => [n.id, n]));

  const getNeighbors = (nodeId: string) => {
    return edges
      .filter(e => e.source_node_id === nodeId)
      .map(e => ({ edge: e, neighbor: nodeMap.get(e.target_node_id) }))
      .filter((item): item is { edge: GraphEdge; neighbor: GraphNode } => item.neighbor !== undefined);
  };

  const nodeTypeColor = (type: string) => {
    switch (type) {
      case 'concept': return 'info';
      case 'entity': return 'accent';
      case 'decision': return 'warning';
      case 'fact': return 'success';
      default: return 'default';
    }
  };

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-[var(--sv-text-primary)]">Knowledge Graph</h1>
        <p className="text-sm text-[var(--sv-text-tertiary)] mt-1">{nodes.length} nodes, {edges.length} relationships</p>
      </div>

      {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

      {loading && <div className="text-sm text-[var(--sv-text-tertiary)]">Loading…</div>}

      {!loading && nodes.length === 0 && !error && (
        <EmptyState
          icon={<Network size={32} className="text-[var(--sv-text-disabled)]" />}
          title="No graph data yet"
          description="Ingest conversations and extract knowledge to build the graph."
        />
      )}

      {nodes.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Node list */}
          <div className="lg:col-span-2 space-y-2">
            {nodes.map((node) => {
              const neighbors = getNeighbors(node.id);
              const isSelected = selectedNode?.id === node.id;
              return (
                <div key={node.id}
                  onClick={() => setSelectedNode(node)}
                  className={`bg-[var(--sv-bg-raised)] border rounded-lg p-3 cursor-pointer transition-colors ${isSelected ? 'border-[var(--sv-accent)]' : 'border-[var(--sv-border-default)] hover:border-[var(--sv-accent)]/30'}`}>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-[var(--sv-accent)] shrink-0" />
                    <p className="text-sm font-medium text-[var(--sv-text-primary)] flex-1 truncate">{node.label}</p>
                    <Badge category="status" value={node.node_type} size="sm" />
                    {node.temporal_status !== 'current' && (
                      <Badge category="temporal" value={{ current: 'ACTIVE', superseded: 'SUPERSEDED', archived: 'ARCHIVED' }[node.temporal_status.toLowerCase()] ?? node.temporal_status.toUpperCase()} size="sm" />
                    )}
                  </div>
                  {isSelected && neighbors.length > 0 && (
                    <div className="mt-3 ml-4 space-y-1.5 border-l border-[var(--sv-border-default)] pl-3">
                      {neighbors.map(({ edge, neighbor }) => (
                        <div key={edge.id} className="flex items-center gap-2 text-xs">
                          <ChevronRight size={10} className="text-[var(--sv-text-disabled)]" />
                          <span className="text-[var(--sv-text-tertiary)]">{edge.relationship_type}</span>
                          <span className="text-[var(--sv-text-disabled)]">→</span>
                          <span className="text-[var(--sv-text-secondary)]">{neighbor.label}</span>
                          <span className="text-[var(--sv-text-disabled)]">{Math.round(edge.confidence * 100)}%</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Detail panel */}
          <div>
            {selectedNode ? (
              <div className="bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] rounded-lg p-4">
                <h3 className="text-sm font-medium text-[var(--sv-text-primary)] mb-3">{selectedNode.label}</h3>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-[var(--sv-text-tertiary)]">Type</span>
                    <span className="text-[var(--sv-text-secondary)]">{selectedNode.node_type}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[var(--sv-text-tertiary)]">Status</span>
                    <Badge category="temporal" value={{ current: 'ACTIVE', superseded: 'SUPERSEDED', archived: 'ARCHIVED' }[selectedNode.temporal_status.toLowerCase()] ?? selectedNode.temporal_status.toUpperCase()} size="sm" />
                  </div>
                  {selectedNode.properties && Object.keys(selectedNode.properties).length > 0 && (
                    <Collapsible label="Properties" defaultOpen={false}>
                      <pre className="bg-[var(--sv-bg-input)] rounded p-2 text-[10px] text-[var(--sv-text-secondary)] overflow-auto max-h-40 font-mono">
                        {JSON.stringify(selectedNode.properties, null, 2)}
                      </pre>
                    </Collapsible>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-xs text-[var(--sv-text-tertiary)] text-center py-8">Click a node to see its relationships.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
