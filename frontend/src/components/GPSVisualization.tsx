import React from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface GPSPoint { timestamp: string; latitude: number; longitude: number; }

export const GPSVisualization: React.FC<{ data: GPSPoint[] }> = ({ data }) => (
  <div className="w-full h-64 bg-white dark:bg-gray-800 rounded-xl p-4 shadow-inner">
    <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-2">GPS Data Over Time</h2>
    <ResponsiveContainer>
      <LineChart data={data} margin={{ top: 10, right: 20, bottom: 5, left: 0 }}>
        <XAxis dataKey="timestamp" tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip />
        <Line
          type="monotone"
          dataKey="latitude"
          stroke="currentColor"
          strokeWidth={2}
          dot={false}
        />
        <Line
          type="monotone"
          dataKey="longitude"
          strokeDasharray="5 5"
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  </div>
); 