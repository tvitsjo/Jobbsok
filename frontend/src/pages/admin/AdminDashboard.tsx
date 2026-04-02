import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getConfig, updateConfig, getSources, updateSource, getStats, triggerFetch } from '../../api/admin';

export default function AdminDashboard() {
  const queryClient = useQueryClient();
  const [modelValue, setModelValue] = useState('');
  const [intervalValue, setIntervalValue] = useState('');
  const [configLoaded, setConfigLoaded] = useState(false);

  const { data: stats } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: () => getStats().then((r) => r.data),
  });

  const { data: configs } = useQuery({
    queryKey: ['admin-config'],
    queryFn: () => getConfig().then((r) => {
      if (!configLoaded) {
        const model = r.data.find((c) => c.key === 'openrouter_model');
        const interval = r.data.find((c) => c.key === 'search_interval_hours');
        if (model) setModelValue(model.value);
        if (interval) setIntervalValue(interval.value);
        setConfigLoaded(true);
      }
      return r.data;
    }),
  });

  const { data: sources } = useQuery({
    queryKey: ['admin-sources'],
    queryFn: () => getSources().then((r) => r.data),
  });

  const saveConfig = useMutation({
    mutationFn: async () => {
      await updateConfig('openrouter_model', modelValue);
      await updateConfig('search_interval_hours', intervalValue);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-config'] }),
  });

  const toggleSource = useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) =>
      updateSource(id, { is_enabled: enabled }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-sources'] }),
  });

  const fetchMutation = useMutation({ mutationFn: triggerFetch });

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Admin</h1>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <p className="text-2xl font-bold text-blue-600">{stats.total_users}</p>
            <p className="text-sm text-gray-500">Brukere</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <p className="text-2xl font-bold text-green-600">{stats.total_jobs}</p>
            <p className="text-sm text-gray-500">Jobber</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <p className="text-2xl font-bold text-purple-600">{stats.total_search_runs}</p>
            <p className="text-sm text-gray-500">Sokerunder</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <p className="text-2xl font-bold text-yellow-600">{stats.total_matches}</p>
            <p className="text-sm text-gray-500">Matcher</p>
          </div>
        </div>
      )}

      {/* Model Config */}
      <section className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">LLM-konfigurasjon</h2>
        <div className="space-y-3">
          <div>
            <label className="text-sm font-medium text-gray-700">OpenRouter-modell (fritekst)</label>
            <input
              type="text" value={modelValue} onChange={(e) => setModelValue(e.target.value)}
              placeholder="anthropic/claude-sonnet-4"
              className="w-full border rounded-lg px-4 py-2 mt-1 focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700">Sokeintervall (timer)</label>
            <input
              type="number" value={intervalValue} onChange={(e) => setIntervalValue(e.target.value)}
              min={1} max={168}
              className="w-full border rounded-lg px-4 py-2 mt-1 focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
          <button
            onClick={() => saveConfig.mutate()}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
          >
            Lagre konfigurasjon
          </button>
        </div>
      </section>

      {/* Job Sources */}
      <section className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">Jobbkilder</h2>
          <button
            onClick={() => fetchMutation.mutate()}
            disabled={fetchMutation.isPending}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50 text-sm"
          >
            {fetchMutation.isPending ? 'Henter...' : 'Hent jobber na'}
          </button>
        </div>
        <div className="space-y-3">
          {sources?.map((source) => (
            <div key={source.id} className="flex items-center justify-between border rounded-lg p-4">
              <div>
                <p className="font-medium">{source.display_name}</p>
                <p className="text-sm text-gray-500">
                  Sist hentet: {source.last_fetched_at ? new Date(source.last_fetched_at).toLocaleString('nb-NO') : 'Aldri'}
                </p>
              </div>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={source.is_enabled}
                  onChange={(e) => toggleSource.mutate({ id: source.id, enabled: e.target.checked })}
                  className="w-4 h-4"
                />
                <span className="text-sm">{source.is_enabled ? 'Aktiv' : 'Inaktiv'}</span>
              </label>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
