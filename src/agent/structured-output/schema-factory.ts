import { z, ZodSchema } from 'zod'

/**
 * Enum for schema types.
 * @readonly
 * @enum {string}
 */
export enum SchemaType {
    FILE = 'file',
    FOLDER = 'folder',
}

/**
 * Returns a predefined structured output schema based on the specified schema type.
 * @param {SchemaType} schemaType - The type of schema to generate. Use SchemaType enum.
 * @returns {ZodSchema} The corresponding Zod schema.
 * @throws {Error} Will throw an error if the schema type is unknown.
 */
export function getSchema(schemaType: SchemaType): ZodSchema {
    switch (schemaType) {
        /*
File Schema Example Output:
{
  "name": "parser.ts",
  "path": "src/utils/parser.ts",
  "summary": "This file implements a parser for processing input data. The main entry point is the [`parseInput`](#L15-L30) function, which takes raw data and transforms it into a structured format. Error handling is managed within the [`handleParsingErrors`](#L45-L60) function to ensure robustness.",
  "relevantCodeBlocks": [
    {
      "name": "parseInput",
      "description": "The primary function responsible for parsing the input data.",
      "startLine": 15,
      "endLine": 30
    },
    {
      "name": "handleParsingErrors",
      "description": "Centralized error handling logic for the parsing process.",
      "startLine": 45,
      "endLine": 60
    }
  ]
}
*/
        case SchemaType.FILE:
            return z.object({
                name: z.string().describe('Name of the file.'),
                path: z
                    .string()
                    .describe('Path to the file within the repository.'),
                summary: z
                    .string()
                    .describe(
                        'Summary of the file, its main purpose, and its role in the project. Include Markdown links to important code blocks within this file using the format `[{Description of Code Block}]({Full github url of the file including the start line with optional ending line}#L{startLine}-L{endLine})` where applicable.'
                    ),
                relevantCodeBlocks: z
                    .array(
                        z.object({
                            name: z
                                .string()
                                .describe(
                                    'Name or identifier of the code block (e.g., function name, class name, key variable).'
                                ),
                            description: z
                                .string()
                                .describe(
                                    'Description of the code block and its significance within the file.'
                                ),
                            startLine: z
                                .number()
                                .describe(
                                    'Starting line number of the code block.'
                                ),
                            endLine: z
                                .number()
                                .describe(
                                    'Ending line number of the code block.'
                                ),
                        })
                    )
                    .optional()
                    .describe(
                        'List of important code blocks (functions, classes, key sections) within the file, with line numbers.'
                    ),
            })

        /*
Folder Schema Example Output:
{
  "name": "components",
  "usage": "Contains reusable React components for the application's user interface.",
  "path": "src/components",
  "summary": "The `components` folder houses the application's building blocks for the user interface. It includes various reusable components like the [`Button`](src/components/Button.tsx) for user interactions and the [`Modal`](src/components/Modal.tsx) for displaying overlay content. The [`Card`](src/components/Card.tsx) component is used throughout the application to present information in a structured manner.",
  "files": [
    {
      "fileName": "Button.tsx",
      "filePath": "src/components/Button.tsx"
    },
    {
      "fileName": "Modal.tsx",
      "filePath": "src/components/Modal.tsx"
    },
    {
      "fileName": "Card.tsx",
      "filePath": "src/components/Card.tsx"
    },
  ],
}
*/
        case SchemaType.FOLDER:
            return z.object({
                name: z.string().describe('Name of the folder.'),
                usage: z.string().describe('What the folder is used for.'),
                path: z.string().describe('Path to the folder.'),
                summary: z
                    .string()
                    .describe(
                        'Summary of the folder, its main purpose, and its role in the project. Include Markdown links to important code blocks within the file using the format `[{Description of Code Block}]({Full github url of the file including the start line with optional ending line}#L{startLine}-L{endLine})` where applicable.'
                    ),
                files: z
                    .array(
                        z.object({
                            fileName: z
                                .string()
                                .describe(
                                    'Name of the file mentioned in the summary'
                                ),
                            filePath: z
                                .string()
                                .describe(
                                    'Path to the file mentioned in the summary'
                                ),
                        })
                    )
                    .optional()
                    .describe('List of files in the folder.'),
            })

        default:
            throw new Error(`Unknown schema type: ${schemaType}`)
    }
}
