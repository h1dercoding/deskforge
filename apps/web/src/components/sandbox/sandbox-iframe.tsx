'use client';

import React, { useRef, useEffect } from 'react';
import { SANDBOX_ORIGIN } from '@/lib/constants';
import { useSandbox } from '@/hooks/useSandbox';
import type { ToolSpec } from '@/types';

interface SandboxIframeProps {
  spec: ToolSpec | null;
  onDataRequest?: (sourceId: string, query: unknown) => Promise<unknown>;
  className?: string;
}

export function SandboxIframe({ spec, onDataRequest, className }: SandboxIframeProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useSandbox({ iframeRef, spec, onDataRequest });

  return (
    <iframe
      ref={iframeRef}
      data-sandbox="true"
      src={`${SANDBOX_ORIGIN}/index.html`}
      // Security: Only allow-scripts — NOT allow-same-origin.
      // allow-scripts + allow-same-origin would let the iframe remove its own sandbox.
      // Communication with the parent is via postMessage only (different origin).
      sandbox="allow-scripts"
      className={className || 'w-full h-full border-0 rounded-lg bg-white'}
      title="Tool Preview"
    />
  );
}
