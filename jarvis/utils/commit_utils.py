import os
import subprocess
import re


def get_git_diff(all_changes=False):
    """Get git diff (staged by default, or all if --all)"""
    cmd = ["git", "diff", "--cached"]
    if all_changes:
        cmd = ["git", "diff"]
    try:
        diff = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode("utf-8")
        return diff.strip()
    except subprocess.CalledProcessError as e:
        return f"Error running git diff: {e.output.decode()}"


def rule_based_commit(diff: str) -> str:
    """Smarter fallback: generate commit messages using file type + keywords"""
    if not diff:
        return "chore: update files"

    # Extract changed file names
    changed_files = []
    for line in diff.splitlines():
        if line.startswith("+++ b/") or line.startswith("--- a/"):
            path = line.split(" ", 1)[-1].replace("+++ b/", "").replace("--- a/", "")
            changed_files.append(path)

    diff_lower = diff.lower()

    # Default type/scope
    commit_type, scope, message = "chore", None, "update project files"

    # Check keywords in diff content
    if "fix" in diff_lower or "bug" in diff_lower:
        commit_type, message = "fix", "resolve issue"
    elif "add" in diff_lower or "create" in diff_lower:
        commit_type, message = "feat", "add new functionality"
    elif "delete" in diff_lower or "remove" in diff_lower:
        commit_type, message = "chore", "remove unused code"
    elif "refactor" in diff_lower:
        commit_type, message = "refactor", "improve code structure"

    # Adjust based on file paths
    for f in changed_files:
        if f.endswith((".md", ".txt")):
            commit_type, scope, message = "docs", None, "update documentation"
        elif f.startswith("tests/") or f.endswith(("_test.py", "_test.js", "_spec.js")):
            commit_type, scope, message = "test", None, "add or update tests"
        elif f.endswith(("requirements.txt", "package.json", "setup.py")):
            commit_type, scope, message = "chore", None, "update dependencies"
        elif f.endswith((".py", ".js", ".java", ".cpp")) and commit_type == "chore":
            commit_type, message = "feat", "update source code"

    # Format Conventional Commit
    if scope:
        return f"{commit_type}({scope}): {message}"
    return f"{commit_type}: {message}"


def ai_commit_message(diff: str, scope=None) -> str:
    """Use AI (if API key available) to generate commit message"""
    api_key = os.getenv("OPENAI_API_KEY")
    project = os.getenv("OPENAI_PROJECT")  # optional project-scoped key

    if not api_key:
        return None  # No API key

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, project=project) if project else OpenAI(api_key=api_key)

        prompt = f"""
        Analyze the following git diff and generate a concise commit message 
        in Conventional Commit format (type(scope): message).
        Use: feat, fix, docs, style, refactor, test, chore.

        Diff:
        {diff}
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # try "gpt-3.5-turbo" if not available
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
            temperature=0.3,
        )

        message = response.choices[0].message.content.strip()
        if scope:
            # Insert scope if user provided one
            message = re.sub(
                r"^(feat|fix|docs|style|refactor|test|chore)(\([^)]*\))?:",
                rf"\1({scope}):",
                message,
            )
        return message

    except Exception as e:
        # Explicitly show why AI failed
        return f"[AI Fallback: {str(e)}] {rule_based_commit(diff)}"
