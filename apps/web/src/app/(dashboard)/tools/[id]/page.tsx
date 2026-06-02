"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ChatPanel } from "@/components/tools/chat-panel";
import { SandboxIframe } from "@/components/sandbox/sandbox-iframe";
import { SandboxBridge } from "@/components/sandbox/sandbox-bridge";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { api } from "@/lib/api";
import { useEditorStore } from "@/stores/editorStore";
import type { Tool } from "@/types";

export default function ToolEditorPage() {
  const params = useParams();
  const toolId = params.id as string;
  const [loading, setLoading] = useState(true);
  const { tool, setTool, spec, updateSpec } = useEditorStore();

  useEffect(() => {
    const loadTool = async () => {
      try {
        const response = await api.get(`/tools/${toolId}`);
        const toolData = response.data.tool as Tool;
        setTool(toolData);
        updateSpec(toolData.spec);
      } catch (error) {
        console.error("Failed to load tool:", error);
      } finally {
        setLoading(false);
      }
    };
    loadTool();
  }, [toolId, setTool, updateSpec]);

  if (loading) return <LoadingSpinner message="Loading tool..." />;
  if (!tool) return <div className="p-8 text-center text-gray-500">Tool not found</div>;

  return (
    <div className="flex h-[calc(100vh-4rem)] gap-4">
      <div className="w-1/3 min-w-[320px] border-r pr-4 overflow-y-auto">
        <ChatPanel toolId={toolId} />
      </div>
      <div className="flex-1 overflow-hidden rounded-lg border bg-white">
        <SandboxBridge toolId={toolId}>
          <SandboxIframe spec={spec} />
        </SandboxBridge>
      </div>
    </div>
  );
}
