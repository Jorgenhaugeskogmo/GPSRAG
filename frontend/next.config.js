/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  output: 'export', // For static export
  trailingSlash: true,
  distDir: 'dist',
  env: {
    NEXT_PUBLIC_API_URL: process.env.NODE_ENV === 'production' 
      ? 'https://gpsrag-production.up.railway.app'
      : process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || '/ws',
  },
  async rewrites() {
    // API proxy for fullstack deployment
    return [
      {
        source: '/api/:path*',
        destination: '/api/:path*', // Served by FastAPI backend
      },
      {
        source: '/docs',
        destination: '/docs', // FastAPI docs
      },
      {
        source: '/redoc',
        destination: '/redoc', // FastAPI redoc
      },
    ];
  },
};

module.exports = nextConfig; 