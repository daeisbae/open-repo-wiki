import sys
import os

# Add src directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.code_splitter import CodeSplitter

def test_code_splitter_overlap_drift():
    # Create a code string with known lines
    lines = [f"Line {i}" for i in range(1, 21)] # 20 lines
    code = "\n".join(lines)
    
    # Initialize splitter with small chunk size to force splits and overlap
    # Chunk size 7 lines, overlap 3 lines
    splitter = CodeSplitter(chunk_size=7, chunk_overlap=3)
    result = splitter.split_code('py', code)
    
    print("Original Code:")
    print(code)
    print("\nSplit Result:")
    print(result)
    
    # Check for correct line numbering
    # If drift happens, we might see "Line 5" labeled as "8: Line 5" or similar
    
    if "1: Line 1" in result:
        print("\nStart looks ok.")
    
    # Check a line in the middle/end
    # We expect "Line 15" to be labeled as "15: Line 15"
    if "15: Line 15" in result:
        print("SUCCESS: Line 15 is correctly labeled.")
    else:
        print("FAILURE: Line 15 is NOT correctly labeled.")
        # Find what it is labeled as
        import re
        match = re.search(r"(\d+): Line 15", result)
        if match:
            print(f"Found 'Line 15' labeled as: {match.group(1)}")

if __name__ == "__main__":
    test_code_splitter_overlap_drift()
