import { useMemo, useState } from "react"
import { useData } from "../context/DataContext"
import { Card, CardHeader, CardTitle, CardContent, KPICard } from "../components/ui/Card"
import { DataTable } from "../components/ui/DataTable"
import { Badge } from "../components/ui/Card"
import { fmtDollar, STATE_NAMES } from "../lib/utils"
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
    ScatterChart, Scatter, Cell, ReferenceLine,
} from "recharts"
import { TrendingUp, TrendingDown, DollarSign, Activity } from "lucide-react"

const TT_STYLE = { backgroundColor: "#1e2535", border: "1px solid #2d3a52", borderRadius: 8, color: "#e2e8f0", fontSize: 12 }
const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#a855f7", "#06b6d4"]

export default function CLVPage() {
    const { data, loading } = useData()
    const [segment, setSegment] = useState("state")

    const stats = useMemo(() => {
        if (!data.length) return null

        const clvs = data.map(r => r._clv)
        const avgCLV = clvs.reduce((a, b) => a + b, 0) / clvs.length
        const totalCLV = clvs.reduce((a, b) => a + b, 0)
        const posCount = clvs.filter(v => v > 0).length
        const negCount = clvs.filter(v => v < 0).length
        const maxCLV = Math.max(...clvs)
        const minCLV = Math.min(...clvs)

        // CLV by state
        const stateAgg = {}
        data.forEach(r => {
            const s = STATE_NAMES[r.POLICYRATEDSTATE_TP] || r.POLICYRATEDSTATE_TP
            if (!stateAgg[s]) stateAgg[s] = { sum: 0, cnt: 0 }
            stateAgg[s].sum += r._clv; stateAgg[s].cnt++
        })
        const clvByState = Object.entries(stateAgg).map(([state, v]) => ({ state, avgCLV: +(v.sum / v.cnt).toFixed(2), count: v.cnt })).sort((a, b) => b.avgCLV - a.avgCLV)

        // CLV by credit tier
        const creditMap = { "INTRNL06": "Elite", "ASSIST01": "Average", "ASSIST03": "Subprime" }
        const creditAgg = {}
        data.forEach(r => {
            const c = creditMap[r.CREDITMODEL_CD] || r.CREDITMODEL_CD
            if (!creditAgg[c]) creditAgg[c] = { sum: 0, cnt: 0 }
            creditAgg[c].sum += r._clv; creditAgg[c].cnt++
        })
        const clvByCredit = Object.entries(creditAgg).map(([credit, v]) => ({ credit, avgCLV: +(v.sum / v.cnt).toFixed(2) })).sort((a, b) => b.avgCLV - a.avgCLV)

        // CLV by channel
        const chanAgg = {}
        data.forEach(r => {
            const c = r.AGENT_CHANNEL
            if (!chanAgg[c]) chanAgg[c] = { sum: 0, cnt: 0 }
            chanAgg[c].sum += r._clv; chanAgg[c].cnt++
        })
        const clvByChannel = Object.entries(chanAgg).map(([channel, v]) => ({ channel, avgCLV: +(v.sum / v.cnt).toFixed(2) }))

        // CLV distribution buckets
        const bmin = -2000, bmax = 4000, step = 500
        const buckets = []
        for (let lo = bmin; lo < bmax; lo += step) {
            const cnt = clvs.filter(v => v >= lo && v < lo + step).length
            buckets.push({ range: `$${lo / 1000 >= 0 ? '' : '-'}${Math.abs(lo / 1000).toFixed(0)}K`, count: cnt, lo })
        }

        // Top 10 by CLV
        const top10 = [...data].sort((a, b) => b._clv - a._clv).slice(0, 10)
        const bot10 = [...data].sort((a, b) => a._clv - b._clv).slice(0, 10)

        return { avgCLV, totalCLV, posCount, negCount, maxCLV, minCLV, clvByState, clvByCredit, clvByChannel, buckets, top10, bot10, total: data.length }
    }, [data])

    if (loading || !stats) {
        return <div className="flex items-center justify-center h-64 text-muted-foreground">Loading data…</div>
    }

    const tableData = segment === "state" ? stats.clvByState.map((r, i) => ({ rank: i + 1, segment: r.state, avgCLV: r.avgCLV, count: r.count }))
        : segment === "credit" ? stats.clvByCredit.map((r, i) => ({ rank: i + 1, segment: r.credit, avgCLV: r.avgCLV, count: "—" }))
            : stats.clvByChannel.map((r, i) => ({ rank: i + 1, segment: r.channel, avgCLV: r.avgCLV, count: "—" }))

    const segmentCols = [
        { key: "rank", label: "#", sortable: false },
        { key: "segment", label: "Segment" },
        { key: "avgCLV", label: "Avg CLV ($)", render: v => <span className={+v >= 0 ? "text-emerald-400" : "text-red-400"}>{fmtDollar(v)}</span> },
        { key: "count", label: "Policies" },
    ]

    const topCols = [
        { key: "FULLPOLICY_NB", label: "Policy #", sortable: false },
        { key: "POLICYRATEDSTATE_TP", label: "State", render: v => STATE_NAMES[v] || v },
        { key: "CREDITMODEL_CD", label: "Credit", render: v => { const m = { "INTRNL06": "Elite", "ASSIST01": "Avg", "ASSIST03": "Subprime" }; return <Badge variant={v === "INTRNL06" ? "success" : v === "ASSIST03" ? "destructive" : "muted"}>{m[v] || v}</Badge> } },
        { key: "DIRECTWRITTENPREMIUM_AM", label: "Premium", render: v => fmtDollar(v) },
        { key: "NETLOSS_PAID_AM", label: "Net Loss", render: v => fmtDollar(v) },
        { key: "_clv", label: "CLV ($)", render: v => <span className={+v >= 0 ? "text-emerald-400 font-bold" : "text-red-400 font-bold"}>{fmtDollar(v)}</span> },
    ]

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-foreground">CLV Analysis</h1>
                <p className="text-muted-foreground text-sm mt-1">
                    Discounted CLV = <code className="text-primary text-xs">(Premium − Comm − Admin − NetLoss) × Renewed / (1 + 0.08)</code>
                </p>
            </div>

            {/* KPIs */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <KPICard title="Avg CLV" value={fmtDollar(stats.avgCLV)} subtitle="Per policy" icon={TrendingUp} color="purple" />
                <KPICard title="Total Portfolio CLV" value={fmtDollar(stats.totalCLV)} subtitle="Sum of all policies" icon={DollarSign} color="blue" />
                <KPICard title="Profitable Policies" value={(stats.posCount / stats.total * 100).toFixed(1) + "%"} subtitle={`${stats.posCount.toLocaleString()} policies`} icon={TrendingUp} color="green" />
                <KPICard title="Loss-Making Policies" value={(stats.negCount / stats.total * 100).toFixed(1) + "%"} subtitle={`${stats.negCount.toLocaleString()} policies`} icon={TrendingDown} color="red" />
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">

                {/* CLV Distribution */}
                <Card>
                    <CardHeader><CardTitle>CLV Distribution</CardTitle></CardHeader>
                    <CardContent>
                        <ResponsiveContainer width="100%" height={220}>
                            <BarChart data={stats.buckets} barSize={20}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#2d3a52" />
                                <XAxis dataKey="range" tick={{ fill: "#94a3b8", fontSize: 10 }} />
                                <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
                                <Tooltip contentStyle={TT_STYLE} formatter={v => [v.toLocaleString(), "Policies"]} />
                                <ReferenceLine x={0} stroke="#ef4444" strokeDasharray="4 4" />
                                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                                    {stats.buckets.map((b, i) => <Cell key={i} fill={b.lo >= 0 ? "#10b981" : "#ef4444"} />)}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>

                {/* CLV by State Bar */}
                <Card>
                    <CardHeader><CardTitle>Avg CLV by State</CardTitle></CardHeader>
                    <CardContent>
                        <ResponsiveContainer width="100%" height={220}>
                            <BarChart data={stats.clvByState} barSize={28}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#2d3a52" />
                                <XAxis dataKey="state" tick={{ fill: "#94a3b8", fontSize: 10 }} />
                                <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} tickFormatter={v => "$" + Math.round(v)} />
                                <Tooltip contentStyle={TT_STYLE} formatter={v => ["$" + v.toLocaleString(), "Avg CLV"]} />
                                <Bar dataKey="avgCLV" radius={[4, 4, 0, 0]}>
                                    {stats.clvByState.map((_, i) => <Cell key={i} fill={["#3b82f6", "#10b981", "#f59e0b", "#a855f7", "#06b6d4", "#ef4444"][i % 6]} />)}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>

                {/* CLV by Credit Tier */}
                <Card>
                    <CardHeader><CardTitle>Avg CLV by Credit Tier</CardTitle></CardHeader>
                    <CardContent>
                        <ResponsiveContainer width="100%" height={220}>
                            <BarChart data={stats.clvByCredit} barSize={50}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#2d3a52" />
                                <XAxis dataKey="credit" tick={{ fill: "#94a3b8", fontSize: 12 }} />
                                <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} tickFormatter={v => "$" + Math.round(v)} />
                                <Tooltip contentStyle={TT_STYLE} formatter={v => ["$" + v.toLocaleString(), "Avg CLV"]} />
                                <Bar dataKey="avgCLV" radius={[4, 4, 0, 0]}>
                                    {stats.clvByCredit.map((_, i) => <Cell key={i} fill={["#3b82f6", "#f59e0b", "#ef4444"][i]} />)}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>

                {/* CLV by Channel */}
                <Card>
                    <CardHeader><CardTitle>Avg CLV by Agent Channel</CardTitle></CardHeader>
                    <CardContent>
                        <ResponsiveContainer width="100%" height={220}>
                            <BarChart data={stats.clvByChannel} barSize={50}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#2d3a52" />
                                <XAxis dataKey="channel" tick={{ fill: "#94a3b8", fontSize: 12 }} />
                                <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} tickFormatter={v => "$" + Math.round(v)} />
                                <Tooltip contentStyle={TT_STYLE} formatter={v => ["$" + v.toLocaleString(), "Avg CLV"]} />
                                <Bar dataKey="avgCLV" radius={[4, 4, 0, 0]}>
                                    {stats.clvByChannel.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>
            </div>

            {/* Segment table */}
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between flex-wrap gap-3">
                        <CardTitle>CLV by Segment</CardTitle>
                        <div className="flex gap-2">
                            {[["state", "By State"], ["credit", "By Credit"], ["channel", "By Channel"]].map(([v, l]) => (
                                <button key={v} onClick={() => setSegment(v)}
                                    className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${segment === v ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:text-foreground"}`}>
                                    {l}
                                </button>
                            ))}
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    <DataTable columns={segmentCols} data={tableData} />
                </CardContent>
            </Card>

            {/* Top / Bottom 10 tables */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                <Card>
                    <CardHeader><CardTitle>🏆 Top 10 Highest CLV Policies</CardTitle></CardHeader>
                    <CardContent>
                        <DataTable columns={topCols} data={stats.top10} />
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader><CardTitle>⚠️ Bottom 10 Lowest CLV Policies</CardTitle></CardHeader>
                    <CardContent>
                        <DataTable columns={topCols} data={stats.bot10} />
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
