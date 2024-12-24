import { StructuredOutputParser } from 'langchain/output_parsers'
import { ZodSchema } from 'zod'

/**
 * Parser class that converts LLM outputs into structured objects
 * @class SchemaParser
 */
export class SchemaParser {
    private outputParser: StructuredOutputParser
    private formatInstructions: string

    constructor(schema: ZodSchema) {
        this.outputParser = new StructuredOutputParser(schema)
        this.formatInstructions = this.outputParser.formalInstructions
    }

    get formalInstructions() {
        return this.formatInstructions
    }

    async parse(output: string): Promise<Object> {
        return await this.outputParser.parse(output)
    }
}
