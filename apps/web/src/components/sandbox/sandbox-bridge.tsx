'use client';

import React, { useEffect, useCallback } from 'react';
import { SANDBOX_ORIGIN } from '@/lib/constants';
import { api } from '@/lib/api';
import type { ApiResponse } from '@/types';

interface SandboxBridgeProps {
  toolId: string;
}

export function SandboxBridge({ toolId }: SandboxBridgeProps) {
  const handleMessage = useCallback(
    async (event: MessageEvent) => {
      if (event.origin !== SANDBOX_ORIGIN) return;

      const { type, payload, requestId } = event.data;

      if (type === 'DATA_REQUEST' && requestId) {
        try {
          const response = await api.post<ApiResponse<{ rows: unknown[]; total: number }>>(
            `/datasources/${payload.sourceId}/query`,
            { query: payload.query }
          );

          const iframe = document.querySelector('iframe');
          iframe?.contentWindow?.postMessage(
            { type: 'DATA_RESPONSE', requestId, payload: response.data },
            SANDBOX_ORIGIN
          );
        } catch (err) {
          const iframe = document.querySelector('iframe');
          iframe?.contentWindow?.postMessage(
            {
              type: 'DATA_ERROR',
              requestId,
              payload: { error: err instanceof Error ? err.message : 'Data request failed' },
            },
            SANDBOX_ORIGIN
          );
        }
      }
    },
    []
  );

  useEffect(() => {
    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [handleMessage]);

  return null;
}
