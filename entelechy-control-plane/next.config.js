// next.config.js
// NOTE: Next.js loads this file in preference to next.config.ts, so settings
// must live here (keep next.config.ts in sync).
module.exports = {
  output: 'standalone',
  allowedDevOrigins: ['208.113.130.72', 'mindmods.org', 'www.mindmods.org'],
  // Expose the dataplane API on the same public origin; authenticated by API key.
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
}
