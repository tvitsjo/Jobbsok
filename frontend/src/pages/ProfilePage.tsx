import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getProfile, updateProfile, uploadCV, uploadLinkedIn, triggerExtraction } from '../api/profile';
import { updateNotificationSettings } from '../api/jobs';
import { getMe } from '../api/auth';

export default function ProfilePage() {
  const queryClient = useQueryClient();
  const [freeText, setFreeText] = useState('');
  const [emails, setEmails] = useState('');
  const [textLoaded, setTextLoaded] = useState(false);

  const { data: profile } = useQuery({
    queryKey: ['profile'],
    queryFn: () => getProfile().then((r) => {
      if (!textLoaded) {
        setFreeText(r.data.free_text || '');
        setTextLoaded(true);
      }
      return r.data;
    }),
  });

  const { data: user } = useQuery({
    queryKey: ['me'],
    queryFn: () => getMe().then((r) => {
      if (!emails) setEmails((r.data.notification_emails || []).join(', '));
      return r.data;
    }),
  });

  const saveFreeText = useMutation({
    mutationFn: () => updateProfile({ free_text: freeText }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['profile'] }),
  });

  const saveEmails = useMutation({
    mutationFn: () => updateNotificationSettings(
      emails.split(',').map((e) => e.trim()).filter(Boolean)
    ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['me'] }),
  });

  const handleCVUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      await uploadCV(file);
      queryClient.invalidateQueries({ queryKey: ['profile'] });
    }
  };

  const handleLinkedInUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      await uploadLinkedIn(file);
      queryClient.invalidateQueries({ queryKey: ['profile'] });
    }
  };

  const handleReExtract = async () => {
    await triggerExtraction();
    queryClient.invalidateQueries({ queryKey: ['profile'] });
  };

  return (
    <div className="max-w-3xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Min profil</h1>

      {/* Free text */}
      <section className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-3">Om meg (fritekst)</h2>
        <textarea
          value={freeText}
          onChange={(e) => setFreeText(e.target.value)}
          rows={6}
          placeholder="Beskriv deg selv, din erfaring, hva du ser etter..."
          className="w-full border rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
        />
        <button
          onClick={() => saveFreeText.mutate()}
          className="mt-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm"
        >
          Lagre
        </button>
      </section>

      {/* CV Upload */}
      <section className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-3">CV (PDF)</h2>
        {profile?.cv_file_path && <p className="text-sm text-green-600 mb-2">CV lastet opp</p>}
        <input type="file" accept=".pdf" onChange={handleCVUpload} className="text-sm" />
      </section>

      {/* LinkedIn Screenshot */}
      <section className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-3">LinkedIn-skjermbilde</h2>
        {profile?.linkedin_image_path && <p className="text-sm text-green-600 mb-2">Bilde lastet opp</p>}
        <input type="file" accept="image/*" onChange={handleLinkedInUpload} className="text-sm" />
      </section>

      {/* Extraction Status */}
      <section className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-3">Analysert profil</h2>
        <p className="text-sm mb-2">
          Status:{' '}
          <span className={`font-medium ${
            profile?.extraction_status === 'completed' ? 'text-green-600' :
            profile?.extraction_status === 'processing' ? 'text-yellow-600' : 'text-gray-500'
          }`}>
            {profile?.extraction_status === 'completed' ? 'Ferdig' :
             profile?.extraction_status === 'processing' ? 'Analyserer...' : 'Venter'}
          </span>
        </p>
        {profile?.summary && (
          <div className="bg-gray-50 rounded p-4 mb-3">
            <h3 className="text-sm font-medium mb-1">Oppsummering</h3>
            <p className="text-sm text-gray-700">{profile.summary}</p>
          </div>
        )}
        {profile?.extracted_skills && (
          <div className="bg-gray-50 rounded p-4 mb-3">
            <h3 className="text-sm font-medium mb-1">Ferdigheter</h3>
            <div className="flex flex-wrap gap-2">
              {((profile.extracted_skills as Record<string, unknown>).skills as string[] || []).map((skill, i) => (
                <span key={i} className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">{skill}</span>
              ))}
            </div>
          </div>
        )}
        <button
          onClick={handleReExtract}
          className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 text-sm"
        >
          Analyser pa nytt
        </button>
      </section>

      {/* Notification Emails */}
      <section className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-3">Varslings-e-poster</h2>
        <p className="text-sm text-gray-500 mb-2">Kommaseparert liste med e-postadresser som skal motta jobbvarsler</p>
        <input
          type="text"
          value={emails}
          onChange={(e) => setEmails(e.target.value)}
          placeholder="epost1@example.com, epost2@example.com"
          className="w-full border rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
        />
        <button
          onClick={() => saveEmails.mutate()}
          className="mt-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm"
        >
          Lagre
        </button>
      </section>
    </div>
  );
}
