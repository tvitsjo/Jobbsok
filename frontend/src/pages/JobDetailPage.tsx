import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getJob, toggleSave, dismissJob } from '../api/jobs';

export default function JobDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [dismissReason, setDismissReason] = useState('');
  const [showDismiss, setShowDismiss] = useState(false);

  const { data: result, isLoading } = useQuery({
    queryKey: ['job', id],
    queryFn: () => getJob(id!).then((r) => r.data),
    enabled: !!id,
  });

  const saveMutation = useMutation({
    mutationFn: () => toggleSave(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['job', id] });
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });

  const dismissMutation = useMutation({
    mutationFn: () => dismissJob(id!, dismissReason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      navigate('/jobs');
    },
  });

  if (isLoading) return <div className="max-w-3xl mx-auto p-6">Laster...</div>;
  if (!result) return <div className="max-w-3xl mx-auto p-6">Ikke funnet</div>;

  const job = result.job_listing;

  return (
    <div className="max-w-3xl mx-auto p-6">
      <button onClick={() => navigate('/jobs')} className="text-blue-600 hover:underline text-sm mb-4 block">
        &larr; Tilbake til jobber
      </button>

      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h1 className="text-2xl font-bold">{job.title}</h1>
            <p className="text-gray-600">{job.company_name ?? 'Ukjent firma'} — {job.location ?? 'Ukjent sted'}</p>
          </div>
          <span
            className={`px-4 py-2 rounded-full text-lg font-bold text-white ${
              result.relevance_score >= 0.7 ? 'bg-green-500' :
              result.relevance_score >= 0.5 ? 'bg-yellow-500' : 'bg-gray-400'
            }`}
          >
            {Math.round(result.relevance_score * 100)}%
          </span>
        </div>

        {result.llm_reasoning && (
          <div className="bg-blue-50 rounded-lg p-4 mb-4">
            <h3 className="text-sm font-semibold text-blue-800 mb-1">Hvorfor denne matchen?</h3>
            <p className="text-sm text-blue-700">{result.llm_reasoning}</p>
          </div>
        )}

        {job.description && (
          <div className="mb-6">
            <h3 className="font-semibold mb-2">Beskrivelse</h3>
            <div className="text-sm text-gray-700 whitespace-pre-wrap">{job.description}</div>
          </div>
        )}

        {job.salary_info && (
          <p className="text-sm mb-2"><span className="font-medium">Lonn:</span> {job.salary_info}</p>
        )}
        {job.job_type && (
          <p className="text-sm mb-2"><span className="font-medium">Type:</span> {job.job_type}</p>
        )}

        <div className="flex gap-3 mt-6">
          {job.url && (
            <a
              href={job.url}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
            >
              Se original annonse
            </a>
          )}
          <button
            onClick={() => saveMutation.mutate()}
            className={`px-6 py-2 rounded-lg border ${
              result.is_saved ? 'bg-yellow-50 border-yellow-400 text-yellow-700' : 'border-gray-300 hover:bg-gray-50'
            }`}
          >
            {result.is_saved ? 'Lagret &#9733;' : 'Lagre'}
          </button>
          <button
            onClick={() => setShowDismiss(!showDismiss)}
            className="px-6 py-2 rounded-lg border border-red-300 text-red-600 hover:bg-red-50"
          >
            Ikke aktuell
          </button>
        </div>

        {showDismiss && (
          <div className="mt-4 bg-red-50 rounded-lg p-4">
            <p className="text-sm font-medium text-red-800 mb-2">Hvorfor er denne jobben ikke aktuell?</p>
            <textarea
              value={dismissReason}
              onChange={(e) => setDismissReason(e.target.value)}
              placeholder="F.eks: For senior, feil bransje, dårlig lokasjon..."
              rows={3}
              className="w-full border rounded-lg px-4 py-2 focus:ring-2 focus:ring-red-500 outline-none"
            />
            <button
              onClick={() => dismissMutation.mutate()}
              disabled={!dismissReason.trim()}
              className="mt-2 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 disabled:opacity-50"
            >
              Bekreft avvisning
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
