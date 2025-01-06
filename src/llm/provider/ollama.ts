import { ChatOllama } from '@langchain/ollama';
import LLMConfig from '../llm-config';
import { HistoryItem, LLMProvider } from '../llm-provider';

export class OllamaProvider extends LLMProvider {
  private llm: ChatOllama;

  constructor(
          modelName: string,
          llmconfig: LLMConfig) {
    super('', modelName, llmconfig, '');
    this.llm = new ChatOllama({
        model: modelName,
        temperature: llmconfig.temperature,
        format: 'json',
        topP: llmconfig.topP,
        topK: llmconfig.topK,
    });
  }

  async run(userPrompt: string, history: HistoryItem[]): Promise<string> {
    const response = await this.llm.invoke(userPrompt);
    console.log(response.content.toString());
    return response.content.toString();
  }
}