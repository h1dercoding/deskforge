'use client';

import React from 'react';
import { Toaster } from '@/components/shared/toaster';
import { ErrorBoundary } from '@/components/shared/error-boundary';

export function ClientProviders({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary>
      {children}
      <Toaster />
    </ErrorBoundary>
  );
}
