import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getPreferences, createPreference, deletePreference } from '../api/jobs';

export default function PreferencesPage() {
  const queryClient = useQueryClient();
  const [titles, setTitles] = useState('');
  const [locations, setLocations] = useState('');
  const [keywords, setKeywords] = useState('');
  const [excludeKeywords, setExcludeKeywords] = useState('');

  const { data: preferences } = useQuery({
    queryKey: ['preferences'],
    queryFn: () => getPreferences().then((r) => r.data),
  });

  const addPref = useMutation({
    mutationFn: () =>
      createPreference({
        job_titles: titles.split(',').map((s) => s.trim()).filter(Boolean),
        locations: locations.split(',').map((s) => s.trim()).filter(Boolean),
        keywords: keywords.split(',').map((s) => s.trim()).filter(Boolean),
        exclude_keywords: excludeKeywords.split(',').map((s) => s.trim()).filter(Boolean),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['preferences'] });
      setTitles('');
      setLocations('');
      setKeywords('');
      setExcludeKeywords('');
    },
  });

  const removePref = useMutation({
    mutationFn: (id: string) => deletePreference(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['preferences'] }),
  });

  return (
    <div className="max-w-3xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Jobbpreferanser</h1>

      {/* Add new */}
      <section className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Legg til preferanse</h2>
        <div className="space-y-3">
          <div>
            <label className="text-sm font-medium text-gray-700">Stillingstitler (kommaseparert)</label>
            <input
              type="text" value={titles} onChange={(e) => setTitles(e.target.value)}
              placeholder="Utvikler, Backend Developer, Systemutvikler"
              className="w-full border rounded-lg px-4 py-2 mt-1 focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700">Steder (kommaseparert)</label>
            <input
              type="text" value={locations} onChange={(e) => setLocations(e.target.value)}
              placeholder="Oslo, Bergen, Remote"
              className="w-full border rounded-lg px-4 py-2 mt-1 focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700">Nokkelord (kommaseparert)</label>
            <input
              type="text" value={keywords} onChange={(e) => setKeywords(e.target.value)}
              placeholder="Python, FastAPI, React"
              className="w-full border rounded-lg px-4 py-2 mt-1 focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700">Ekskluder nokkelord (kommaseparert)</label>
            <input
              type="text" value={excludeKeywords} onChange={(e) => setExcludeKeywords(e.target.value)}
              placeholder="Senior, Lead, Manager"
              className="w-full border rounded-lg px-4 py-2 mt-1 focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
          <button
            onClick={() => addPref.mutate()}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
          >
            Legg til
          </button>
        </div>
      </section>

      {/* Existing preferences */}
      <section>
        <h2 className="text-lg font-semibold mb-4">Dine preferanser</h2>
        {!preferences?.length && <p className="text-gray-500">Ingen preferanser lagt til enna.</p>}
        <div className="space-y-3">
          {preferences?.map((pref) => (
            <div key={pref.id} className="bg-white rounded-lg shadow p-4">
              <div className="flex justify-between items-start">
                <div>
                  {pref.job_titles.length > 0 && (
                    <p className="text-sm"><span className="font-medium">Titler:</span> {pref.job_titles.join(', ')}</p>
                  )}
                  {pref.locations.length > 0 && (
                    <p className="text-sm"><span className="font-medium">Steder:</span> {pref.locations.join(', ')}</p>
                  )}
                  {pref.keywords.length > 0 && (
                    <p className="text-sm"><span className="font-medium">Nokkelord:</span> {pref.keywords.join(', ')}</p>
                  )}
                  {pref.exclude_keywords.length > 0 && (
                    <p className="text-sm text-red-600"><span className="font-medium">Ekskluderer:</span> {pref.exclude_keywords.join(', ')}</p>
                  )}
                </div>
                <button
                  onClick={() => removePref.mutate(pref.id)}
                  className="text-red-500 hover:text-red-700 text-sm"
                >
                  Slett
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
