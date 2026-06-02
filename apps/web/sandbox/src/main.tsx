import React from "react";
import ReactDOM from "react-dom/client";
import { SandboxRenderer } from "./renderer";
import "./styles.css";

interface ToolSpec {
  version: number;
  name: string;
  layout: { type: string; columns: number; gap?: string };
  components: Array<{
    id: string;
    type: string;
    position: { row: number; col: number; colSpan?: number; rowSpan?: number };
    props: Record<string, any>;
    dataSourceRef?: string;
  }>;
  dataSources: Array<{
    id: string;
    type: string;
    connectionId?: string;
    table?: string;
    query?: Record<string, any>;
  }>;
  actions?: Array<{
    id: string;
    type: string;
    dataSourceRef: string;
    triggerComponentId: string;
  }>;
}

const root = ReactDOM.createRoot(document.getElementById("root")!);

function handleMessage(event: MessageEvent) {
  const { type, spec, data, requestId } = event.data;

  if (type === "render") {
    root.render(
      <React.StrictMode>
        <SandboxRenderer spec={spec as ToolSpec} />
      </React.StrictMode>
    );
    window.parent.postMessage({ type: "rendered", success: true }, "*");
  } else if (type === "data-response") {
    // Dispatch custom event for data bridge
    window.dispatchEvent(new CustomEvent("sandbox-data", { detail: { requestId, data } }));
  }
}

window.addEventListener("message", handleMessage);

// Signal ready
window.parent.postMessage({ type: "sandbox-ready" }, "*");
