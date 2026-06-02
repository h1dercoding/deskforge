/**
 * Data bridge for sandbox communication with parent window.
 * All data requests from sandbox components go through postMessage.
 */

export interface DataRequest {
  type: "data-request";
  requestId: string;
  dataSourceRef: string;
  query?: {
    filter?: Record<string, any>;
    sort?: Array<{ key: string; direction: "asc" | "desc" }>;
    page?: number;
    per_page?: number;
    aggregate?: boolean;
  };
}

export interface DataResponse {
  type: "data-response";
  requestId: string;
  data: {
    rows: any[];
    total?: number;
  };
}

export interface ActionRequest {
  type: "action";
  action: {
    id: string;
    type: "create" | "update" | "delete";
    dataSourceRef: string;
  };
  data: Record<string, any>;
}

// Utility to request data from parent
export function requestData(dataSourceRef: string, query?: Record<string, any>): Promise<any> {
  return new Promise((resolve) => {
    const requestId = `${dataSourceRef}-${Date.now()}`;
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail;
      if (detail.requestId === requestId) {
        window.removeEventListener("sandbox-data", handler);
        resolve(detail.data);
      }
    };
    window.addEventListener("sandbox-data", handler);
    window.parent.postMessage({ type: "data-request", requestId, dataSourceRef, query }, "*");
  });
}
