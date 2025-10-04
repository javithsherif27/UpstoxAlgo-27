import React from 'react';
import { useProfile } from '../queries/useProfile';

export const DashboardPage: React.FC = () => {
  const { data, isLoading, error } = useProfile();

  console.log('DashboardPage: Profile query state:', { data, isLoading, error });

  if (isLoading) return <div className="p-4">Loading profile...</div>;
  if (error) {
    console.error('DashboardPage: Profile error:', error);
    return <div className="p-4 text-red-600">Failed to load profile: {error.message}</div>;
  }

  return (
    <div className="p-4 space-y-2">
      <h2 className="text-lg font-semibold">Profile</h2>
      <div className="text-sm">Name: {data?.name || 'No name data'}</div>
      <div className="text-sm">Client ID: {data?.client_id || 'No client_id data'}</div>
      <div className="text-sm">KYC Status: {data?.kyc_status || 'No kyc_status data'}</div>
      
      {/* Debug information */}
      <div className="mt-4 p-2 bg-gray-100 text-xs">
        <div>Debug - Raw data: {JSON.stringify(data, null, 2)}</div>
      </div>
    </div>
  );
};
