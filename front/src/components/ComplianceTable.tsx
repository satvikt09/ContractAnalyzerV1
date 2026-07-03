type Props = {
  rows: any[];
  config: any;
};

export default function ComplianceTable({ rows, config }: Props) {
  return (
    <div className="bg-white rounded-2xl shadow p-6 mt-6 overflow-auto">
      <h2 className="text-2xl font-semibold mb-4">Compliance Check Results</h2>
      <table className="min-w-full border-collapse">
        <thead>
          <tr className="bg-gray-100">
            <th className="border p-3">Clause</th>
            <th className="border p-3">Requirement</th>
            {config?.showClauseSummaryColumn && (
              <th className="border p-3">Summary of Key Details</th>
            )}
            {config?.showStatusColumn && (
              <th className="border p-3">Status</th>
            )}
            <th className="border p-3">Evidence</th>
            <th className="border p-3">Remarks</th>
            <th className="border p-3">Confidence</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              <td className="border p-3">{row.clause}</td>
              <td className="border p-3">{row.requirement}</td>
              {config?.showClauseSummaryColumn && (
                <td className="border p-3">{row.clause_summary}</td>
              )}
              {config?.showStatusColumn && (
                <td className="border p-3">
                  {row.status === "Met" ? (
                    <span className="text-green-700 font-semibold">✓ Met</span>
                  ) : row.status === "Partially Met" ? (
                    <span className="text-yellow-600 font-semibold">⚠ Partially Met</span>
                  ) : (
                    <span className="text-red-700 font-semibold">✕ Not Met</span>
                  )}
                </td>
              )}
              <td className="border p-3">{row.evidence}</td>
              <td className="border p-3">{row.remarks}</td>
              <td className="border p-3">{row.confidence}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}