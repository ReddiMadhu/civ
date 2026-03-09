import { useState, useMemo } from "react"
import { cn } from "../../lib/utils"
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, Search } from "lucide-react"

function TableRoot({ className, children }) {
    return (
        <div className={cn("w-full overflow-auto rounded-lg border border-border", className)}>
            <table className="w-full text-sm">{children}</table>
        </div>
    )
}

function TableHeader({ children }) {
    return <thead className="border-b border-border bg-muted/60">{children}</thead>
}

function TableBody({ children }) {
    return <tbody className="divide-y divide-border">{children}</tbody>
}

function TableRow({ children, className }) {
    return <tr className={cn("transition-colors hover:bg-muted/40", className)}>{children}</tr>
}

function TableHead({ children, className, onClick, sorted }) {
    return (
        <th
            onClick={onClick}
            className={cn(
                "px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground whitespace-nowrap",
                onClick && "cursor-pointer select-none hover:text-foreground",
                className
            )}
        >
            <span className="flex items-center gap-1">
                {children}
                {sorted === "asc" && <span>↑</span>}
                {sorted === "desc" && <span>↓</span>}
            </span>
        </th>
    )
}

function TableCell({ children, className }) {
    return <td className={cn("px-4 py-3 text-foreground/90 whitespace-nowrap", className)}>{children}</td>
}

const PAGE_SIZES = [25, 50, 100]

export function DataTable({ columns, data, searchKey, title }) {
    const [page, setPage] = useState(1)
    const [pageSize, setPageSize] = useState(25)
    const [search, setSearch] = useState("")
    const [sort, setSort] = useState({ key: null, dir: "asc" })

    const filtered = useMemo(() => {
        if (!search) return data
        const q = search.toLowerCase()
        return data.filter(row =>
            searchKey ? String(row[searchKey]).toLowerCase().includes(q)
                : Object.values(row).some(v => String(v).toLowerCase().includes(q))
        )
    }, [data, search, searchKey])

    const sorted = useMemo(() => {
        if (!sort.key) return filtered
        return [...filtered].sort((a, b) => {
            const av = a[sort.key], bv = b[sort.key]
            const an = parseFloat(av), bn = parseFloat(bv)
            const cmp = isNaN(an) ? String(av).localeCompare(String(bv)) : an - bn
            return sort.dir === "asc" ? cmp : -cmp
        })
    }, [filtered, sort])

    const total = sorted.length
    const totalPages = Math.max(1, Math.ceil(total / pageSize))
    const safePage = Math.min(page, totalPages)
    const slice = sorted.slice((safePage - 1) * pageSize, safePage * pageSize)

    const handleSort = (key) => {
        setSort(s => s.key === key ? { key, dir: s.dir === "asc" ? "desc" : "asc" } : { key, dir: "asc" })
        setPage(1)
    }

    return (
        <div className="flex flex-col gap-4">
            {/* Controls */}
            <div className="flex flex-wrap items-center justify-between gap-3">
                {title && <h2 className="text-lg font-semibold text-foreground">{title}</h2>}
                <div className="relative">
                    <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
                    <input
                        value={search}
                        onChange={e => { setSearch(e.target.value); setPage(1) }}
                        placeholder="Search…"
                        className="pl-8 pr-3 py-1.5 text-sm rounded-lg bg-muted border border-border text-foreground placeholder-muted-foreground outline-none focus:ring-1 focus:ring-primary w-56"
                    />
                </div>
            </div>

            {/* Table */}
            <TableRoot>
                <TableHeader>
                    <tr>
                        {columns.map(col => (
                            <TableHead key={col.key} onClick={col.sortable !== false ? () => handleSort(col.key) : undefined}
                                sorted={sort.key === col.key ? sort.dir : undefined}>
                                {col.label}
                            </TableHead>
                        ))}
                    </tr>
                </TableHeader>
                <TableBody>
                    {slice.length === 0 ? (
                        <TableRow>
                            <td colSpan={columns.length} className="px-4 py-10 text-center text-muted-foreground">No results found</td>
                        </TableRow>
                    ) : slice.map((row, i) => (
                        <TableRow key={i}>
                            {columns.map(col => (
                                <TableCell key={col.key} className={col.className}>
                                    {col.render ? col.render(row[col.key], row) : row[col.key]}
                                </TableCell>
                            ))}
                        </TableRow>
                    ))}
                </TableBody>
            </TableRoot>

            {/* Pagination */}
            <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-muted-foreground">
                <span>{total.toLocaleString()} rows • Page {safePage} of {totalPages}</span>
                <div className="flex items-center gap-1">
                    <select value={pageSize} onChange={e => { setPageSize(+e.target.value); setPage(1) }}
                        className="text-xs bg-muted border border-border rounded px-2 py-1 text-foreground">
                        {PAGE_SIZES.map(s => <option key={s}>{s}</option>)}
                    </select>
                    {[
                        [<ChevronsLeft size={14} />, 1, safePage <= 1],
                        [<ChevronLeft size={14} />, safePage - 1, safePage <= 1],
                        [<ChevronRight size={14} />, safePage + 1, safePage >= totalPages],
                        [<ChevronsRight size={14} />, totalPages, safePage >= totalPages],
                    ].map(([icon, target, disabled], i) => (
                        <button key={i} onClick={() => setPage(target)} disabled={disabled}
                            className="rounded px-2 py-1 hover:bg-muted disabled:opacity-30 disabled:cursor-not-allowed">
                            {icon}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    )
}
