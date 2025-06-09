/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  trailingSlash: false,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        // I Vercel-miljøet vil dette automatisk rutes til /api-mappen
        // Lokalt vil det proxy'es til backend-serveren
        destination: process.env.NODE_ENV === 'production'
          ? '/api/:path*'
          : 'http://localhost:8000/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig; 