/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  output: 'standalone', // For Docker production builds
  trailingSlash: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || '/api',
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