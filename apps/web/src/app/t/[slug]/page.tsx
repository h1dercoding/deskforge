"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { SandboxIframe } from "@/components/sandbox/sandbox-iframe";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { api } from "@/lib/api";
import type { Tool } from "@/types";

export default function PublicToolPage() {
  const params = useParams();
  const slug = params.slug as string;
  const [tool, setTool] = useState<Tool | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get(`/sharing/${slug}`)
      .then((res) => setTool(res.data.tool))
      .catch((e) => setError(e.response?.data?.error?.message || "Tool not found"))
      .finally(() => setLoading(false));
  }, [slug]);

  if (loading) return <LoadingSpinner message="Loading tool..." />;
  if (error) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-gray-900">Tool Not Found</h1>
        <p className="mt-2 text-gray-500">{error}</p>
        <a href="/" className="mt-4 inline-block text-blue-600 hover:underline">Go to DeskForge</a>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-3 flex items-center justify-between">
        <h1 className="text-lg font-semibold">{tool?.name}</h1>
        <span className="text-xs text-gray-400">Powered by DeskForge</span>
      </header>
      <main className="p-6">
        <div className="max-w-7xl mx-auto bg-white rounded-lg shadow-sm border overflow-hidden">
          <SandboxIframe spec={tool?.spec} />
        </div>
      </main>
    </div>
  );
}
