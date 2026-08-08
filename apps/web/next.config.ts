import type { NextConfig } from "next";

const apiOrigin = process.env.CREATORSHIELD_API_URL || "http://api:8000";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/api/media/:path*",
        destination: `${apiOrigin}/media/:path*`,
      },
      {
        source: "/api/:path*",
        destination: `${apiOrigin}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
