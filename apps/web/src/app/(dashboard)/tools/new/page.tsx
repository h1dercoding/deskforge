"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { PromptInput } from "@/components/tools/prompt-input";
import { TemplateGallery } from "@/components/tools/template-gallery";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select } from "@/components/ui/select";
import { api } from "@/lib/api";
import { useEditorStore } from "@/stores/editorStore";
import type { DataSource } from "@/types";

export default function NewToolPage() {
  const router = useRouter();
  const [isGenerating, setIsGenerating] = useState(false);
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [selectedDataSource, setSelectedDataSource] = useState<string>("");
  const { setTool, updateSpec } = useEditorStore();

  // Fetch data sources for the selector
  useEffect(() => {
    api.get("/datasources").then((res) => {
      const sources = res.data?.sources || [];
      setDataSources(sources);
    }).catch(() => {
      // Silently fail — data source selection is optional
    });
  }, []);

  const handleGenerate = async (prompt: string, templateId?: string) => {
    setIsGenerating(true);
    try {
      const payload: Record<string, unknown> = { prompt };
      if (templateId) payload.template_id = templateId;
      if (selectedDataSource) payload.data_source_id = selectedDataSource;

      const response = await api.post("/generate", payload);
      if (response.data?.tool_id) {
        router.push(`/tools/${response.data.tool_id}`);
      }
    } catch (error) {
      console.error("Generation failed:", error);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Create a New Tool</h1>
        <p className="mt-2 text-gray-600">
          Describe what you need in plain English, and DeskForge will build it for you.
        </p>
      </div>

      {/* Data Source Selector */}
      {dataSources.length > 0 && (
        <div className="bg-muted/30 border rounded-lg p-4">
          <label className="text-sm font-medium mb-2 block">
            Connect a Data Source (optional)
          </label>
          <p className="text-xs text-muted-foreground mb-3">
            Select a data source to give the AI context about your data columns and structure.
          </p>
          <select
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={selectedDataSource}
            onChange={(e) => setSelectedDataSource(e.target.value)}
          >
            <option value="">No data source — generate with generic columns</option>
            {dataSources.map((ds) => (
              <option key={ds.id} value={ds.id}>
                {ds.name} ({ds.type}) — {ds.row_count ?? 0} rows
              </option>
            ))}
          </select>
        </div>
      )}

      <Tabs defaultValue="describe" className="w-full">
        <TabsList>
          <TabsTrigger value="describe">Describe Your Tool</TabsTrigger>
          <TabsTrigger value="templates">Start from Template</TabsTrigger>
        </TabsList>
        <TabsContent value="describe" className="mt-6">
          <PromptInput onSubmit={(prompt) => handleGenerate(prompt)} isLoading={isGenerating} />
        </TabsContent>
        <TabsContent value="templates" className="mt-6">
          <TemplateGallery onSelect={(templateId, prompt) => handleGenerate(prompt, templateId)} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
