import axios from "axios";
import { jest } from "@jest/globals";
import {
	fetchGithubRepoDetails,
	fetchGithubRepoTree,
	fetchGithubRepoFile,
} from "@/github/fetchrepo";

jest.mock("axios");

describe("fetchGithubRepoDetails", () => {
	it("should fetch and return the repository details correctly", async () => {
		const mockResponse = {
			data: {
				owner: {
					login: "octocat",
				},
				name: "Hello-World",
				html_url: "https://github.com/octocat/Hello-World",
				description: "My first repository on GitHub!",
				stargazers_count: 2769,
				forks_count: 2499,
				topics: [],
				language: "JavaScript",
				default_branch: "master",
			},
		};

		const mockResponse2 = {
			data: {
				sha: "7fd1a60b01f91b314f59955a4e4d4e80d8edf11d",
			},
		};
		axios.get = jest.fn();
		axios.get.mockImplementation(async (url) => {
			if (url.includes("/git/trees/master")) {
				return mockResponse2;
			} else {
				return mockResponse;
			}
		});

		const result = await fetchGithubRepoDetails("octocat", "Hello-World");

		const expectedOutput = {
			repoOwner: "octocat",
			repoName: "Hello-World",
			url: "https://github.com/octocat/Hello-World",
			topics: [],
			language: "JavaScript",
			description: "My first repository on GitHub!",
			stars: 2769,
			forks: 2499,
			defaultBranch: "master",
			sha: "7fd1a60b01f91b314f59955a4e4d4e80d8edf11d",
		};

		expect(result).toEqual(expectedOutput);
	});
});

describe("fetchGithubRepoTree", () => {
	it("should fetch single full file tree structure", async () => {
		const mockResponse = {
			data: [
				{
					name: "README",
					path: "README",
					sha: "980a0d5f19a64b4b30a87d4206aade58726b60e3",
					size: 13,
					url: "https://api.github.com/repos/octocat/Hello-World/contents/README?ref=master",
					html_url: "https://github.com/octocat/Hello-World/blob/master/README",
					git_url:
						"https://api.github.com/repos/octocat/Hello-World/git/blobs/980a0d5f19a64b4b30a87d4206aade58726b60e3",
					download_url:
						"https://raw.githubusercontent.com/octocat/Hello-World/master/README",
					type: "file",
					_links: {
						self: "https://api.github.com/repos/octocat/Hello-World/contents/README?ref=master",
						git: "https://api.github.com/repos/octocat/Hello-World/git/blobs/980a0d5f19a64b4b30a87d4206aade58726b60e3",
						html: "https://github.com/octocat/Hello-World/blob/master/README",
					},
				},
			],
		};

		const expectedOutput = {
			path: "",
			files: ["README"],
			subdirectories: [],
		};

		axios.get = jest.fn(() => mockResponse);

		const result = await fetchGithubRepoTree(
			"octocat",
			"Hello-World",
			"7fd1a60b01f91b314f59955a4e4d4e80d8edf11d",
			"",
		);

		expect(result).toEqual(expectedOutput);
	});

	it("should fetch repository tree structure recursively", async () => {
		const mockRootResponse = {
			data: [
				{
					name: ".github",
					path: ".github",
					type: "dir",
				},
				{
					name: "README.md",
					path: "README.md",
					type: "file",
				},
				{
					name: "main.cpp",
					path: "main.cpp",
					type: "file",
				},
			],
		};

		const mockGithubDirResponse = {
			data: [
				{
					name: "workflows",
					path: ".github/workflows",
					type: "dir",
				},
			],
		};

		const mockWorkflowsResponse = {
			data: [
				{
					name: "ci.yml",
					path: ".github/workflows/ci.yml",
					type: "file",
				},
			],
		};

		axios.get
			.mockResolvedValueOnce(mockRootResponse)
			.mockResolvedValueOnce(mockGithubDirResponse)
			.mockResolvedValueOnce(mockWorkflowsResponse);

		const result = await fetchGithubRepoTree("daeisbae", "AParser");

		const expectedOutput = {
			path: "",
			files: ["README.md", "main.cpp"],
			subdirectories: [
				{
					path: ".github",
					files: [],
					subdirectories: [
						{
							path: ".github/workflows",
							files: [".github/workflows/ci.yml"],
							subdirectories: [],
						},
					],
				},
			],
		};

		expect(result).toEqual(expectedOutput);
	});
});

describe("fetchGithubRepoFile", () => {
	it("should fetch file with specific sha and empty path", async () => {
		const mockResponse = {
			data: "Hello World!",
		};

		axios.get = jest.fn().mockResolvedValue(mockResponse);

		const result = await fetchGithubRepoFile(
			"octocat",
			"Hello-World",
			"7fd1a60b01f91b314f59955a4e4d4e80d8edf11d",
			"",
		);

		const expectedOutput = "Hello World!";

		expect(result).toEqual(expectedOutput);
		expect(axios.get).toHaveBeenCalledWith(
			"https://raw.githubusercontent.com/octocat/Hello-World/7fd1a60b01f91b314f59955a4e4d4e80d8edf11d/",
		);
	});
});
