import sys
import os

# Add src directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.code_splitter import CodeSplitter

def test_code_splitter_line_numbering():
    code = """def hello_world():
    print("Hello, world!")
    return True
"""
    splitter = CodeSplitter(chunk_size=100, chunk_overlap=0)
    result = splitter.split_code('py', code)
    
    expected_output_part = """1: def hello_world():
2:     print("Hello, world!")
3:     return True"""
    
    print("Result:")
    print(result)
    
    if expected_output_part in result:
        print("\nSUCCESS: Line numbers are correctly prepended.")
    else:
        print("\nFAILURE: Line numbers are missing or incorrect.")

if __name__ == "__main__":
    test_code_splitter_line_numbering()
