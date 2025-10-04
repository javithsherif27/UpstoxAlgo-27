const IST_OFFSET_MINUTES = 330; // 5.5 hours

export function getNowIST(): Date {
  const now = new Date();
  // convert to IST by adding offset difference from local timezone
  const utc = now.getTime() + now.getTimezoneOffset() * 60000;
  return new Date(utc + IST_OFFSET_MINUTES * 60000);
}

export function getEODIST(): string {
  const now = getNowIST();
  const eod = new Date(now);
  eod.setHours(23, 59, 59, 999);
  return eod.toISOString();
}

export function isExpiredEOD(expiresAt: string): boolean {
  return new Date() > new Date(expiresAt);
}
