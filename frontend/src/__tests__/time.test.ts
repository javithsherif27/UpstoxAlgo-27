import { describe, it, expect } from 'vitest';
import { getEODIST, isExpiredEOD } from '../lib/time';

describe('time helpers', () => {
  it('eod is in future', () => {
    const eod = getEODIST();
    expect(new Date(eod).getTime()).toBeGreaterThan(Date.now());
  });
  it('isExpiredEOD false for future time', () => {
    const eod = new Date(Date.now() + 10000).toISOString();
    expect(isExpiredEOD(eod)).toBe(false);
  });
});
