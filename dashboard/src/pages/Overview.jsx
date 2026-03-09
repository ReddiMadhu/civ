import { useMemo } from "react"
import { useData } from "../context/DataContext"
import { KPICard } from "../components/ui/Card"
import { fmtDollar, fmtPct, STATE_NAMES } from "../lib/utils"
import { DollarSign, Shield, Activity, TrendingUp, Users, AlertTriangle } from "lucide-react"

export default function Overview() {
    const { data, loading } = useData()

    const stats = useMemo(() => {
        if (!data.length) return null
        const n = data.length
        const avgPrem = data.reduce((s, r) => s + (+r.DIRECTWRITTENPREMIUM_AM || 0), 0) / n
        const totalPrem = data.reduce((s, r) => s + (+r.DIRECTWRITTENPREMIUM_AM || 0), 0)
        const totalLoss = data.reduce((s, r) => s + (+r.NETLOSS_PAID_AM || 0), 0)
        const totalEarn = data.reduce((s, r) => s + (+r.EARNEDPREMIUM_AM || 0), 0)
        const lossRatio = totalLoss / totalEarn
        const claimFreq = data.filter(r => +r.CLAIMCOUNT_CT > 0).length / n
        const renewRate = data.filter(r => r.POLICY_RENEWED_FLAG === "True" || r.POLICY_RENEWED_FLAG === "1").length / n
        const delqRate = data.filter(r => r.DelequencyFlag === "True" || r.DelequencyFlag === "true").length / n
        const avgCLV = data.reduce((s, r) => s + (r._clv || 0), 0) / n
        const totalCLV = data.reduce((s, r) => s + (r._clv || 0), 0)
        return { n, avgPrem, totalPrem, lossRatio, claimFreq, renewRate, delqRate, avgCLV, totalCLV }
    }, [data])

    if (loading || !stats) {
        return <div className="flex items-center justify-center h-64 text-muted-foreground">Loading data…</div>
    }

    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-2xl font-bold text-foreground">Portfolio Overview</h1>
                <p className="text-muted-foreground text-sm mt-1">Key performance indicators across {stats.n.toLocaleString()} policies</p>
            </div>

            {/* KPI Grid */}
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                <KPICard title="Avg Annual Premium" value={fmtDollar(stats.avgPrem)} subtitle="Per policy" icon={DollarSign} color="blue" />
                <KPICard title="Loss Ratio" value={fmtPct(stats.lossRatio)} subtitle="Net loss / earned premium" icon={Shield} color={stats.lossRatio > 0.75 ? "red" : "green"} />
                <KPICard title="Claim Frequency" value={fmtPct(stats.claimFreq)} subtitle="Policies with ≥1 claim" icon={Activity} color="amber" />
                <KPICard title="Renewal Rate" value={fmtPct(stats.renewRate)} subtitle="Policy retention" icon={Users} color="green" />
                <KPICard title="Delinquency Rate" value={fmtPct(stats.delqRate)} subtitle="Payment defaults" icon={AlertTriangle} color="red" />
                <KPICard title="Avg CLV" value={fmtDollar(stats.avgCLV)} subtitle="1-period discounted" icon={TrendingUp} color="purple" />
            </div>

            {/* Portfolio totals */}
            <div className="rounded-xl border border-border bg-card p-6">
                <h2 className="text-base font-semibold text-foreground mb-4">Portfolio Totals</h2>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
                    {[
                        ["Total Written Premium", fmtDollar(stats.totalPrem)],
                        ["Total Earned Premium", fmtDollar(stats.totalPrem * 0.925)],
                        ["Total Net Loss", fmtDollar(data.reduce((s, r) => s + (+r.NETLOSS_PAID_AM || 0), 0))],
                        ["Total Gross Loss", fmtDollar(data.reduce((s, r) => s + (+r.GROSSLOSSPAIO_AM || 0), 0))],
                        ["Total Portfolio CLV", fmtDollar(stats.totalCLV)],
                        ["Total Policies", stats.n.toLocaleString()],
                    ].map(([l, v]) => (
                        <div key={l}>
                            <p className="text-xs text-muted-foreground">{l}</p>
                            <p className="text-xl font-bold text-foreground mt-0.5">{v}</p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}
