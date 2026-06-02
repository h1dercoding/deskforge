'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from '@/hooks/useToast';

interface DbFormProps {
  onSubmit: (data: DbFormData) => void;
  onTest?: (data: DbFormData) => void;
  isLoading?: boolean;
}

export interface DbFormData {
  type: 'postgresql' | 'mysql';
  host: string;
  port: string;
  db: string;
  user: string;
  pass: string;
  ssl: boolean;
  readonly: boolean;
}

export function DbForm({ onSubmit, onTest, isLoading }: DbFormProps) {
  const [form, setForm] = useState<DbFormData>({
    type: 'postgresql',
    host: 'localhost',
    port: '5432',
    db: '',
    user: '',
    pass: '',
    ssl: false,
    readonly: true,
  });

  const update = (field: keyof DbFormData, value: string | boolean) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.host || !form.db || !form.user) {
      toast({ title: 'Missing fields', description: 'Please fill in all required fields.', variant: 'destructive' });
      return;
    }
    onSubmit(form);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <label className="text-sm font-medium">Database Type</label>
        <Select value={form.type} onValueChange={(v) => update('type', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="postgresql">PostgreSQL</SelectItem>
            <SelectItem value="mysql">MySQL</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="col-span-2">
          <Input
            label="Host"
            value={form.host}
            onChange={(e) => update('host', e.target.value)}
            placeholder="localhost"
            required
          />
        </div>
        <Input
          label="Port"
          value={form.port}
          onChange={(e) => update('port', e.target.value)}
          placeholder={form.type === 'postgresql' ? '5432' : '3306'}
        />
      </div>

      <Input
        label="Database Name"
        value={form.db}
        onChange={(e) => update('db', e.target.value)}
        placeholder="my_database"
        required
      />

      <Input
        label="Username"
        value={form.user}
        onChange={(e) => update('user', e.target.value)}
        placeholder="db_user"
        required
      />

      <Input
        label="Password"
        type="password"
        value={form.pass}
        onChange={(e) => update('pass', e.target.value)}
        placeholder="••••••••"
      />

      <div className="flex items-center gap-4">
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={form.ssl}
            onChange={(e) => update('ssl', e.target.checked)}
            className="rounded border-gray-300"
          />
          Use SSL
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={form.readonly}
            onChange={(e) => update('readonly', e.target.checked)}
            className="rounded border-gray-300"
          />
          Read-only
        </label>
      </div>

      <div className="flex gap-2">
        {onTest && (
          <Button type="button" variant="outline" onClick={() => onTest(form)} disabled={isLoading}>
            Test Connection
          </Button>
        )}
        <Button type="submit" disabled={isLoading} className="flex-1">
          {isLoading ? 'Connecting...' : 'Connect'}
        </Button>
      </div>
    </form>
  );
}
