'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Plus, Search, Tag, FolderOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ToolCard } from '@/components/tools/tool-card';
import { LoadingSpinner } from '@/components/shared/loading-spinner';
import { useTools } from '@/hooks/useTools';
import { toast } from '@/hooks/useToast';
import { api } from '@/lib/api';
import { cn } from '@/lib/utils';

export default function ToolsPage() {
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [categories, setCategories] = useState<string[]>([]);

  const { tools, isLoading, error, deleteTool } = useTools({
    category: selectedCategory || undefined,
    tags: selectedTags.length > 0 ? selectedTags.join(',') : undefined,
  });

  useEffect(() => {
    api.get<{ data: { categories: string[] } }>('/tools/categories')
      .then((res) => setCategories(res.data.categories || []))
      .catch(() => {});
  }, [tools]);

  // Collect all unique tags from tools
  const allTags = Array.from(
    new Set(tools.flatMap((t) => t.tags || []))
  ).sort();

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

  const toggleTag = (tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  };

  if (isLoading && !selectedCategory && selectedTags.length === 0) {
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
    <div className="flex gap-6">
      {/* Category Sidebar */}
      <aside className="hidden lg:block w-56 flex-shrink-0">
        <div className="sticky top-4 space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-2 flex items-center gap-2">
              <FolderOpen className="h-4 w-4" />
              Categories
            </h3>
            <div className="space-y-1">
              <button
                onClick={() => setSelectedCategory(null)}
                className={cn(
                  'w-full text-left px-3 py-1.5 rounded-md text-sm transition-colors',
                  !selectedCategory
                    ? 'bg-primary/10 text-primary font-medium'
                    : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                )}
              >
                All Tools
              </button>
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat === selectedCategory ? null : cat)}
                  className={cn(
                    'w-full text-left px-3 py-1.5 rounded-md text-sm transition-colors',
                    selectedCategory === cat
                      ? 'bg-primary/10 text-primary font-medium'
                      : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                  )}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          {allTags.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-muted-foreground mb-2 flex items-center gap-2">
                <Tag className="h-4 w-4" />
                Tags
              </h3>
              <div className="flex flex-wrap gap-1.5">
                {allTags.map((tag) => (
                  <Badge
                    key={tag}
                    variant={selectedTags.includes(tag) ? 'default' : 'outline'}
                    className="cursor-pointer text-xs"
                    onClick={() => toggleTag(tag)}
                  >
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 min-w-0">
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
              <p className="text-muted-foreground">No tools match your filters.</p>
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
    </div>
  );
}
