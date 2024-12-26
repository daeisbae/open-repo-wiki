import CodeSplitter from '@/agent/document-splitter/code-splitter'

describe('CodeSplitter', () => {
    let codeSplitter

    beforeEach(() => {
        codeSplitter = new CodeSplitter(1000, 100)
    })

    test('should split JavaScript code into chunks of code and line no and return in string', async () => {
        const code = `
      function add(a, b) {
        return a + b;
      }
    `
        const fileExtension = 'js'

        const documents = await codeSplitter.splitCode(fileExtension, code)

        expect(documents).toContain(`// Line 2 - 4`)
        expect(documents).toContain(`function add(a, b) {`)
    })

    test('should return null for unsupported file extensions', async () => {
        const code = `
      def add(a, b):
          return a + b
    `
        const fileExtension = 'unsupported'

        const documents = await codeSplitter.splitCode(fileExtension, code)

        expect(documents).toBeNull()
    })
})
