/** @type {import('next').NextConfig} */
import dotenv from "dotenv";
dotenv.config();

const nextConfig = {
	transpilePackages: ["next-mdx-remote"],
	// Need to remove this later
	typescript: {
		ignoreBuildErrors: true,
	},
	async rewrites() {
		console.log("API_ENDPOINT", process.env.NEXT_PUBLIC);
		return [
			{
				source: "/api/:path*",
				destination: `${process.env.NEXT_PUBLIC_API_ENDPOINT}/api/queue`,
			},
			{
				source: "/api/:path*",
				destination: `${process.env.NEXT_PUBLIC_API_ENDPOINT}/api/queue`,
			},
		];
	},
};

export default nextConfig;
