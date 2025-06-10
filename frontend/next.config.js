/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  trailingSlash: false,
  
  // Railway build optimization - reduser memory usage
  eslint: {
    // Deaktiver ESLint under build for å spare memory på Railway
    ignoreDuringBuilds: true,
  },
  typescript: {
    // Deaktiver type checking under build for å spare memory
    ignoreBuildErrors: true,
  },
  experimental: {
    // Reduser worker threads for memory optimization
    workerThreads: false,
  },
  
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        // Railway production vs lokalt utvikling
        destination: process.env.NODE_ENV === 'production'
          ? '/api/:path*'
          : 'http://localhost:8000/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig; 