import { useEffect, useMemo, useState } from 'react';
import { getCurrentUser } from '../api/users';
import type { User } from '../api/users';
import {
  loadProfileSettings,
  saveProfileSettings,
  type ProfileSettings,
  type ThemePreference,
} from '../store/profile';

export default function Profile() {
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [settings, setSettings] = useState<ProfileSettings>({});

  useEffect(() => {
    getCurrentUser()
      .then(setUser)
      .catch(() => setError('Failed to load user'));
  }, []);

  useEffect(() => {
    if (user) {
      setSettings((prev) => ({ ...prev, ...loadProfileSettings(user.id) }));
    }
  }, [user]);

  const currentTz = useMemo(() => {
    try {
      return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
    } catch {
      return 'UTC';
    }
  }, []);

  if (error) {
    return <div role="alert">{error}</div>;
  }

  if (!user) {
    return <div>Loading...</div>;
  }

  return (
    <div className="max-w-3xl mx-auto p-4 space-y-6">
      <h2 className="text-2xl font-bold">Profile</h2>

      <section className="bg-white/50 dark:bg-gray-800/40 rounded-lg p-4 shadow-sm">
        <h3 className="text-lg font-semibold mb-3">Account</h3>
        <div className="space-y-2 text-sm">
          <p>
            <span className="font-medium">Email:</span> {user.email}
          </p>
          <p>
            <span className="font-medium">Status:</span> {user.is_active ? 'Active' : 'Inactive'}
          </p>
          <p>
            <span className="font-medium">Role:</span> {user.is_superuser ? 'Admin' : 'User'}
          </p>
        </div>
      </section>

      <form
        className="bg-white/50 dark:bg-gray-800/40 rounded-lg p-4 shadow-sm space-y-4"
        onSubmit={(e) => {
          e.preventDefault();
          if (!user) return;
          setSaving(true);
          try {
            saveProfileSettings(user.id, settings);
          } finally {
            setSaving(false);
          }
        }}
      >
        <h3 className="text-lg font-semibold">Company</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Company Name</label>
            <input
              type="text"
              value={settings.companyName || ''}
              onChange={(e) => setSettings({ ...settings, companyName: e.target.value })}
              className="w-full rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-2"
              placeholder="e.g., BakeMate LLC"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Website</label>
            <input
              type="url"
              value={settings.companyWebsite || ''}
              onChange={(e) => setSettings({ ...settings, companyWebsite: e.target.value })}
              className="w-full rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-2"
              placeholder="https://example.com"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Company Email</label>
            <input
              type="email"
              value={settings.companyEmail || ''}
              onChange={(e) => setSettings({ ...settings, companyEmail: e.target.value })}
              className="w-full rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-2"
              placeholder="billing@example.com"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Phone</label>
            <input
              type="tel"
              value={settings.phone || ''}
              onChange={(e) => setSettings({ ...settings, phone: e.target.value })}
              className="w-full rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-2"
              placeholder="(555) 123-4567"
            />
          </div>
          <div className="md:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Address Line 1</label>
              <input
                type="text"
                value={settings.address?.line1 || ''}
                onChange={(e) => setSettings({ ...settings, address: { ...settings.address, line1: e.target.value } })}
                className="w-full rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Address Line 2</label>
              <input
                type="text"
                value={settings.address?.line2 || ''}
                onChange={(e) => setSettings({ ...settings, address: { ...settings.address, line2: e.target.value } })}
                className="w-full rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">City</label>
              <input
                type="text"
                value={settings.address?.city || ''}
                onChange={(e) => setSettings({ ...settings, address: { ...settings.address, city: e.target.value } })}
                className="w-full rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">State/Province</label>
              <input
                type="text"
                value={settings.address?.state || ''}
                onChange={(e) => setSettings({ ...settings, address: { ...settings.address, state: e.target.value } })}
                className="w-full rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Postal Code</label>
              <input
                type="text"
                value={settings.address?.postalCode || ''}
                onChange={(e) => setSettings({ ...settings, address: { ...settings.address, postalCode: e.target.value } })}
                className="w-full rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Country</label>
              <input
                type="text"
                value={settings.address?.country || ''}
                onChange={(e) => setSettings({ ...settings, address: { ...settings.address, country: e.target.value } })}
                className="w-full rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-2"
              />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-start">
          <div>
            <label className="block text-sm font-medium mb-1">Company Logo</label>
            <div className="flex items-center gap-4">
              <div className="h-20 w-20 rounded border border-dashed flex items-center justify-center overflow-hidden bg-white dark:bg-gray-900">
                {settings.logoDataUrl ? (
                  <img src={settings.logoDataUrl} alt="Logo preview" className="object-contain h-full w-full" />
                ) : (
                  <img src="/logo-placeholder.svg" alt="No logo" className="h-10 w-10 opacity-60" />
                )}
              </div>
              <div className="space-x-2">
                <label className="inline-block">
                  <span className="sr-only">Choose logo</span>
                  <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (!file) return;
                      const reader = new FileReader();
                      reader.onload = () => {
                        setSettings({ ...settings, logoDataUrl: String(reader.result) });
                      };
                      reader.readAsDataURL(file);
                    }}
                  />
                  <span className="cursor-pointer inline-flex items-center rounded bg-blue-600 px-3 py-2 text-white text-sm">Upload</span>
                </label>
                {settings.logoDataUrl && (
                  <button
                    type="button"
                    className="inline-flex items-center rounded border px-3 py-2 text-sm"
                    onClick={() => setSettings({ ...settings, logoDataUrl: undefined })}
                  >
                    Remove
                  </button>
                )}
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2">PNG or SVG recommended. Max ~1MB for best performance.</p>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Brand Color</label>
            <input
              type="color"
              value={settings.brandColor || '#7c3aed'}
              onChange={(e) => setSettings({ ...settings, brandColor: e.target.value })}
              className="h-10 w-16 p-0 border rounded bg-white dark:bg-gray-900"
            />
          </div>
        </div>

        <h3 className="text-lg font-semibold mt-2">Preferences</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Theme</label>
            <select
              value={settings.theme || 'system'}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  theme: e.target.value as ThemePreference,
                })
              }
              className="w-full rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-2"
            >
              <option value="system">System</option>
              <option value="light">Light</option>
              <option value="dark">Dark</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Currency</label>
            <select
              value={settings.currency || 'USD'}
              onChange={(e) => setSettings({ ...settings, currency: e.target.value })}
              className="w-full rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-2"
            >
              <option value="USD">USD</option>
              <option value="EUR">EUR</option>
              <option value="GBP">GBP</option>
              <option value="CAD">CAD</option>
              <option value="AUD">AUD</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Date Format</label>
            <select
              value={settings.dateFormat || 'YYYY-MM-DD'}
              onChange={(e) => setSettings({ ...settings, dateFormat: e.target.value })}
              className="w-full rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-2"
            >
              <option value="YYYY-MM-DD">YYYY-MM-DD</option>
              <option value="MM/DD/YYYY">MM/DD/YYYY</option>
              <option value="DD/MM/YYYY">DD/MM/YYYY</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Time Zone</label>
            <select
              value={settings.timeZone || currentTz}
              onChange={(e) => setSettings({ ...settings, timeZone: e.target.value })}
              className="w-full rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-2"
            >
              <option value={currentTz}>{currentTz} (Detected)</option>
              <option value="UTC">UTC</option>
              <option value="America/New_York">America/New_York</option>
              <option value="America/Los_Angeles">America/Los_Angeles</option>
              <option value="Europe/London">Europe/London</option>
              <option value="Europe/Berlin">Europe/Berlin</option>
              <option value="Asia/Tokyo">Asia/Tokyo</option>
              <option value="Asia/Kolkata">Asia/Kolkata</option>
              <option value="Australia/Sydney">Australia/Sydney</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Units</label>
            <select
              value={settings.units || 'imperial'}
              onChange={(e) => setSettings({ ...settings, units: e.target.value as 'imperial' | 'metric' })}
              className="w-full rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-2"
            >
              <option value="imperial">Imperial (lb, oz)</option>
              <option value="metric">Metric (kg, g)</option>
            </select>
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium mb-1">Invoice/Email Signature</label>
            <textarea
              value={settings.signature || ''}
              onChange={(e) => setSettings({ ...settings, signature: e.target.value })}
              className="w-full rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-2 min-h-[80px]"
              placeholder={'Thank you for your business!\n— The BakeMate Team'}
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <label className="inline-flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={!!settings.emailNotifications}
              onChange={(e) => setSettings({ ...settings, emailNotifications: e.target.checked })}
              className="h-4 w-4"
            />
            Email notifications
          </label>
          <label className="inline-flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={!!settings.smsNotifications}
              onChange={(e) => setSettings({ ...settings, smsNotifications: e.target.checked })}
              className="h-4 w-4"
            />
            SMS notifications
          </label>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="submit"
            className="inline-flex items-center rounded bg-blue-600 px-4 py-2 text-white text-sm disabled:opacity-50"
            disabled={saving || !user}
          >
            {saving ? 'Saving…' : 'Save Changes'}
          </button>
        </div>
      </form>
    </div>
  );
}
