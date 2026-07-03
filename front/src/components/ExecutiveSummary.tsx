type Props = {
  summary: any;
};

export default function ExecutiveSummary({ summary }: Props) {
  return (
    <div className="bg-white rounded-xl shadow p-6">
      <h2 className="text-2xl font-semibold mb-4">Executive Summary</h2>
      <p>
        <strong>Overall Risk Rating:</strong> {summary.overall_rating}
      </p>
      <p className="mt-4">{summary.executive_narrative}</p>
      <h3 className="mt-6 font-semibold">Key Findings</h3>
      <ul className="list-disc ml-6 mt-2">
        {summary.top_findings?.map((item: string, index: number) => (
          <li key={index}>{item}</li>
        ))}
      </ul>
      <h3 className="mt-6 font-semibold">Recommendation</h3>
      <p>{summary.recommendation}</p>
    </div>
  );
}