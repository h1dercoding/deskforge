import React, { useState, useMemo } from "react";
import { Search, ChevronUp, ChevronDown, ChevronLeft, ChevronRight } from "lucide-react";

interface Column {
  key: string;
  label: string;
  type?: string;
}

interface DataTableProps {
  spec: {
    props: {
      columns?: Column[];
      title?: string;
      pageSize?: number;
      searchable?: boolean;
    };
  };
  dataSourceRef?: string;
}

export function DataTable({ spec, dataSourceRef }: DataTableProps) {
  const columns = spec.props.columns || [];
  const pageSize = spec.props.pageSize || 25;
  const searchable = spec.props.searchable !== false;

  const [data, setData] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const [page, setPage] = useState(1);

  // Request data from parent
  React.useEffect(() => {
    if (!dataSourceRef) return;
    const requestId = `${dataSourceRef}-${Date.now()}`;
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail;
      if (detail.requestId === requestId) {
        setData(detail.data?.rows || []);
      }
    };
    window.addEventListener("sandbox-data", handler);
    window.parent.postMessage({ type: "data-request", requestId, dataSourceRef }, "*");
    return () => window.removeEventListener("sandbox-data", handler);
  }, [dataSourceRef]);

  const filtered = useMemo(() => {
    let result = data;
    if (search) {
      const q = search.toLowerCase();
      result = result.filter((row) =>
        Object.values(row).some((v) => String(v).toLowerCase().includes(q))
      );
    }
    if (sortKey) {
      result = [...result].sort((a, b) => {
        const va = a[sortKey] ?? "";
        const vb = b[sortKey] ?? "";
        const cmp = String(va).localeCompare(String(vb), undefined, { numeric: true });
        return sortDir === "asc" ? cmp : -cmp;
      });
    }
    return result;
  }, [data, search, sortKey, sortDir]);

  const totalPages = Math.ceil(filtered.length / pageSize);
  const paginated = filtered.slice((page - 1) * pageSize, page * pageSize);

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  return (
    <div className="border rounded-lg overflow-hidden bg-white">
      <div className="p-4 border-b flex items-center justify-between">
        <h3 className="font-semibold text-gray-900">{spec.props.title || "Data Table"}</h3>
        {searchable && (
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              className="pl-9 pr-3 py-1.5 border rounded-md text-sm w-64 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Search..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            />
          </div>
        )}
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  className="px-4 py-3 text-left font-medium text-gray-600 cursor-pointer hover:bg-gray-100 select-none"
                  onClick={() => handleSort(col.key)}
                >
                  <div className="flex items-center gap-1">
                    {col.label}
                    {sortKey === col.key && (
                      sortDir === "asc" ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y">
            {paginated.length === 0 ? (
              <tr>
                <td colSpan={columns.length || 1} className="px-4 py-8 text-center text-gray-400">
                  No data available
                </td>
              </tr>
            ) : (
              paginated.map((row, i) => (
                <tr key={i} className="hover:bg-gray-50">
                  {columns.map((col) => (
                    <td key={col.key} className="px-4 py-3 text-gray-700">
                      {String(row[col.key] ?? "")}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      {totalPages > 1 && (
        <div className="p-3 border-t flex items-center justify-between text-sm text-gray-500">
          <span>{filtered.length} rows</span>
          <div className="flex items-center gap-2">
            <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="p-1 disabled:opacity-30">
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span>Page {page} of {totalPages}</span>
            <button disabled={page >= totalPages} onClick={() => setPage(page + 1)} className="p-1 disabled:opacity-30">
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
