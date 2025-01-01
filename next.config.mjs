/** @type {import('next').NextConfig} */
const nextConfig = {
	transpilePackages: ["next-mdx-remote"],
	// Need to remove this later
	typescript: {
		ignoreBuildErrors: true,
	},
};

export default nextConfig;
