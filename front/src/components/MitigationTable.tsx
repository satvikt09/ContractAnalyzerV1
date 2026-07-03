type Props = {
  rows: any[];
};

export default function MitigationTable({ rows }: Props) {
  return (
    <div className="bg-white rounded-2xl shadow p-6 mt-6 overflow-auto">
      <h2 className="text-2xl font-semibold mb-4">Mitigation Strategy Results</h2>
      <table className="min-w-full border-collapse">
        <thead>
          <tr className="bg-gray-100">
            <th className="border p-3">Clause</th>
            <th className="border p-3">Risk</th>
            <th className="border p-3">Mitigation Recommendation</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              <td className="border p-3">{row.clause}</td>
              <td className="border p-3">{row.risk}</td>
              <td className="border p-3">{row.mitigation}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}