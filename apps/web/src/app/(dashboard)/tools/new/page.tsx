"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { PromptInput } from "@/components/tools/prompt-input";
import { TemplateGallery } from "@/components/tools/template-gallery";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/api";
import { useEditorStore } from "@/stores/editorStore";

export default function NewToolPage() {
  const router = useRouter();
  const [isGenerating, setIsGenerating] = useState(false);
  const { setTool, updateSpec } = useEditorStore();

  const handleGenerate = async (prompt: string, templateId?: string) => {
    setIsGenerating(true);
    try {
      const response = await api.post("/generate", { prompt, template_id: templateId });
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
