import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../lib/api';
import { ProfileDTO } from '../lib/types';

async function fetchProfile(): Promise<ProfileDTO> {
  console.log('fetchProfile: Making request to /api/upstox/profile');
  const res = await apiClient.get('/api/upstox/profile');
  console.log('fetchProfile: Response received:', res.data);
  return res.data;
}

export function useProfile() {
  return useQuery({ 
    queryKey: ['profile'], 
    queryFn: fetchProfile,
    retry: 1,
    retryDelay: 1000
  });
}
