import { filterFile } from '@/github/filterfile';

describe('filterFile', () => {
    it('should remove files that match a simple pattern', () => {
        const files = ['index.js', 'README.md', 'node_modules/library.js'];
        const regexFilter = ['node_modules'];
        const result = filterFile(files, regexFilter);
        expect(result).toEqual(['index.js', 'README.md']);
    });

    it('should remove files that match a regex for specific extensions', () => {
        const files = ['index.js', 'app.json', 'style.css'];
        const regexFilter = ['.*\\.json$'];
        const result = filterFile(files, regexFilter);
        expect(result).toEqual(['index.js', 'style.css']);
    });

    it('should remove files that match multiple regex patterns', () => {
        const files = ['index.js', 'README.md', '.github/config.yml', 'node_modules/library.js'];
        const regexFilter = ['node_modules', '\\.github'];
        const result = filterFile(files, regexFilter);
        expect(result).toEqual(['index.js', 'README.md']);
    });

    it('should retain all files if regex patterns do not match any file', () => {
        const files = ['index.js', 'README.md', 'style.css'];
        const regexFilter = ['non_existent_folder', '\\.unknown$'];
        const result = filterFile(files, regexFilter);
        expect(result).toEqual(['index.js', 'README.md', 'style.css']);
    });

    it('should remove all files if the regex matches everything', () => {
        const files = ['index.js', 'README.md', 'style.css'];
        const regexFilter = ['.*'];
        const result = filterFile(files, regexFilter);
        expect(result).toEqual([]);
    });

    it('should handle an empty file list gracefully', () => {
        const files = [];
        const regexFilter = ['.*'];
        const result = filterFile(files, regexFilter);
        expect(result).toEqual([]);
    });

    it('should handle an empty regex filter gracefully', () => {
        const files = ['index.js', 'README.md'];
        const regexFilter = [];
        const result = filterFile(files, regexFilter);
        expect(result).toEqual(['index.js', 'README.md']);
    });
});
