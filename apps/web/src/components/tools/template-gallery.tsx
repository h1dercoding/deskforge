'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Template } from '@/types';

interface TemplateGalleryProps {
  templates: Template[];
  onSelect: (template: Template) => void;
  isLoading?: boolean;
}

const defaultTemplates: Template[] = [
  {
    id: 'dashboard',
    name: 'Analytics Dashboard',
    description: 'KPI cards, line chart, and data table for business metrics',
    category: 'Analytics',
    prompt: 'Create an analytics dashboard with KPI cards showing revenue, users, and conversion rate, a line chart for trends, and a sortable data table.',
    spec: { version: 1, name: 'Analytics Dashboard', layout: { type: 'grid', columns: 12 }, dataSources: [], components: [] },
  },
  {
    id: 'crud',
    name: 'CRUD Manager',
    description: 'Create, read, update, delete records with a form and table',
    category: 'Data Management',
    prompt: 'Build a CRUD manager with a form to add/edit records and a data table to view, search, and delete entries.',
    spec: { version: 1, name: 'CRUD Manager', layout: { type: 'grid', columns: 12 }, dataSources: [], components: [] },
  },
  {
    id: 'survey',
    name: 'Survey Form',
    description: 'Multi-field form with validation and submission tracking',
    category: 'Forms',
    prompt: 'Create a survey form with multiple field types including text, select, checkbox, and radio buttons with validation.',
    spec: { version: 1, name: 'Survey Form', layout: { type: 'single-column', columns: 1 }, dataSources: [], components: [] },
  },
  {
    id: 'inventory',
    name: 'Inventory Tracker',
    description: 'Track stock levels with KPIs and searchable table',
    category: 'Operations',
    prompt: 'Build an inventory tracker with KPI cards for total items and low stock alerts, plus a searchable and sortable data table.',
    spec: { version: 1, name: 'Inventory Tracker', layout: { type: 'grid', columns: 12 }, dataSources: [], components: [] },
  },
  {
    id: 'sales',
    name: 'Sales Report',
    description: 'Revenue breakdown with bar chart and pie chart',
    category: 'Analytics',
    prompt: 'Create a sales report with a bar chart for monthly revenue, a pie chart for category breakdown, and KPI cards.',
    spec: { version: 1, name: 'Sales Report', layout: { type: 'grid', columns: 12 }, dataSources: [], components: [] },
  },
  {
    id: 'project',
    name: 'Project Tracker',
    description: 'Task management with status overview and data table',
    category: 'Productivity',
    prompt: 'Build a project tracker with KPI cards for tasks by status, a bar chart for progress by project, and a task list table.',
    spec: { version: 1, name: 'Project Tracker', layout: { type: 'grid', columns: 12 }, dataSources: [], components: [] },
  },
];

export function TemplateGallery({ templates, onSelect, isLoading }: TemplateGalleryProps) {
  const displayTemplates = templates.length > 0 ? templates : defaultTemplates;

  return (
    <div>
      <h3 className="text-lg font-semibold mb-4">Start from a template</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {displayTemplates.map((template) => (
          <Card
            key={template.id}
            className="cursor-pointer hover:shadow-md hover:border-primary/50 transition-all"
            onClick={() => onSelect(template)}
          >
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">{template.name}</CardTitle>
                <Badge variant="secondary">{template.category}</Badge>
              </div>
              <CardDescription className="line-clamp-2">{template.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-20 bg-muted rounded-md flex items-center justify-center">
                <span className="text-xs text-muted-foreground">Preview</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      {isLoading && (
        <div className="text-center py-8 text-muted-foreground">Loading templates...</div>
      )}
    </div>
  );
}
