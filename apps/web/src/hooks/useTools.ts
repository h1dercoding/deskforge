'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import type { Tool, ApiResponse, PaginationMeta } from '@/types';

interface UseToolsOptions {
  status?: string;
  page?: number;
  perPage?: number;
  category?: string;
  tags?: string;
}

export function useTools(options: UseToolsOptions = {}) {
  const [tools, setTools] = useState<Tool[]>([]);
  const [meta, setMeta] = useState<PaginationMeta | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTools = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (options.status) params.status = options.status;
      if (options.page) params.page = String(options.page);
      if (options.perPage) params.per_page = String(options.perPage);
      if (options.category) params.category = options.category;
      if (options.tags) params.tags = options.tags;

      const response = await api.get<ApiResponse<{ tools: Tool[] }>>('/tools', { params });
      setTools(response.data.tools);
      if (response.meta) setMeta(response.meta);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to fetch tools';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [options.status, options.page, options.perPage, options.category, options.tags]);

  useEffect(() => {
    fetchTools();
  }, [fetchTools]);

  const createTool = useCallback(
    async (data: { name?: string; prompt: string; spec?: unknown; data_source_id?: string }) => {
      const response = await api.post<ApiResponse<{ tool: Tool }>>('/tools', data);
      setTools((prev) => [response.data.tool, ...prev]);
      return response.data.tool;
    },
    []
  );

  const deleteTool = useCallback(async (id: string) => {
    await api.delete(`/tools/${id}`);
    setTools((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return {
    tools,
    meta,
    isLoading,
    error,
    fetchTools,
    createTool,
    deleteTool,
  };
}

export function useTool(id: string) {
  const [tool, setTool] = useState<Tool | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTool = useCallback(async () => {
    if (!id) return;
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.get<ApiResponse<{ tool: Tool }>>(`/tools/${id}`);
      setTool(response.data.tool);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to fetch tool';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchTool();
  }, [fetchTool]);

  const updateTool = useCallback(
    async (data: Partial<Pick<Tool, 'name' | 'description' | 'theme' | 'visibility'>>) => {
      const response = await api.patch<ApiResponse<{ tool: Tool }>>(`/tools/${id}`, data);
      setTool(response.data.tool);
      return response.data.tool;
    },
    [id]
  );

  return {
    tool,
    isLoading,
    error,
    fetchTool,
    updateTool,
    setTool,
  };
}
