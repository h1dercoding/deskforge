'use client';

import React from 'react';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { ToolTheme } from '@/types';

interface ThemeEditorProps {
  theme: ToolTheme;
  onChange: (theme: ToolTheme) => void;
}

const fontOptions = [
  { label: 'Inter', value: 'Inter' },
  { label: 'Roboto', value: 'Roboto' },
  { label: 'Open Sans', value: 'Open Sans' },
  { label: 'Lato', value: 'Lato' },
  { label: 'Poppins', value: 'Poppins' },
  { label: 'Montserrat', value: 'Montserrat' },
  { label: 'System Default', value: 'system-ui' },
];

const radiusOptions = [
  { label: 'None', value: '0px' },
  { label: 'Small', value: '4px' },
  { label: 'Medium', value: '8px' },
  { label: 'Large', value: '12px' },
  { label: 'Full', value: '9999px' },
];

export function ThemeEditor({ theme, onChange }: ThemeEditorProps) {
  const updateTheme = (updates: Partial<ToolTheme>) => {
    onChange({ ...theme, ...updates });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Theme</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Primary Color</label>
          <div className="flex items-center gap-2">
            <input
              type="color"
              value={theme.primaryColor || '#3b82f6'}
              onChange={(e) => updateTheme({ primaryColor: e.target.value })}
              className="h-10 w-10 rounded border cursor-pointer"
            />
            <Input
              value={theme.primaryColor || '#3b82f6'}
              onChange={(e) => updateTheme({ primaryColor: e.target.value })}
              className="flex-1"
              placeholder="#3b82f6"
            />
          </div>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Background Color</label>
          <div className="flex items-center gap-2">
            <input
              type="color"
              value={theme.backgroundColor || '#ffffff'}
              onChange={(e) => updateTheme({ backgroundColor: e.target.value })}
              className="h-10 w-10 rounded border cursor-pointer"
            />
            <Input
              value={theme.backgroundColor || '#ffffff'}
              onChange={(e) => updateTheme({ backgroundColor: e.target.value })}
              className="flex-1"
              placeholder="#ffffff"
            />
          </div>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Font Family</label>
          <Select
            value={theme.fontFamily || 'Inter'}
            onValueChange={(value) => updateTheme({ fontFamily: value })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select font" />
            </SelectTrigger>
            <SelectContent>
              {fontOptions.map((font) => (
                <SelectItem key={font.value} value={font.value}>
                  {font.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Border Radius</label>
          <Select
            value={theme.borderRadius || '8px'}
            onValueChange={(value) => updateTheme({ borderRadius: value })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select radius" />
            </SelectTrigger>
            <SelectContent>
              {radiusOptions.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </CardContent>
    </Card>
  );
}
