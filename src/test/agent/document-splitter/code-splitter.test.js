import CodeSplitter from '@/agent/document-splitter/code-splitter';

describe('CodeSplitter', () => {
  let codeSplitter;

  beforeEach(() => {
    codeSplitter = new CodeSplitter(1000, 100);
  });

  test('should split JavaScript code into chunks', async () => {
    const code = `
      function add(a, b) {
        return a + b;
      }
    `;
    const fileExtension = 'js';

    const documents = await codeSplitter.splitCode(fileExtension, code);

    expect(documents).toHaveLength(1);
    expect(documents[0].pageContent).toContain('function add(a, b)');
  });

  test('should return null for unsupported file extensions', async () => {
    const code = `
      def add(a, b):
          return a + b
    `;
    const fileExtension = 'unsupported';

    const documents = await codeSplitter.splitCode(fileExtension, code);

    expect(documents).toBeNull();
  });
});