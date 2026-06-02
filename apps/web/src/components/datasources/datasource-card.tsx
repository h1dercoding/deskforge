'use client';

import React from 'react';
import Link from 'next/link';
import { Database, FileSpreadsheet, Table2, Trash2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { formatDate, getStatusColor } from '@/lib/utils';
import type { DataSource } from '@/types';

interface DataSourceCardProps {
  source: DataSource;
  onDelete?: (id: string) => void;
}

const typeIcons: Record<string, React.ElementType> = {
  csv: FileSpreadsheet,
  google_sheets: Table2,
  postgresql: Database,
  mysql: Database,
};

export function DataSourceCard({ source, onDelete }: DataSourceCardProps) {
  const Icon = typeIcons[source.type] || Database;

  return (
    <Card className="group hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <Link href={`/datasources/${source.id}`} className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
              <Icon className="h-5 w-5 text-primary" />
            </div>
            <div>
              <CardTitle className="text-base hover:text-primary transition-colors">
                {source.name}
              </CardTitle>
              <p className="text-xs text-muted-foreground capitalize">{source.type.replace('_', ' ')}</p>
            </div>
          </Link>
          {onDelete && (
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 opacity-0 group-hover:opacity-100"
              onClick={() => onDelete(source.id)}
            >
              <Trash2 className="h-4 w-4 text-destructive" />
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Badge className={getStatusColor(source.status)} variant="outline">
              {source.status}
            </Badge>
            {source.row_count > 0 && (
              <span className="text-xs text-muted-foreground">
                {source.row_count.toLocaleString()} rows
              </span>
            )}
          </div>
          <span className="text-xs text-muted-foreground">
            {formatDate(source.updated_at)}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
