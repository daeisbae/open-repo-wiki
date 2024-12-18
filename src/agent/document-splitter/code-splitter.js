import { RecursiveCharacterTextSplitter } from '@langchain/textsplitters';

/**
 * Splitting code into chunks into Langchain document depending on file extension.
 */
export default class CodeSplitter {
    /**
     * Constructor for CodeSplitter.
     * @param {number} chunkSize - The size of each chunk.
     * @param {number} chunkOverlap - The number of overlapping characters between chunks.
     */
    constructor(chunkSize, chunkOverlap) {
        this.chunkSize = chunkSize;
        this.chunkOverlap = chunkOverlap;
    }

    /**
     * Retrieves the programming language associated with a given file extension.
     * @param {string} extension - The file extension excluding the dot (e.g., 'js', 'py').
     * @returns {Language | null} - The corresponding Language enum or null (if not supported).
     */
    #getLanguageFromExtension(extension) {
        let extensionToLanguageMap = {
            'py': 'python',
            'js': 'js',
            'jsx': 'js',
            'ts': 'js',
            'tsx': 'js',
            'go': 'go',
            'rb': 'ruby',
            'rs': 'rust',
            'php': 'php',
            'cpp': 'cpp',
            'cc': 'cpp',
            'cxx': 'cpp',
            'hpp': 'cpp',
            'hxx': 'cpp',
            'h': 'cpp',
        };
        return extensionToLanguageMap[extension.toLowerCase()] || null;
    }

    /**
     * Splits the provided code into chunks based on the file extension.
     * @param {string} fileExtension - The file extension indicating the programming language.
     * @param {string} code - The code content to be split.
     * @returns {Promise<Array<Document>> | null}  - A promise that resolves to an array of document chunks.
     */
    async splitCode(fileExtension, code) {
        const language = this.#getLanguageFromExtension(fileExtension);
        if (!language) {
            return null;
        }
        

        const splitter = RecursiveCharacterTextSplitter.fromLanguage(language, {
            chunkSize: this.chunkSize,
            chunkOverlap: this.chunkOverlap,
        });

        const documents = await splitter.createDocuments([code]);
        return documents;
    }
}