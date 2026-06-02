'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Plus, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ToolCard } from '@/components/tools/tool-card';
import { LoadingSpinner } from '@/components/shared/loading-spinner';
import { useTools } from '@/hooks/useTools';
import { toast } from '@/hooks/useToast';

export default function ToolsPage() {
  const { tools, isLoading, error, deleteTool } = useTools();
  const [search, setSearch] = useState('');

  const filteredTools = tools.filter(
    (tool) =>
      tool.name.toLowerCase().includes(search.toLowerCase()) ||
      tool.description?.toLowerCase().includes(search.toLowerCase())
  );

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this tool?')) return;
    try {
      await deleteTool(id);
      toast({ title: 'Tool deleted', variant: 'success' });
    } catch {
      toast({ title: 'Failed to delete tool', variant: 'destructive' });
    }
  };

  if (isLoading) {
    return <LoadingSpinner message="Loading your tools..." className="py-20" />;
  }

  if (error) {
    return (
      <div className="text-center py-20">
        <p className="text-destructive mb-4">{error}</p>
        <Button variant="outline" onClick={() => window.location.reload()}>
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Tools</h1>
          <p className="text-muted-foreground">Manage your internal tools and dashboards.</p>
        </div>
        <Button asChild>
          <Link href="/tools/new">
            <Plus className="h-4 w-4 mr-2" />
            New Tool
          </Link>
        </Button>
      </div>

      {/* Search */}
      <div className="mb-6">
        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search tools..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {/* Tools Grid */}
      {filteredTools.length === 0 ? (
        <div className="text-center py-20">
          {tools.length === 0 ? (
            <>
              <h2 className="text-lg font-semibold mb-2">No tools yet</h2>
              <p className="text-muted-foreground mb-4">
                Create your first tool by describing what you need.
              </p>
              <Button asChild>
                <Link href="/tools/new">
                  <Plus className="h-4 w-4 mr-2" />
                  Create Your First Tool
                </Link>
              </Button>
            </>
          ) : (
            <p className="text-muted-foreground">No tools match your search.</p>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredTools.map((tool) => (
            <ToolCard key={tool.id} tool={tool} onDelete={handleDelete} />
          ))}
        </div>
      )}
    </div>
  );
}
