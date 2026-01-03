import subprocess
import os
import tempfile
from pathlib import Path

# --- List of common code file extensions to look for ---
CODE_FILE_EXTENSIONS = [
    "*.py",      # Python
    "*.js",      # JavaScript
    "*.jsx",     # React JSX
    "*.ts",      # TypeScript
    "*.tsx",     # React TSX
    "*.java",    # Java
    "*.go",      # Go
    "*.html",    # HTML
    "*.css",     # CSS
    "*.scss",    # SCSS
    "*.rb",      # Ruby
    "*.php",     # PHP
    "*.cs",      # C#
    "*.cpp",     # C++
    "*.c",       # C
    "*.h",       # C/C++ Header
    "*.swift",   # Swift
    "*.kt",      # Kotlin
    "*.rs",      # Rust
]

def get_code_from_repo(clone_url: str, commit_hash: str) -> str:
    """
    Clones a Git repository to a temporary directory, checks out a specific commit,
    and reads the content of all recognized coding files.

    Returns the concatenated content of all found files as a single string.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Cloning {clone_url} into temporary directory {temp_dir}...")

        try:
            # --- Git Clone ---
            # Using --depth 1 is efficient but requires fetching the specific commit later
            subprocess.run(
                ["git", "clone", "--depth", "1", clone_url, temp_dir], 
                check=True, capture_output=True, text=True
            )

            # --- Git Fetch & Checkout ---
            # Fetch the specific commit hash since a shallow clone might not include it
            subprocess.run(
                ["git", "fetch", "origin", commit_hash],
                cwd=temp_dir, check=False, capture_output=True, text=True # Use check=False to ignore errors if commit is already present
            )
            
            subprocess.run(
                ["git", "checkout", commit_hash], 
                cwd=temp_dir, check=True, capture_output=True, text=True
            )

            print(f"✅ Successfully checked out commit {commit_hash}.")
        except subprocess.CalledProcessError as e:
            # Provide a more detailed error message if a Git command fails
            raise RuntimeError(f"Git command failed:\n--- STDOUT ---\n{e.stdout}\n--- STDERR ---\n{e.stderr}")

        # --- Read File Contents ---
        all_code = []
        temp_path = Path(temp_dir)
        
        for extension in CODE_FILE_EXTENSIONS:
            for code_file in temp_path.rglob(extension):
                # Exclude files in .git directory
                if ".git" in str(code_file):
                    continue
                try:
                    header = f"# --- File: {code_file.relative_to(temp_dir)} ---\n"
                    content = code_file.read_text(encoding="utf-8")
                    all_code.append(header + content)
                except Exception as e:
                    print(f"⚠ Could not read file {code_file}: {e}")

        if not all_code:
            raise ValueError("❌ No recognized code files found in the repository.")

        return "\n\n".join(all_code)