import { Link } from "@tanstack/react-router";
import {
  type ColumnDef,
  type SortingState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { useState } from "react";

import { VerdictBadge } from "@/components/VerdictBadge";
import { NEIGHBORHOODS } from "@/lib/data/neighborhoods";
import type { Metrics, Property } from "@/lib/data/properties";
import { fmtMoney, fmtPct, fmtSignedPct } from "@/lib/format";

export type ScreenerRow = { p: Property; m: Metrics };

// Sort verdicts by severity (go < watch < no-go) rather than alphabetically.
const VERDICT_ORDER: Record<string, number> = { go: 0, watch: 1, "no-go": 2 };
const neighborhoodName = (slug: string) => NEIGHBORHOODS.find((n) => n.slug === slug)?.name ?? slug;

// Right-aligned, monospaced numeric columns (by column id).
const NUMERIC = new Set([
  "beds",
  "list",
  "fair",
  "delta",
  "rent",
  "cap",
  "coc",
  "appr",
  "dom",
  "fit",
]);

const columns: ColumnDef<ScreenerRow>[] = [
  {
    id: "verdict",
    header: "Verdict",
    accessorFn: (r) => VERDICT_ORDER[r.m.verdict],
    cell: ({ row }) => (
      <Link to="/property/$id" params={{ id: row.original.p.id }}>
        <VerdictBadge
          verdict={row.original.m.verdict}
          confidence={row.original.m.verdictConfidence}
          size="sm"
        />
      </Link>
    ),
  },
  {
    id: "address",
    header: "Address",
    accessorFn: (r) => r.p.address,
    cell: ({ row }) => (
      <Link
        to="/property/$id"
        params={{ id: row.original.p.id }}
        className="underline-offset-4 hover:underline"
      >
        {row.original.p.address}
      </Link>
    ),
  },
  {
    id: "neighborhood",
    header: "Neighborhood",
    accessorFn: (r) => neighborhoodName(r.p.neighborhoodSlug),
    cell: ({ getValue }) => <span className="text-muted-foreground">{getValue() as string}</span>,
  },
  {
    id: "beds",
    header: "Beds",
    accessorFn: (r) => r.p.beds,
    cell: ({ row }) => `${row.original.p.beds}/${row.original.p.baths}`,
  },
  {
    id: "list",
    header: "List",
    accessorFn: (r) => r.p.listPrice,
    cell: ({ row }) => fmtMoney(row.original.p.listPrice, { compact: true }),
  },
  {
    id: "fair",
    header: "Fair",
    accessorFn: (r) => r.p.predictedPrice,
    cell: ({ row }) => (
      <span className="text-muted-foreground">
        {fmtMoney(row.original.p.predictedPrice, { compact: true })}
      </span>
    ),
  },
  {
    id: "delta",
    header: "Δ",
    accessorFn: (r) => r.m.pricePremium,
    cell: ({ row }) => {
      const d = row.original.m.pricePremium;
      return (
        <span className={d < 0 ? "text-go-strong" : d > 0.05 ? "text-nogo-strong" : ""}>
          {fmtSignedPct(d)}
        </span>
      );
    },
  },
  {
    id: "rent",
    header: "Rent/mo",
    accessorFn: (r) => r.p.predictedRent,
    cell: ({ row }) => `$${row.original.p.predictedRent.toLocaleString()}`,
  },
  {
    id: "cap",
    header: "Cap",
    accessorFn: (r) => r.m.capRate,
    cell: ({ row }) => fmtPct(row.original.m.capRate, 2),
  },
  {
    id: "coc",
    header: "CoC",
    accessorFn: (r) => r.m.cashOnCash,
    cell: ({ row }) => fmtPct(row.original.m.cashOnCash, 2),
  },
  {
    id: "appr",
    header: "Appr 5y",
    accessorFn: (r) => r.p.expectedAppreciation,
    cell: ({ row }) => fmtPct(row.original.p.expectedAppreciation, 1),
  },
  {
    id: "dom",
    header: "DOM",
    accessorFn: (r) => r.p.expectedDom,
    cell: ({ row }) => `${row.original.p.expectedDom}d`,
  },
  {
    id: "fit",
    header: "Tenant fit",
    accessorFn: (r) => r.p.tenantFitScore,
    cell: ({ row }) => row.original.p.tenantFitScore,
  },
];

export function ScreenerTable({ rows }: { rows: ScreenerRow[] }) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [globalFilter, setGlobalFilter] = useState("");

  const table = useReactTable({
    data: rows,
    columns,
    state: { sorting, globalFilter },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    // Free-text search over address + submarket name only (numeric columns are
    // filtered via the sidebar controls, not text search).
    globalFilterFn: (row, _columnId, value) => {
      const q = String(value).toLowerCase().trim();
      if (!q) return true;
      const p = row.original.p;
      return (
        p.address.toLowerCase().includes(q) ||
        neighborhoodName(p.neighborhoodSlug).toLowerCase().includes(q)
      );
    },
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  const visible = table.getRowModel().rows;

  return (
    <div>
      <div className="mb-4 flex items-center justify-between gap-4">
        <input
          value={globalFilter}
          onChange={(e) => setGlobalFilter(e.target.value)}
          placeholder="Search address or submarket…"
          aria-label="Search candidates by address or submarket"
          className="w-full max-w-xs rule-b border-foreground bg-transparent py-2 text-sm focus:outline-none"
        />
        <span className="whitespace-nowrap text-xs text-muted-foreground">
          {visible.length} shown
        </span>
      </div>
      <div className="overflow-x-auto rule-t rule-b">
        <table className="w-full text-sm tabular">
          <thead>
            {table.getHeaderGroups().map((hg) => (
              <tr
                key={hg.id}
                className="rule-b text-left text-[10px] font-mono uppercase tracking-wider text-muted-foreground"
              >
                {hg.headers.map((h) => {
                  const sorted = h.column.getIsSorted();
                  const numeric = NUMERIC.has(h.column.id);
                  return (
                    <th
                      key={h.id}
                      scope="col"
                      aria-sort={
                        sorted === "asc" ? "ascending" : sorted === "desc" ? "descending" : "none"
                      }
                      className={`px-3 py-3 font-medium ${numeric ? "text-right" : ""}`}
                    >
                      {/* button (not the th) carries the click so sorting is keyboard-accessible */}
                      <button
                        type="button"
                        onClick={h.column.getToggleSortingHandler()}
                        className={`inline-flex select-none items-center gap-1 uppercase tracking-wider hover:text-foreground ${numeric ? "flex-row-reverse" : ""}`}
                      >
                        {flexRender(h.column.columnDef.header, h.getContext())}
                        <span aria-hidden>
                          {sorted === "asc" ? "↑" : sorted === "desc" ? "↓" : ""}
                        </span>
                      </button>
                    </th>
                  );
                })}
              </tr>
            ))}
          </thead>
          <tbody>
            {visible.map((row) => (
              <tr key={row.id} className="rule-b transition-colors hover:bg-secondary/60">
                {row.getVisibleCells().map((cell) => (
                  <td
                    key={cell.id}
                    className={`px-3 py-3 ${NUMERIC.has(cell.column.id) ? "text-right font-mono" : ""}`}
                  >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
            {visible.length === 0 && (
              <tr>
                <td colSpan={columns.length} className="py-16 text-center text-muted-foreground">
                  No candidates match — loosen the filters or clear the search.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
