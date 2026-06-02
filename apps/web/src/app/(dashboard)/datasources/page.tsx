"use client";

import { useEffect, useState } from "react";
import { DataSourceCard } from "@/components/datasources/datasource-card";
import { CsvUpload } from "@/components/datasources/csv-upload";
import { DbForm } from "@/components/datasources/db-form";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/api";
import type { DataSource } from "@/types";

export default function DataSourcesPage() {
  const [sources, setSources] = useState<DataSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);

  const loadSources = async () => {
    try {
      const res = await api.get("/datasources");
      setSources(res.data.sources || []);
    } catch (e) {
      console.error("Failed to load data sources:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadSources(); }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Data Sources</h1>
          <p className="text-gray-500">Connect your data to power your tools</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>Add Data Source</Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Add Data Source</DialogTitle>
            </DialogHeader>
            <Tabs defaultValue="csv">
              <TabsList>
                <TabsTrigger value="csv">CSV / Excel</TabsTrigger>
                <TabsTrigger value="database">Database</TabsTrigger>
              </TabsList>
              <TabsContent value="csv" className="mt-4">
                <CsvUpload onComplete={() => { setDialogOpen(false); loadSources(); }} />
              </TabsContent>
              <TabsContent value="database" className="mt-4">
                <DbForm onComplete={() => { setDialogOpen(false); loadSources(); }} />
              </TabsContent>
            </Tabs>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? (
        <p className="text-gray-400">Loading...</p>
      ) : sources.length === 0 ? (
        <div className="text-center py-12 border rounded-lg bg-gray-50">
          <p className="text-gray-500">No data sources yet. Add one to get started.</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {sources.map((source) => (
            <DataSourceCard key={source.id} source={source} onDelete={loadSources} />
          ))}
        </div>
      )}
    </div>
  );
}
