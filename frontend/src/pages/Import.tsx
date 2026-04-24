import { useState } from 'react';
import apiClient from '../api/index';

type ImportResult = {
  imported: number;
  skipped: number;
  errors: string[];
};

function Uploader({ label, endpoint }: { label: string; endpoint: string }) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const form = new FormData();
      form.append('file', file);
      const { data } = await apiClient.post(endpoint, form);
      setResult(data);
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || 'Upload failed';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded shadow p-4">
      <h3 className="text-lg font-semibold mb-2">{label}</h3>
      <form onSubmit={onSubmit} className="space-y-3">
        <input
          type="file"
          accept=".csv"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="block w-full text-sm"
        />
        <button
          type="submit"
          disabled={!file || loading}
          className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
        >
          {loading ? 'Importing…' : 'Import CSV'}
        </button>
      </form>
      {error && <p className="text-red-600 text-sm mt-2">{error}</p>}
      {result && (
        <div className="text-sm mt-2">
          <p>
            Imported <strong>{result.imported}</strong>, Skipped <strong>{result.skipped}</strong>
          </p>
          {result.errors?.length ? (
            <details className="mt-1">
              <summary>Errors ({result.errors.length})</summary>
              <ul className="list-disc ml-5">
                {result.errors.map((e, i) => (
                  <li key={i} className="break-all">{e}</li>
                ))}
              </ul>
            </details>
          ) : null}
        </div>
      )}
    </div>
  );
}

export default function Import() {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Import Data</h2>
      <p className="text-sm text-gray-600">Upload CSV exports to import Expenses, Mileage, or Orders.</p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Uploader label="Import Expenses" endpoint="/expenses/import-file" />
        <Uploader label="Import Mileage" endpoint="/mileage/import-file" />
        <Uploader label="Import Orders" endpoint="/orders/import-file" />
      </div>
    </div>
  );
}

