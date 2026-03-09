import { clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs) {
    return twMerge(clsx(inputs))
}

export function fmt(v, digits = 2) {
    if (v == null || isNaN(v)) return "—"
    return Number(v).toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits })
}

export function fmtPct(v) {
    return fmt(v * 100, 1) + "%"
}

export function fmtDollar(v) {
    if (v == null || isNaN(v)) return "—"
    const n = Number(v)
    if (Math.abs(n) >= 1e6) return "$" + fmt(n / 1e6, 2) + "M"
    if (Math.abs(n) >= 1e3) return "$" + fmt(n / 1e3, 1) + "K"
    return "$" + fmt(n, 2)
}

export const STATE_NAMES = {
    "12": "Florida",
    "48": "Texas",
    "06": "California",
    "36": "New York",
    "18": "Illinois",
    "26": "Michigan",
}
