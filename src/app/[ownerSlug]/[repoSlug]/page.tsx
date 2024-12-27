import { JSX, Suspense } from 'react'
import { RepoCard } from '@/components/RepoCard'
import Loading from '@/app/[ownerSlug]/[repoSlug]/loading'
import { FetchRepoService, FullRepository } from '@/db/get-db'
import { MarkdownContent } from '@/components/MarkdownContent'
import { notFound } from 'next/navigation'

interface PageProps {
    params: {
        ownerSlug: string
        repoSlug: string
    }
}

interface RepoPageProps {
    ownerSlug: string
    repoSlug: string
}

const placeholder = `
# parser.cpp\n\n

- Reference \`parser/parser.cpp\`\n

This file defines the \`Parser\` class, responsible for transforming a stream of tokens into an Abstract Syntax Tree (AST). The parser utilizes a queue of \`TokenPtr\` objects (\`tok_queue_\`) and provides methods for consuming tokens (\`Eat\`), peeking at the next token (\`Peek\`), and expecting specific token types (\`ExpectedTokenType\`). The core functionality resides in \`ProduceAST\` which drives the parsing process by repeatedly calling \`ParseStatement\` until an end-of-line token is encountered. Different parsing methods are present to handle various expressions such as \`ParsePrimaryExpression\`, \`ParseAdditionExpression\`, \`ParseMultiplicationExpression\`, and \`ParseComparisonExpression\`. It supports variable declarations and assignments, and also handles whitespace using \`ParseWhitespaceExpression\`. The parser uses recursive descent parsing strategy with helper functions for each type of expression. It throws \`UnexpectedTokenParsedException\` when unexpected tokens are encountered. The \`Parser\` class depends on the \`TokenPtr\` and the \`ast.hpp\` module for the AST node definitions. Key methods include: [\`Eat\`](https://github.com/daeisbae/AParser/blob/9bbea84efa9f8eeed5576f53e4a65ca87a7f023c/parser/parser.cpp#L11-L15) for consuming tokens, [\`Peek\`](https://github.com/daeisbae/AParser/blob/9bbea84efa9f8eeed5576f53e4a65ca87a7f023c/parser/parser.cpp#L17-L17) for peeking at tokens, [\`ExpectedTokenType\`](https://github.com/daeisbae/AParser/blob/9bbea84efa9f8eeed5576f53e4a65ca87a7f023c/parser/parser.cpp#L19-L39) for validating token types, [\`ProduceAST\`](https://github.com/daeisbae/AParser/blob/9bbea84efa9f8eeed5576f53e4a65ca87a7f023c/parser/parser.cpp#L41-L53) for generating the AST, [\`ParseStatement\`](https://github.com/daeisbae/AParser/blob/9bbea84efa9f8eeed5576f53e4a65ca87a7f023c/parser/parser.cpp#L55-L62) for parsing statements, and [\`ParseExpression\`](https://github.com/daeisbae/AParser/blob/9bbea84efa9f8eeed5576f53e4a65ca87a7f023c/parser/parser.cpp#L64-L66) for parsing expressions. The file also handles different types of expressions using separate parsing methods like [\`ParsePrimaryExpression\`](https://github.com/daeisbae/AParser/blob/9bbea84efa9f8eeed5576f53e4a65ca87a7f023c/parser/parser.cpp#L68-L145), [\`ParseAdditionExpression\`](https://github.com/daeisbae/AParser/blob/9bbea84efa9f8eeed5576f53e4a65ca87a7f023c/parser/parser.cpp#L147-L165), [\`ParseMultiplicationExpression\`](https://github.com/daeisbae/AParser/blob/9bbea84efa9f8eeed5576f53e4a65ca87a7f023c/parser/parser.cpp#L167-L185), [\`ParseWhitespaceExpression\`](https://github.com/daeisbae/AParser/blob/9bbea84efa9f8eeed5576f53e4a65ca87a7f023c/parser/parser.cpp#L187-L192), [\`ParseIdentifierDeclarationExpression\`](https://github.com/daeisbae/AParser/blob/9bbea84efa9f8eeed5576f53e4a65ca87a7f023c/parser/parser.cpp#L194-L217), [\`ParseIdentifierAssignmentExpression\`](https://github.com/daeisbae/AParser/blob/9bbea84efa9f8eeed5576f53e4a65ca87a7f023c/parser/parser.cpp#L219-L243), and [\`ParseComparisonExpression\`](https://github.com/daeisbae/AParser/blob/9bbea84efa9f8eeed5576f53e4a65ca87a7f023c/parser/parser.cpp#L245-L263).
`

async function RepoPage({
    ownerSlug,
    repoSlug,
}: RepoPageProps): Promise<JSX.Element> {
    const fetchRepoService = new FetchRepoService()
    const repoDetails: FullRepository | null =
        await fetchRepoService.getFullRepositoryTree(ownerSlug, repoSlug)

    if (!repoDetails) {
        notFound()
    }

    return (
        <div className="flex gap-6 p-6">
            <div className="flex-1">
                <MarkdownContent content={placeholder} />
            </div>
            <div className="w-[300px]">
                <RepoCard repoInfo={repoDetails.repository} />
            </div>
        </div>
    )
}

export default function DocumentationPage({ params }: PageProps) {
    const { ownerSlug, repoSlug } = params

    return (
        <Suspense fallback={<Loading />}>
            <RepoPage ownerSlug={ownerSlug} repoSlug={repoSlug} />
        </Suspense>
    )
}
