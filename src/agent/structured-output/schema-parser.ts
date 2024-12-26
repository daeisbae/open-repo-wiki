import { StructuredOutputParser } from 'langchain/output_parsers'
import { ZodSchema, ZodTypeAny } from 'zod'

/**
 * Parser class that converts LLM outputs into structured objects based on Zod schemas
 * @class SchemaParser
 */
export class SchemaParser {
    private outputParser: StructuredOutputParser<ZodTypeAny>
    private formatInstructions: string

    /**
     * Constructor for SchemaParser instance
     * @param schema - Zod schema defining the expected output structure
     */
    constructor(schema: ZodSchema) {
        this.outputParser = StructuredOutputParser.fromZodSchema(schema)
        this.formatInstructions = this.outputParser.getFormatInstructions()
    }

    /**
     * output instructions for LLM
     * @returns Formatting instructions for LLM
     */
    get formalInstructions() {
        return this.formatInstructions
    }

    /**
     * Removes JSON markdown code block wrapper if present
     * @param {string} input - potentially containing JSON markdown block
     * @returns Cleaned string without markdown wrapper
     * @private
     */
    private removeJsonMarkdownWrapper(input: string): string {
        if (!input) return input

        const hasJsonStart = input.startsWith('```json\n')
        const hasMarkdownEnd = input.endsWith('\n```')

        if (hasJsonStart && hasMarkdownEnd) {
            return input.slice(8, -4)
        }

        return input
    }

    /**
     * Parses LLM output into structured object based on schema
     * @param {string} output - Raw string output (expecting JSON stringified) from LLM
     * @returns Promise resolving to parsed object matching schema
     */
    async parse(output: string): Promise<Object> {
        const filteredOutput = this.removeJsonMarkdownWrapper(output)
        return await this.outputParser.parse(filteredOutput)
    }
}
