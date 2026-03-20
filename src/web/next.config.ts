import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Connect to local FastAPI backend
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8765/:path*",
      },
    ];
  },
};

export default nextConfig;
