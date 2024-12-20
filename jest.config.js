/* eslint-disable import/no-anonymous-default-export */
export default {
	transform: {
		"^.+\\.tsx?$": "babel-jest",
	},
	extensionsToTreatAsEsm: [".ts", ".tsx"],
	moduleNameMapper: {
		"^@/(.*)$": "<rootDir>/src/$1",
	},
};
