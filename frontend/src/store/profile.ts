export type ThemePreference = 'system' | 'light' | 'dark';

export interface Address {
  line1?: string;
  line2?: string;
  city?: string;
  state?: string;
  postalCode?: string;
  country?: string;
}

export interface ProfileSettings {
  companyName?: string;
  companyWebsite?: string;
  companyEmail?: string;
  phone?: string;
  address?: Address;
  logoDataUrl?: string; // stored as Data URL for preview/persistence
  brandColor?: string; // hex color
  theme?: ThemePreference;
  currency?: string; // e.g., USD, EUR
  dateFormat?: string; // e.g., YYYY-MM-DD
  timeZone?: string; // IANA tz
  units?: 'imperial' | 'metric';
  emailNotifications?: boolean;
  smsNotifications?: boolean;
  signature?: string;
}

const KEY_PREFIX = 'profile_settings:';

export function loadProfileSettings(userId: string): ProfileSettings {
  try {
    const raw = localStorage.getItem(KEY_PREFIX + userId);
    if (!raw) return {};
    return JSON.parse(raw) as ProfileSettings;
  } catch {
    return {};
  }
}

export function saveProfileSettings(userId: string, settings: ProfileSettings): void {
  localStorage.setItem(KEY_PREFIX + userId, JSON.stringify(settings));
}

export function clearProfileSettings(userId: string): void {
  localStorage.removeItem(KEY_PREFIX + userId);
}

