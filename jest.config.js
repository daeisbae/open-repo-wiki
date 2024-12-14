export default {
    transform: {}, // No need for Babel if you're using native ESM
    moduleNameMapper: {
        '^@/(.*)$': '<rootDir>/src/$1', // Alias support
    },
};
