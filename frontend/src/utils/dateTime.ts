const BAKERY_TIME_ZONE = 'America/New_York';

const bakeryDateTimeFormatter = new Intl.DateTimeFormat('en-US', {
  timeZone: BAKERY_TIME_ZONE,
  weekday: 'short',
  month: 'short',
  day: 'numeric',
  hour: 'numeric',
  minute: '2-digit',
  hour12: true,
  timeZoneName: 'short',
});

const bakeryDateFormatter = new Intl.DateTimeFormat('en-US', {
  timeZone: BAKERY_TIME_ZONE,
  weekday: 'short',
  month: 'short',
  day: 'numeric',
});

const bakeryDateOnlyFormatter = new Intl.DateTimeFormat('en-US', {
  timeZone: BAKERY_TIME_ZONE,
  year: 'numeric',
  month: 'short',
  day: 'numeric',
});

export function formatBakeryDateTime(value?: string | null) {
  if (!value) {
    return 'Not set';
  }
  return bakeryDateTimeFormatter.format(new Date(value));
}

export function formatBakeryDate(value?: string | null) {
  if (!value) {
    return 'Not set';
  }
  return bakeryDateFormatter.format(new Date(value));
}

export function formatBakeryDateOnly(value?: string | null) {
  if (!value) {
    return 'Not set';
  }
  const normalized = `${value}T12:00:00Z`;
  return bakeryDateOnlyFormatter.format(new Date(normalized));
}
