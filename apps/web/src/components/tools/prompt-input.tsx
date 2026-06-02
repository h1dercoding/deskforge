'use client';

import React, { useState } from 'react';
import { Send } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { MIN_PROMPT_LENGTH, MAX_PROMPT_LENGTH } from '@/lib/constants';

interface PromptInputProps {
  onSubmit: (prompt: string) => void;
  isLoading?: boolean;
  placeholder?: string;
  initialValue?: string;
}

export function PromptInput({
  onSubmit,
  isLoading = false,
  placeholder = 'Describe the tool you want to build. Be specific about the data, layout, and interactions you need...',
  initialValue = '',
}: PromptInputProps) {
  const [prompt, setPrompt] = useState(initialValue);
  const [error, setError] = useState<string | undefined>();

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setPrompt(e.target.value);
    if (error) setError(undefined);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = prompt.trim();
    if (trimmed.length < MIN_PROMPT_LENGTH) {
      setError(`Description must be at least ${MIN_PROMPT_LENGTH} characters`);
      return;
    }
    if (trimmed.length > MAX_PROMPT_LENGTH) {
      setError(`Description must be at most ${MAX_PROMPT_LENGTH} characters`);
      return;
    }
    onSubmit(trimmed);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <Textarea
        value={prompt}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        error={error}
        maxLength={MAX_PROMPT_LENGTH}
        showCharCount
        className="min-h-[120px] text-base"
        disabled={isLoading}
      />
      <div className="flex items-center justify-between">
        <p className="text-xs text-muted-foreground">
          Press <kbd className="px-1 py-0.5 bg-muted rounded text-xs">Ctrl</kbd> + <kbd className="px-1 py-0.5 bg-muted rounded text-xs">Enter</kbd> to submit
        </p>
        <Button type="submit" disabled={isLoading || prompt.trim().length < MIN_PROMPT_LENGTH}>
          {isLoading ? (
            <>
              <span className="animate-spin mr-2">⏳</span>
              Generating...
            </>
          ) : (
            <>
              <Send className="h-4 w-4 mr-2" />
              Generate
            </>
          )}
        </Button>
      </div>
    </form>
  );
}
