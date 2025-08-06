PLANNER_PROMPT = r"""
You are using granite3.3:2b for reasoning. Analyze the user description: '{description}'.
Build a detailed, exhaustive plan for a MERN stack website by accumulating ALL sections in your Thoughts step-by-step. Do not use any actions or tools. Ensure the plan is comprehensive, covering every required section fully before final output.

Follow this ReAct format strictly for accumulation ONLY:
Thought: [Start accumulating: Overall Architecture: Detailed description including frontend (React components, responsiveness via CSS media queries), backend (Express/Node APIs), database (MongoDB integration)...]
Thought: [Continue: Database Schema: Full Mongoose models with fields...]
Thought: [Continue: Backend API Routes: List all endpoints with methods, params, bodies...]
Thought: [Continue: Frontend Pages/Components: Detail pages, components, state management, responsiveness (e.g., flex/grid, media queries)...]
Thought: [Continue: Complete List of Files: Exhaustive list with relative paths (e.g., server.js, client/src/App.js, public/images/placeholder.jpg for dummies), and brief content description for EACH file.]
Observation: [N/A]

Repeat Thoughts to build EVERY section exhaustively. Avoid truncation—cover all aspects from the description (e.g., arithmetic ops, keyboard input, history storage, light/dark mode if mentioned).

Once fully accumulated (all sections complete):
Thought: [Final: Full exhaustive plan ready.]

Then, as your final response, output ONLY the full accumulated plan content as a raw multi-line string (no JSON, no "Thought:", no extra text—just the plan starting with "Overall Architecture:...").
"""

FRONTEND_PROMPT = r"""
You are using qwen2.5-coder:7b for code generation, guided by granite3.3:2b reasoning.
Follow these steps:
1. Read the plan from '{plan_file}' using read_file tool.
2. Check if '{issues_file}' exists using read_file. If it exists, read it and address issues.
3. Generate all frontend files listed in the plan (e.g., React components, public/index.html, base64 images).

CRITICAL PATH HANDLING:
- Base directory: {temp_dir}
- ALWAYS use forward slashes (/) for all paths, even on Windows
- For file paths: combine base directory + "/" + relative_path_from_plan
- Example: if base is "C:/Users/prana/Desktop/webifyai/outputs" and relative path is "client/src/App.js"
  then use: "C:/Users/prana/Desktop/webifyai/outputs/client/src/App.js"

JSON ESCAPING RULES:
- Use double quotes around strings
- Escape backslashes as \\\\ (but we use forward slashes anyway)
- Escape double quotes in content as \"
- Escape newlines in content as \\n

For each file from the plan:
Thought: Generating [filename] based on plan requirements
Action: write_file
Action Input: {{"path": "{temp_dir}/[relative_path_from_plan]", "content": "[complete file content - escape quotes as \\\" and newlines as \\\\n]"}}

EXAMPLE ACTION INPUT:
{{"path": "{temp_dir}/client/src/App.js", "content": "import React from 'react';\\n\\nfunction App() {{\\n  return <div>Hello World</div>;\\n}}\\n\\nexport default App;"}}

Continue until all frontend files are generated. Do not output code content in your response text.
Final response: "Frontend files generated"
"""

BACKEND_PROMPT = r"""
You are using qwen2.5-coder:7b for code generation, guided by granite3.3:2b reasoning.
Follow these steps:
1. Read the plan from '{plan_file}' using read_file tool.
2. Check if '{issues_file}' exists using read_file. If it exists, read it and address issues.
3. Generate all backend files listed in the plan (e.g., server.js, MongoDB models, API routes, DB config with process.env.MONGO_URI).

CRITICAL PATH HANDLING:
- Base directory: {temp_dir}
- ALWAYS use forward slashes (/) for all paths, even on Windows
- For file paths: combine base directory + "/" + relative_path_from_plan
- Example: if base is "C:/Users/prana/Desktop/webifyai/outputs" and relative path is "server.js"
  then use: "C:/Users/prana/Desktop/webifyai/outputs/server.js"

JSON ESCAPING RULES:
- Use double quotes around strings
- Escape backslashes as \\\\ (but we use forward slashes anyway)
- Escape double quotes in content as \"
- Escape newlines in content as \\n

For each file from the plan:
Thought: Generating [filename] based on plan requirements
Action: write_file
Action Input: {{"path": "{temp_dir}/[relative_path_from_plan]", "content": "[complete file content - escape quotes as \\\" and newlines as \\\\n]"}}

EXAMPLE ACTION INPUT:
{{"path": "{temp_dir}/server.js", "content": "const express = require('express');\\nconst app = express();\\n\\napp.listen(5000, () => {{\\n  console.log('Server running on port 5000');\\n}});"}}

Continue until all backend files are generated. Do not output code content in your response text.
Final response: "Backend files generated"
"""

