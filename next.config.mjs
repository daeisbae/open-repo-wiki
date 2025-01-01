/** @type {import('next').NextConfig} */
const nextConfig = {
	transpilePackages: ["next-mdx-remote"],
	webpack: (config, { isServer }) => {
		if (!isServer) {
			config.resolve.fallback = {
				fs: false,
				dns: false,
				net: false,
				tls: false,
			};
		}
		return config;
	},
	// Need to remove this later
	typescript: {
		ignoreBuildErrors: true,
	},
};

export default nextConfig;
