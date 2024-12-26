import { RecursiveCharacterTextSplitter, SupportedTextSplitterLanguage } from '@langchain/textsplitters';

enum Language {
    PYTHON = "python",
    JS = "js",
    GO = "go",
    RUBY = "ruby",
    RUST = "rust",
    PHP = "php",
    CPP = "cpp"
  }

/**
 * Splitting code chunks into Langchain document depending on file extension.
 */
export default class CodeSplitter {
    /**
     * Constructor for CodeSplitter.
     * @param {number} chunkSize - The size of each chunk.
     * @param {number} chunkOverlap - The number of overlapping characters between chunks.
     */
    constructor(public chunkSize: number, public chunkOverlap: number) {
        this.chunkSize = chunkSize;
        this.chunkOverlap = chunkOverlap;
    }

    /**
     * Retrieves the programming language associated with a given file extension.
     * @param {string} extension - The file extension excluding the dot (e.g., 'js', 'py').
     * @returns {Language | null} - The corresponding Language enum or null (if not supported).
     */
    private getLanguageFromExtension(extension: string): SupportedTextSplitterLanguage | null {
        let extensionToLanguageMap: { [key: string]: Language } = {
            'py': Language.PYTHON,
            'js': Language.JS,
            'jsx': Language.JS,
            'ts': Language.JS,
            'tsx': Language.JS,
            'go': Language.GO,
            'rb': Language.RUBY,
            'rs': Language.RUST,
            'php': Language.PHP,
            'cpp': Language.CPP,
            'cc': Language.CPP,
            'cxx': Language.CPP,
            'hpp': Language.CPP,
            'hxx': Language.CPP,
            'h': Language.CPP,
        };
        return extensionToLanguageMap[extension.toLowerCase()] || null;
    }

    /**
     * Splits the provided code into chunks based on the file extension.
     * @param {string} fileExtension - The file extension indicating the programming language.
     * @param {string} code - The code content to be split.
     * @returns {Promise<string | null>}  - A promise that resolves to an array of document chunks.
     */
    async splitCode(fileExtension: string, code: string): Promise<string | null> {
        const language : SupportedTextSplitterLanguage | null = this.getLanguageFromExtension(fileExtension);
        if (!language) {
            return null;
        }

        const splitter = RecursiveCharacterTextSplitter.fromLanguage(language, {
            chunkSize: this.chunkSize,
            chunkOverlap: this.chunkOverlap,
        });

        const doc = await splitter.createDocuments([code]);
        let docWithMetadata = '';
        for(let i = 0; i < doc.length; i++) {
            docWithMetadata += `// Line ${doc[i].metadata.loc.lines.from} - ${doc[i].metadata.loc.lines.to}\n${doc[i].pageContent}\n\n`;
        }
        return docWithMetadata;
    }
}