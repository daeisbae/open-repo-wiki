import LLMConfig from '@/llm/llm-config.js';

describe('LLMConfig', () => {
    describe('constructor validation', () => {
        it('should create instance with valid parameters', () => {
            const config = new LLMConfig(0.7, 0.9, 50, 1000);
            expect(config).toBeInstanceOf(LLMConfig);
        });

        it('should throw error for temperature < 0', () => {
            expect(() => new LLMConfig(-0.1, 0.9, 50, 1000))
                .toThrow('Temperature must be between 0.0 and 2.0');
        });

        it('should throw error for temperature > 2', () => {
            expect(() => new LLMConfig(2.1, 0.9, 50, 1000))
                .toThrow('Temperature must be between 0.0 and 2.0');
        });

    });
});