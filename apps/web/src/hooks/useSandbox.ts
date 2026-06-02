'use client';

import { useEffect, useCallback, useRef } from 'react';
import { SANDBOX_ORIGIN } from '@/lib/constants';
import type { ToolSpec } from '@/types';

interface SandboxMessage {
  type: string;
  payload?: unknown;
  requestId?: string;
}

interface UseSandboxOptions {
  iframeRef: React.RefObject<HTMLIFrameElement | null>;
  spec: ToolSpec | null;
  onDataRequest?: (sourceId: string, query: unknown) => Promise<unknown>;
}

export function useSandbox({ iframeRef, spec, onDataRequest }: UseSandboxOptions) {
  const isReadyRef = useRef(false);

  const sendSpec = useCallback(
    (specData: ToolSpec) => {
      if (!iframeRef.current?.contentWindow) return;
      iframeRef.current.contentWindow.postMessage(
        { type: 'SPEC_UPDATE', payload: specData },
        SANDBOX_ORIGIN
      );
    },
    [iframeRef]
  );

  const sendData = useCallback(
    (requestId: string, data: unknown) => {
      if (!iframeRef.current?.contentWindow) return;
      iframeRef.current.contentWindow.postMessage(
        { type: 'DATA_RESPONSE', requestId, payload: data },
        SANDBOX_ORIGIN
      );
    },
    [iframeRef]
  );

  const sendError = useCallback(
    (requestId: string, error: string) => {
      if (!iframeRef.current?.contentWindow) return;
      iframeRef.current.contentWindow.postMessage(
        { type: 'DATA_ERROR', requestId, payload: { error } },
        SANDBOX_ORIGIN
      );
    },
    [iframeRef]
  );

  useEffect(() => {
    const handleMessage = async (event: MessageEvent) => {
      if (event.origin !== SANDBOX_ORIGIN) return;

      const message = event.data as SandboxMessage;

      switch (message.type) {
        case 'SANDBOX_READY':
          isReadyRef.current = true;
          if (spec) {
            sendSpec(spec);
          }
          break;

        case 'DATA_REQUEST': {
          if (!onDataRequest || !message.requestId) break;
          try {
            const data = await onDataRequest(
              (message.payload as { sourceId: string }).sourceId,
              (message.payload as { query: unknown }).query
            );
            sendData(message.requestId, data);
          } catch (err) {
            sendError(
              message.requestId,
              err instanceof Error ? err.message : 'Data request failed'
            );
          }
          break;
        }

        case 'SANDBOX_ERROR':
          console.error('Sandbox error:', message.payload);
          break;
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [spec, onDataRequest, sendSpec, sendData, sendError]);

  useEffect(() => {
    if (isReadyRef.current && spec) {
      sendSpec(spec);
    }
  }, [spec, sendSpec]);

  return {
    sendSpec,
    sendData,
    sendError,
    isReady: isReadyRef.current,
  };
}
