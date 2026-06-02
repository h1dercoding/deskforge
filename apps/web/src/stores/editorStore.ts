'use client';

import { create } from 'zustand';
import type { Tool, ToolSpec, ChatMessage } from '@/types';

interface EditorState {
  tool: Tool | null;
  spec: ToolSpec | null;
  chatHistory: ChatMessage[];
  isGenerating: boolean;
  generationStep: string | null;

  setTool: (tool: Tool) => void;
  updateSpec: (spec: ToolSpec) => void;
  addMessage: (message: ChatMessage) => void;
  clearChat: () => void;
  setGenerating: (generating: boolean) => void;
  setGenerationStep: (step: string | null) => void;
  reset: () => void;
}

export const useEditorStore = create<EditorState>()((set) => ({
  tool: null,
  spec: null,
  chatHistory: [],
  isGenerating: false,
  generationStep: null,

  setTool: (tool: Tool) =>
    set({
      tool,
      spec: tool.spec,
    }),

  updateSpec: (spec: ToolSpec) =>
    set((state) => ({
      spec,
      tool: state.tool ? { ...state.tool, spec } : null,
    })),

  addMessage: (message: ChatMessage) =>
    set((state) => ({
      chatHistory: [...state.chatHistory, message],
    })),

  clearChat: () => set({ chatHistory: [] }),

  setGenerating: (generating: boolean) => set({ isGenerating: generating }),

  setGenerationStep: (step: string | null) => set({ generationStep: step }),

  reset: () =>
    set({
      tool: null,
      spec: null,
      chatHistory: [],
      isGenerating: false,
      generationStep: null,
    }),
}));
