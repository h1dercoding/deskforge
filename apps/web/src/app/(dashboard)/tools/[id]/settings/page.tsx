"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ThemeEditor } from "@/components/tools/theme-editor";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { api } from "@/lib/api";
import { toast } from "@/hooks/useToast";
import type { Tool } from "@/types";

export default function ToolSettingsPage() {
  const params = useParams();
  const toolId = params.id as string;
  const [tool, setTool] = useState<Tool | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [visibility, setVisibility] = useState<"public" | "private">("private");
  const [theme, setTheme] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get(`/tools/${toolId}`).then((res) => {
      const t = res.data.tool as Tool;
      setTool(t);
      setName(t.name);
      setDescription(t.description || "");
      setVisibility(t.visibility);
      setTheme(t.theme || {});
      setLoading(false);
    });
  }, [toolId]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.patch(`/tools/${toolId}`, { name, description, theme });
      await api.patch(`/tools/${toolId}/sharing`, { visibility });
      toast({ title: "Saved!", description: "Tool settings updated successfully.", variant: "success" });
    } catch (e) {
      console.error("Save failed:", e);
      toast({ title: "Save failed", description: "Could not save changes.", variant: "destructive" });
    } finally {
      setSaving(false);
    }
  };

  const handleCopyLink = async () => {
    if (!tool?.slug) return;
    const url = `${window.location.origin}/t/${tool.slug}`;
    try {
      await navigator.clipboard.writeText(url);
      toast({ title: "Copied!", description: "Share link copied to clipboard.", variant: "success" });
    } catch {
      // Fallback for older browsers
      const textArea = document.createElement("textarea");
      textArea.value = url;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand("copy");
      document.body.removeChild(textArea);
      toast({ title: "Copied!", description: "Share link copied to clipboard.", variant: "success" });
    }
  };

  if (loading) return <LoadingSpinner message="Loading settings..." />;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Tool Settings</h1>
      <Card>
        <CardHeader>
          <CardTitle>General</CardTitle>
          <CardDescription>Basic tool information</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium">Name</label>
            <Input value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div>
            <label className="text-sm font-medium">Description</label>
            <Input value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Sharing</CardTitle>
          <CardDescription>Control who can access this tool</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <Button variant={visibility === "private" ? "default" : "outline"} onClick={() => setVisibility("private")}>
              Private
            </Button>
            <Button variant={visibility === "public" ? "default" : "outline"} onClick={() => setVisibility("public")}>
              Public
            </Button>
          </div>
          {visibility === "public" && tool?.slug && (
            <div className="mt-3 flex items-center gap-2">
              <code className="bg-gray-100 px-2 py-1 rounded text-sm flex-1 truncate">
                /t/{tool.slug}
              </code>
              <Button variant="outline" size="sm" onClick={handleCopyLink}>
                Copy Link
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Theme</CardTitle>
          <CardDescription>Customize the look and feel</CardDescription>
        </CardHeader>
        <CardContent>
          <ThemeEditor theme={theme} onChange={setTheme} />
        </CardContent>
      </Card>

      <Button onClick={handleSave} disabled={saving}>
        {saving ? "Saving..." : "Save Changes"}
      </Button>
    </div>
  );
}
