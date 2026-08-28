"""Analysis report generation service (HTML and JSON)."""

import json
from pathlib import Path

from app.config import settings
from app.schemas.responses import AnalysisResponse


class ReportService:
    """Generates structured and printable audit reports for satellite analyses."""

    def __init__(self, reports_dir: Path | None = None):
        self.reports_dir = reports_dir or settings.REPORTS_DIR
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def save_report(self, response: AnalysisResponse) -> Path:
        """Save analysis response as JSON audit report."""
        report_id = response.report_id or "latest"
        json_path = self.reports_dir / f"report_{report_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(response.model_dump(), f, indent=2)
        return json_path

    def get_report(self, report_id: str) -> dict | None:
        """Retrieve stored report by ID."""
        json_path = self.reports_dir / f"report_{report_id}.json"
        if not json_path.exists():
            return None
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def generate_html_report(self, response: AnalysisResponse) -> str:
        """Generate a self-contained printable HTML audit report."""
        steps_html = "".join(
            f"""
            <tr class="border-b border-slate-700">
                <td class="py-2 px-3 font-mono text-xs text-cyan-400">{s.step}</td>
                <td class="py-2 px-3 text-xs">{s.tool or '-'}</td>
                <td class="py-2 px-3 text-xs text-slate-300">{s.implementation or '-'}</td>
                <td class="py-2 px-3 text-xs text-right font-mono">{s.duration_ms:.1f}ms</td>
                <td class="py-2 px-3 text-xs text-center"><span class="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 font-semibold">{s.status.value.upper()}</span></td>
            </tr>
            """
            for s in response.execution_trace
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>TENALI AI Analysis Report - {response.report_id}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 p-8 font-sans">
    <div class="max-w-4xl mx-auto bg-slate-900 border border-slate-800 rounded-xl p-8 shadow-2xl">
        <div class="flex justify-between items-start border-b border-slate-800 pb-6 mb-6">
            <div>
                <h1 class="text-3xl font-black tracking-tight text-white flex items-center gap-3">
                    <span class="text-cyan-400">TENALI</span> AI
                </h1>
                <p class="text-sm text-slate-400">SIH 26167 Remote Sensing Vision-Language Assistant</p>
            </div>
            <div class="text-right">
                <span class="px-3 py-1 bg-cyan-950 border border-cyan-800 text-cyan-400 rounded-full text-xs font-bold">REPORT #{response.report_id}</span>
                <p class="text-xs text-slate-500 mt-1">Smart India Hackathon 2026</p>
            </div>
        </div>

        <div class="grid grid-cols-2 gap-4 mb-6">
            <div class="bg-slate-950/60 p-4 rounded-lg border border-slate-800/80">
                <p class="text-xs text-slate-400 uppercase font-semibold">User Query</p>
                <p class="text-base font-medium text-white mt-1">"{response.inputs.get('query')}"</p>
            </div>
            <div class="bg-slate-950/60 p-4 rounded-lg border border-slate-800/80">
                <p class="text-xs text-slate-400 uppercase font-semibold">Classified Task & Mode</p>
                <p class="text-base font-medium text-cyan-300 mt-1">{response.task} ({response.inputs.get('mode')})</p>
            </div>
        </div>

        <div class="bg-gradient-to-br from-slate-950 to-slate-900 p-6 rounded-xl border border-cyan-900/40 mb-6">
            <h2 class="text-xs font-bold uppercase tracking-wider text-cyan-400 mb-2">Synthesized Grounded Answer</h2>
            <p class="text-lg text-slate-100 leading-relaxed">{response.answer}</p>
            <div class="flex gap-4 mt-4 text-xs text-slate-400 border-t border-slate-800/80 pt-3">
                <div>Confidence Estimate: <strong class="text-white">{response.confidence_estimate:.2f} ({response.confidence_level})</strong></div>
                <div>Execution Mode: <strong class="text-white">{response.execution_mode}</strong></div>
            </div>
        </div>

        <div class="mb-6">
            <h2 class="text-sm font-bold uppercase tracking-wider text-slate-400 mb-3">Auditable Execution Trace</h2>
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="border-b border-slate-800 text-xs text-slate-400 uppercase">
                            <th class="py-2 px-3">Stage</th>
                            <th class="py-2 px-3">Tool</th>
                            <th class="py-2 px-3">Adapter / Engine</th>
                            <th class="py-2 px-3 text-right">Latency</th>
                            <th class="py-2 px-3 text-center">Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {steps_html}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="border-t border-slate-800 pt-4 text-xs text-slate-500 flex justify-between items-center">
            <p><strong>Disclaimer:</strong> {response.disclaimer}</p>
            <button onclick="window.print()" class="px-4 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white font-medium rounded text-xs">Print / PDF</button>
        </div>
    </div>
</body>
</html>
"""


report_service = ReportService()
