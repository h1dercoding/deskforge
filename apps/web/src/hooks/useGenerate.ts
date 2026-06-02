'use client';

import { useState, useCallback, useRef } from 'react';
import { api } from '@/lib/api';
import { useEditorStore } from '@/stores/editorStore';
import type { ToolSpec, SSEProgressEvent, SSESpecEvent } from '@/types';

interface GenerateOptions {
  prompt: string;
  dataSourceId?: string;
  templateId?: string;
}

interface IterateOptions {
  toolId: string;
  message: string;
}

export function useGenerate() {
  const [progress, setProgress] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const { setGenerating, setGenerationStep, updateSpec, addMessage } = useEditorStore();

  const generate = useCallback(
    (options: GenerateOptions): Promise<{ spec: ToolSpec; toolId?: string }> => {
      return new Promise((resolve, reject) => {
        setError(null);
        setGenerating(true);
        setGenerationStep('analyzing');
        setProgress('Understanding your requirements...');

        addMessage({
          id: Date.now().toString(),
          role: 'user',
          content: options.prompt,
          timestamp: new Date().toISOString(),
        });

        const es = api.createEventSource('/generate', {
          prompt: options.prompt,
          data_source_id: options.dataSourceId,
          template_id: options.templateId,
        });
        eventSourceRef.current = es;

        es.addEventListener('progress', ((event: MessageEvent) => {
          const data: SSEProgressEvent = JSON.parse(event.data);
          setGenerationStep(data.step);
          setProgress(data.message);
        }) as EventListener);

        es.addEventListener('spec', ((event: MessageEvent) => {
          const data: SSESpecEvent = JSON.parse(event.data);
          updateSpec(data.spec);
          setGenerating(false);
          setGenerationStep(null);
          setProgress(null);

          addMessage({
            id: Date.now().toString(),
            role: 'assistant',
            content: 'Here is the generated tool. You can iterate by describing changes below.',
            timestamp: new Date().toISOString(),
          });

          resolve({ spec: data.spec, toolId: data.tool_id });
        }) as EventListener);

        es.addEventListener('error', ((event: MessageEvent) => {
          try {
            const data = JSON.parse(event.data);
            setError(data.error?.message || 'Generation failed');
          } catch {
            setError('Generation failed');
          }
          setGenerating(false);
          setGenerationStep(null);
          setProgress(null);
          reject(new Error('Generation failed'));
        }) as EventListener);

        es.addEventListener('done', (() => {
          es.close();
        }) as EventListener);
      });
    },
    [setGenerating, setGenerationStep, updateSpec, addMessage]
  );

  const iterate = useCallback(
    (options: IterateOptions): Promise<{ spec: ToolSpec }> => {
      return new Promise((resolve, reject) => {
        setError(null);
        setGenerating(true);
        setGenerationStep('iterating');
        setProgress('Applying your changes...');

        addMessage({
          id: Date.now().toString(),
          role: 'user',
          content: options.message,
          timestamp: new Date().toISOString(),
        });

        const es = api.createEventSource(`/generate/${options.toolId}/iterate`, {
          message: options.message,
        });
        eventSourceRef.current = es;

        es.addEventListener('progress', ((event: MessageEvent) => {
          const data: SSEProgressEvent = JSON.parse(event.data);
          setGenerationStep(data.step);
          setProgress(data.message);
        }) as EventListener);

        es.addEventListener('spec', ((event: MessageEvent) => {
          const data: SSESpecEvent = JSON.parse(event.data);
          updateSpec(data.spec);
          setGenerating(false);
          setGenerationStep(null);
          setProgress(null);

          addMessage({
            id: Date.now().toString(),
            role: 'assistant',
            content: 'Changes applied. Review the preview and iterate further if needed.',
            timestamp: new Date().toISOString(),
          });

          resolve({ spec: data.spec });
        }) as EventListener);

        es.addEventListener('error', ((event: MessageEvent) => {
          try {
            const data = JSON.parse(event.data);
            setError(data.error?.message || 'Iteration failed');
          } catch {
            setError('Iteration failed');
          }
          setGenerating(false);
          setGenerationStep(null);
          setProgress(null);
          reject(new Error('Iteration failed'));
        }) as EventListener);

        es.addEventListener('done', (() => {
          es.close();
        }) as EventListener);
      });
    },
    [setGenerating, setGenerationStep, updateSpec, addMessage]
  );

  const cancel = useCallback(() => {
    eventSourceRef.current?.close();
    setGenerating(false);
    setGenerationStep(null);
    setProgress(null);
  }, [setGenerating, setGenerationStep]);

  return {
    generate,
    iterate,
    cancel,
    progress,
    error,
  };
}
