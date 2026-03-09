import { useMemo } from "react"
import { useData } from "../context/DataContext"
import { DataTable } from "../components/ui/DataTable"
import { Badge } from "../components/ui/Card"
import { fmtDollar } from "../lib/utils"

const COLUMNS = [
    { key: "FULLPOLICY_NB", label: "Policy #", sortable: false },
    { key: "POLICYEFFECTIVE_DT", label: "Eff Date" },
    {
        key: "POLICYRATEDSTATE_TP", label: "State",
        render: v => { const m = { "12": "FL", "48": "TX", "06": "CA", "36": "NY", "18": "IL", "26": "MI" }; return m[v] || v }
    },
    {
        key: "CREDITMODEL_CD", label: "Credit",
        render: v => <Badge variant={v === "INTRNL06" ? "success" : v === "ASSIST03" ? "destructive" : "muted"}>{v === "INTRNL06" ? "Elite" : v === "ASSIST03" ? "Subprime" : "Avg"}</Badge>
    },
    { key: "DIRECTWRITTENPREMIUM_AM", label: "Premium", render: v => fmtDollar(v) },
    { key: "NETLOSS_PAID_AM", label: "Net Loss", render: v => fmtDollar(v) },
    { key: "GROSSLOSSPAIO_AM", label: "Gross Loss", render: v => fmtDollar(v) },
    { key: "CLAIMCOUNT_CT", label: "Claims" },
    { key: "MERITPOINT_CT", label: "Merit" },
    { key: "HOME_AGE_YR", label: "Home Age" },
    { key: "HAZARD_SCORE", label: "Hazard" },
    {
        key: "POLICY_RENEWED_FLAG", label: "Renewed",
        render: v => <Badge variant={v === "True" || v === "1" ? "success" : "destructive"}>{v === "True" || v === "1" ? "Yes" : "No"}</Badge>
    },
    {
        key: "DelequencyFlag", label: "Delq",
        render: v => v === "True" || v === "true"
            ? <Badge variant="destructive">Yes</Badge>
            : <Badge variant="muted">No</Badge>
    },
    { key: "_clv", label: "CLV ($)", render: v => <span className={+v >= 0 ? "text-emerald-600 font-semibold" : "text-rose-600 font-semibold"}>{fmtDollar(v)}</span> },
]

export default function DataTablePage() {
    const { data, loading } = useData()

    if (loading) return <div className="flex items-center justify-center h-64 text-muted-foreground">Loading data…</div>

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-foreground">Policy Data</h1>
                <p className="text-muted-foreground text-sm mt-1">Browse, search and sort all 50,000 insurance policies</p>
            </div>
            <DataTable
                columns={COLUMNS}
                data={data}
                searchKey="FULLPOLICY_NB"
                title=""
            />
        </div>
    )
}
