'use client';

import React, { useEffect, useCallback, useRef } from 'react';
import { SANDBOX_ORIGIN } from '@/lib/constants';
import { api } from '@/lib/api';
import type { ApiResponse } from '@/types';

interface SandboxBridgeProps {
  toolId: string;
  iframeRef?: React.RefObject<HTMLIFrameElement | null>;
}

export function SandboxBridge({ toolId, iframeRef }: SandboxBridgeProps) {
  // Use a local ref as fallback when no external ref is provided
  const localIframeRef = useRef<HTMLIFrameElement | null>(null);

  const getIframe = () =>
    iframeRef?.current || localIframeRef.current || document.querySelector('iframe[data-sandbox]');

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

          const iframe = getIframe();
          iframe?.contentWindow?.postMessage(
            { type: 'DATA_RESPONSE', requestId, payload: response.data },
            SANDBOX_ORIGIN
          );
        } catch (err) {
          const iframe = getIframe();
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

      // Handle form submissions from the sandbox
      if (type === 'FORM_SUBMIT' && requestId) {
        try {
          const response = await api.post<ApiResponse<{ id: string }>>(
            `/tools/${toolId}/submissions`,
            { data: payload.data, submitted_by: payload.submitted_by }
          );

          const iframe = getIframe();
          iframe?.contentWindow?.postMessage(
            { type: 'FORM_SUBMIT_RESPONSE', requestId, payload: { success: true, id: response.data.id } },
            SANDBOX_ORIGIN
          );
        } catch (err) {
          const iframe = getIframe();
          iframe?.contentWindow?.postMessage(
            {
              type: 'FORM_SUBMIT_ERROR',
              requestId,
              payload: { error: err instanceof Error ? err.message : 'Form submission failed' },
            },
            SANDBOX_ORIGIN
          );
        }
      }
    },
    [iframeRef, toolId]
  );

  useEffect(() => {
    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [handleMessage]);

  return null;
}
