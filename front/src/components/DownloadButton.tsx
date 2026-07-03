export default function DownloadButton() {
  return (
    <div className="mt-6">
      <a
        href="http://localhost:8000/download-report/"
        target="_blank"
        rel="noreferrer"
        className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
      >
        Download DOCX Report
      </a>
    </div>
  );
}