import type { NextConfig } from "next";
import path from "path";

const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';

// Use a port-scoped distDir so multiple dev instances don't collide on the lock file
const distDir = process.env.PORT && process.env.PORT !== '9999'
  ? `.next-${process.env.PORT}`
  : '.next';

const nextConfig: NextConfig = {
  output: 'standalone',
  distDir,
  basePath: basePath,
  assetPrefix: basePath,
  // Disable request logging in production
  logging: false,
  // Expose the dataplane API on the same public origin (the platform exposes one
  // port per service). These paths are authenticated by the API key, not Basic auth.
  async rewrites() {
    const api = process.env.ENTELECHY_CP_DATAPLANE_API_URL || 'http://localhost:8888';
    return [
      { source: '/v1/:path*', destination: `${api}/v1/:path*` },
      { source: '/mcp', destination: `${api}/mcp` },
      { source: '/mcp/:path*', destination: `${api}/mcp/:path*` },
      { source: '/openapi.json', destination: `${api}/openapi.json` },
      { source: '/docs', destination: `${api}/docs` },
      { source: '/version', destination: `${api}/version` },
    ];
  },
  // Set the monorepo root explicitly to avoid detecting wrong lockfiles in parent directories
  turbopack: {
    root: path.resolve(__dirname, '..'),
  },
};

export default nextConfig;
