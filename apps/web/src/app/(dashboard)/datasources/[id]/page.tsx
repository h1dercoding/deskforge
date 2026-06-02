"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { api } from "@/lib/api";
import type { DataSource } from "@/types";

export default function DataSourceDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [source, setSource] = useState<DataSource | null>(null);
  const [schema, setSchema] = useState<{ columns: { name: string; type: string }[] } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get(`/datasources`).then((r) => r.data.sources?.find((s: DataSource) => s.id === id)),
      api.get(`/datasources/${id}/schema`).then((r) => r.data).catch(() => null),
    ]).then(([s, sch]) => {
      setSource(s || null);
      setSchema(sch);
      setLoading(false);
    });
  }, [id]);

  if (loading) return <LoadingSpinner message="Loading data source..." />;
  if (!source) return <div className="p-8 text-center text-gray-500">Data source not found</div>;

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{source.name}</h1>
          <div className="flex items-center gap-2 mt-1">
            <Badge variant="outline">{source.type}</Badge>
            <Badge variant={source.status === "connected" ? "default" : "destructive"}>{source.status}</Badge>
          </div>
        </div>
        <Button variant="outline" onClick={() => api.post(`/datasources/${id}/test`).then((r) => alert(r.data.status))}>
          Test Connection
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Schema</CardTitle>
        </CardHeader>
        <CardContent>
          {schema?.columns?.length ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Column Name</TableHead>
                  <TableHead>Type</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {schema.columns.map((col) => (
                  <TableRow key={col.name}>
                    <TableCell className="font-mono">{col.name}</TableCell>
                    <TableCell><Badge variant="secondary">{col.type}</Badge></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="text-gray-400">No schema information available</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
