import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { getJobs, triggerSearch } from '../api/jobs';

export default function JobResultsPage() {
  const [minScore, setMinScore] = useState(0);
  const [savedOnly, setSavedOnly] = useState(false);
  const [searching, setSearching] = useState(false);

  const { data: jobs, isLoading } = useQuery({
    queryKey: ['jobs', { min_score: minScore / 100, saved_only: savedOnly }],
    queryFn: () => getJobs({ min_score: minScore / 100, saved_only: savedOnly, limit: 100 }).then((r) => r.data),
  });

  const handleSearch = async () => {
    setSearching(true);
    try { await triggerSearch(); } finally { setTimeout(() => setSearching(false), 3000); }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Jobbmatcher</h1>
        <button
          onClick={handleSearch} disabled={searching}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {searching ? 'Soker...' : 'Nytt sok'}
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6 flex items-center gap-6">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">Min. score:</label>
          <input
            type="range" min={0} max={100} value={minScore}
            onChange={(e) => setMinScore(Number(e.target.value))}
            className="w-32"
          />
          <span className="text-sm w-10">{minScore}%</span>
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={savedOnly} onChange={(e) => setSavedOnly(e.target.checked)} />
          Kun lagrede
        </label>
      </div>

      {isLoading && <p className="text-gray-500">Laster...</p>}

      {jobs && jobs.length === 0 && (
        <p className="text-gray-500">Ingen jobber funnet. Prov a kjore et sok!</p>
      )}

      <div className="space-y-3">
        {jobs?.map((result) => (
          <Link
            key={result.id}
            to={`/jobs/${result.id}`}
            className="block bg-white rounded-lg shadow p-4 hover:shadow-md transition"
          >
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <h3 className="font-medium text-lg">{result.job_listing.title}</h3>
                <p className="text-sm text-gray-500">
                  {result.job_listing.company_name ?? 'Ukjent firma'} — {result.job_listing.location ?? 'Ukjent sted'}
                </p>
                {result.llm_reasoning && (
                  <p className="text-sm text-gray-600 mt-1 line-clamp-2">{result.llm_reasoning}</p>
                )}
              </div>
              <div className="flex items-center gap-2 ml-4">
                {result.is_saved && <span className="text-yellow-500 text-lg">&#9733;</span>}
                <span
                  className={`px-3 py-1 rounded-full text-sm font-medium text-white ${
                    result.relevance_score >= 0.7 ? 'bg-green-500' :
                    result.relevance_score >= 0.5 ? 'bg-yellow-500' : 'bg-gray-400'
                  }`}
                >
                  {Math.round(result.relevance_score * 100)}%
                </span>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