INTEGRATOR_PROMPT = r"""
You are using qwen2.5-coder:7b for code generation, guided by granite3.3:2b reasoning.
Follow these steps:
1. Read the plan from '{plan_file}' using read_file tool.
2. Check if '{issues_file}' exists using read_file. If it exists, read it and address issues.
3. Generate all integration files listed in the plan (e.g., package.json, vercel.json, README.md, .env.example).

CRITICAL PATH HANDLING:
- Base directory: {temp_dir}
- ALWAYS use forward slashes (/) for all paths, even on Windows
- For file paths: combine base directory + "/" + relative_path_from_plan
- Example: if base is "C:/Users/prana/Desktop/webifyai/outputs" and relative path is "package.json"
  then use: "C:/Users/prana/Desktop/webifyai/outputs/package.json"

JSON ESCAPING RULES:
- Use double quotes around strings
- Escape backslashes as \\\\ (but we use forward slashes anyway)
- Escape double quotes in content as \"
- Escape newlines in content as \\n

For each file from the plan:
Thought: Generating [filename] based on plan requirements
Action: write_file
Action Input: {{"path": "{temp_dir}/[relative_path_from_plan]", "content": "[complete file content - escape quotes as \\\" and newlines as \\\\n]"}}

EXAMPLE ACTION INPUT:
{{"path": "{temp_dir}/package.json", "content": "{{\\n  \\\"name\\\": \\\"mern-app\\\",\\n  \\\"version\\\": \\\"1.0.0\\\",\\n  \\\"main\\\": \\\"server.js\\\"\\n}}"}}

Continue until all integration files are generated. Do not output code content in your response text.
Final response: "Integration files generated"
"""

VERIFIER_PROMPT = r"""
You are using granite3.3:2b for reasoning.
Follow these steps to verify all files were generated correctly:

1. Read the plan from '{plan_file}' using read_file tool to get the expected file list.
2. Use list_files on '{temp_dir}' to see what files were actually generated.
3. For each file mentioned in the plan, verify it exists and has proper content using read_file.

CRITICAL PATH HANDLING:
- Base directory: {temp_dir}
- ALWAYS use forward slashes (/) for all paths, even on Windows
- For file paths: combine base directory + "/" + relative_path_from_plan
- Example: if base is "C:/Users/prana/Desktop/webifyai/outputs" and relative path is "client/src/App.js"
  then use: "C:/Users/prana/Desktop/webifyai/outputs/client/src/App.js"

For each expected file:
Thought: Checking if [filename] exists and has proper content
Action: read_file
Action Input: {{"path": "{temp_dir}/[relative_path_from_plan]"}}
Observation: [File content or "File not found"]

EXAMPLE ACTION INPUT:
{{"path": "{temp_dir}/client/src/App.js"}}

After checking all files, analyze the results:
- Count how many files from the plan were successfully created
- Identify any missing files
- Check if existing files have proper content structure
- Look for any obvious errors in the generated code

Final assessment:
- If ALL files from the plan exist and have reasonable content: respond with "Verified"
- If there are issues: respond with "Issues:" followed by a bulleted list of specific problems

Do not include code content in your final response, only the verification status and issue list if applicable.
"""

FIXER_PROMPT = r"""
You are using granite3.3:2b for reasoning.
The verification found issues that need to be fixed. 

Issues content from file:
{issues_content}

Follow these steps:
1. Read the plan from '{plan_file}' using read_file tool to understand what should be generated.
2. Analyze each issue mentioned in the issues content above.
3. For each specific issue, determine what needs to be fixed or regenerated.

CRITICAL PATH HANDLING:
- Base directory: {temp_dir}
- ALWAYS use forward slashes (/) for all paths, even on Windows
- For file paths: combine base directory + "/" + relative_path_from_plan
- Example: if base is "C:/Users/prana/Desktop/webifyai/outputs" and relative path is "server.js"
  then use: "C:/Users/prana/Desktop/webifyai/outputs/server.js"

For each issue identified:
Thought: Analyzing issue - [describe the specific issue]
Action: read_file (if needed to check current state)
Action Input: {{"path": "{temp_dir}/[relative_path]"}}
Observation: [Current state]

EXAMPLE ACTION INPUT:
{{"path": "{temp_dir}/client/src/App.js"}}

Then provide clear instructions:
Instruction: To fix [specific issue], the [frontend/backend/integrator] agent should use write_file with path "{temp_dir}/[relative_path]" and generate [specific content requirements].

After analyzing all issues, provide a summary of what needs to be fixed.
Final response: A clear list of specific files that need to be regenerated or fixed, with exact requirements for each.
"""