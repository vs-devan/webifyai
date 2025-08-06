import os
from crewai import Agent, Task, Crew, Process, LLM
from configs.prompts import PLANNER_PROMPT, FRONTEND_PROMPT, BACKEND_PROMPT, INTEGRATOR_PROMPT, VERIFIER_PROMPT, FIXER_PROMPT
from agents.planner import get_planner_agent
from agents.verifier import get_verifier_agent
from tools.file_tools import read_file, write_file, list_files
from utils.file_utils import collect_files

def generate_mern_code(description: str) -> dict:
    # Configure two LLMs with increased context window
    reasoning_llm = LLM(
        model="ollama/granite3.3:2b",
        temperature=0.0,  # Stricter output
        max_tokens=6000,  # Increased from 4000
        timeout=600,
        # Ollama-specific parameters to increase context window
        base_url="http://localhost:11434",
        api_key="ollama",
        model_kwargs={
            "num_ctx": 8192,  # Increase context window from default 4096
            "num_predict": 6000,  # Max tokens to predict
            "temperature": 0.0,
            "top_k": 40,
            "top_p": 0.9,
            "repeat_penalty": 1.1
        }
    )
    
    coding_llm = LLM(
        model="ollama/qwen2.5-coder:7b",
        temperature=0.1,  # Balanced coding
        max_tokens=10000,  # Increased from 8000
        timeout=600,
        # Ollama-specific parameters to increase context window
        base_url="http://localhost:11434",
        api_key="ollama",
        model_kwargs={
            "num_ctx": 16384,  # Larger context window for coding model
            "num_predict": 10000,  # Max tokens to predict
            "temperature": 0.1,
            "top_k": 40,
            "top_p": 0.9,
            "repeat_penalty": 1.1
        }
    )

    # Create agent instances
    frontend_agent = Agent(
        role="Frontend Developer",
        goal="Generate React frontend files per instructions",
        backstory="Expert React developer who follows precise instructions to generate complete files.",
        llm=coding_llm,
        tools=[read_file, write_file, list_files],
        verbose=True,
        allow_delegation=False,
        max_iter=25,  # Increased for tool chaining
        max_execution_time=1200  # Increased timeout
    )
    
    backend_agent = Agent(
        role="Backend Developer",
        goal="Generate Express.js backend files per instructions",
        backstory="Expert Node.js developer who follows precise instructions to generate complete files.",
        llm=coding_llm,
        tools=[read_file, write_file, list_files],
        verbose=True,
        allow_delegation=False,
        max_iter=25,
        max_execution_time=1200
    )
    
    integrator_agent = Agent(
        role="Integration Specialist",
        goal="Generate configuration files per instructions",
        backstory="DevOps expert who follows precise instructions to create configuration files.",
        llm=coding_llm,
        tools=[read_file, write_file, list_files],
        verbose=True,
        allow_delegation=False,
        max_iter=25,
        max_execution_time=1200
    )
    
    reasoning_agent = Agent(
        role="Reasoning Coordinator",
        goal="Analyze issues and provide precise code generation instructions",
        backstory="Expert in breaking down complex tasks into clear instructions for code generation.",
        llm=reasoning_llm,
        tools=[read_file, list_files],
        verbose=True,
        allow_delegation=False,
        max_iter=15,  # Increased
        max_execution_time=600
    )
    
    verifier_agent = get_verifier_agent(reasoning_llm)
    planner_agent = get_planner_agent(reasoning_llm)

    # Outputs directory with normalized paths - ensure absolute path and forward slashes
    outputs_dir = os.path.abspath(os.path.join(os.getcwd(), "outputs")).replace('\\', '/')
    os.makedirs(outputs_dir, exist_ok=True)
    
    # Use absolute paths for plan and issues files with forward slashes
    plan_file = os.path.join(outputs_dir, "plan.txt").replace('\\', '/')
    issues_file = os.path.join(outputs_dir, "issues.txt").replace('\\', '/')
    
    print(f"🚀 Starting MERN Code Generation...")
    print(f"📂 Working directory: {os.getcwd()}")
    print(f"📂 Outputs directory: {outputs_dir}")
    print(f"📄 Plan file: {plan_file}")
    print(f"📄 Issues file: {issues_file}")
    
    # Planning phase: Output raw content, write manually
    print("📝 Phase 1: Planning...")
    plan_task = Task(
        description=PLANNER_PROMPT.format(description=description),
        expected_output="Detailed MERN app plan as raw string",
        agent=planner_agent
    )
    planner_crew = Crew(
        agents=[planner_agent], 
        tasks=[plan_task], 
        verbose=True,
        process=Process.sequential
    )
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            plan_result = planner_crew.kickoff()
            plan_content = plan_result.raw.strip()
            
            # Write plan file manually with error handling
            with open(plan_file, 'w', encoding='utf-8') as f:
                f.write(plan_content)
            
            # Verify the plan was written correctly
            if os.path.exists(plan_file) and os.path.getsize(plan_file) > 0:
                print(f"✅ Planning completed - Plan file size: {os.path.getsize(plan_file)} bytes")
                break
            else:
                raise Exception("Plan file was not created properly")
                
        except Exception as e:
            print(f"❌ Planning attempt {attempt+1} failed: {str(e)}")
            if attempt == max_retries - 1:
                raise

    # Generation and verification loop
    max_iters = 3
    verified = False
    files_generated = False
    
    for iteration in range(max_iters):
        print(f"\n🔄 Starting Iteration {iteration + 1}/{max_iters}")
        
        if not files_generated:
            # Initial generation
            print("⚛️ Phase 2: Frontend Generation...")
            frontend_task = Task(
                description=FRONTEND_PROMPT.format(
                    plan_file=plan_file, 
                    issues_file=issues_file, 
                    temp_dir=outputs_dir
                ),
                expected_output="Frontend files generated",
                agent=frontend_agent
            )
            frontend_crew = Crew(
                agents=[frontend_agent], 
                tasks=[frontend_task], 
                verbose=True,
                process=Process.sequential
            )
            frontend_crew.kickoff()
            print("✅ Frontend generation completed")
            
            print("🖥️ Phase 3: Backend Generation...")
            backend_task = Task(
                description=BACKEND_PROMPT.format(
                    plan_file=plan_file, 
                    issues_file=issues_file, 
                    temp_dir=outputs_dir
                ),
                expected_output="Backend files generated",
                agent=backend_agent
            )
            backend_crew = Crew(
                agents=[backend_agent], 
                tasks=[backend_task], 
                verbose=True,
                process=Process.sequential
            )
            backend_crew.kickoff()
            print("✅ Backend generation completed")
            
            print("🔧 Phase 4: Integration Files...")
            integrator_task = Task(
                description=INTEGRATOR_PROMPT.format(
                    plan_file=plan_file, 
                    issues_file=issues_file, 
                    temp_dir=outputs_dir
                ),
                expected_output="Integration files generated",
                agent=integrator_agent
            )
            integrator_crew = Crew(
                agents=[integrator_agent], 
                tasks=[integrator_task], 
                verbose=True,
                process=Process.sequential
            )
            integrator_crew.kickoff()
            print("✅ Integration files completed")
            
            files_generated = True
            print("✅ Initial file generation completed")
            
            # List generated files for debugging
            try:
                generated_files = os.listdir(outputs_dir)
                print(f"📁 Generated files in {outputs_dir}: {generated_files}")
            except Exception as e:
                print(f"❌ Error listing generated files: {e}")
                
        else:
            # Fix specific issues
            print("🔧 Applying fixes based on previous verification...")
            if os.path.exists(issues_file):
                with open(issues_file, 'r', encoding='utf-8') as f:
                    issues_content = f.read()
                    
                fix_task = Task(
                    description=FIXER_PROMPT.format(
                        issues_file=issues_file,
                        issues_content=issues_content,
                        temp_dir=outputs_dir,
                        plan_file=plan_file
                    ),
                    expected_output="Instructions for fixing specific issues",
                    agent=reasoning_agent
                )
                fix_crew = Crew(
                    agents=[reasoning_agent], 
                    tasks=[fix_task], 
                    verbose=True,
                    process=Process.sequential
                )
                fix_result = fix_crew.kickoff()
                fix_instructions = fix_result.raw
                
                # Pass instructions to coding agents
                for agent, prompt in [
                    (frontend_agent, FRONTEND_PROMPT),
                    (backend_agent, BACKEND_PROMPT),
                    (integrator_agent, INTEGRATOR_PROMPT)
                ]:
                    task = Task(
                        description=f"{prompt.format(plan_file=plan_file, issues_file=issues_file, temp_dir=outputs_dir)}\n\nAdditional Instructions from Reasoning Agent:\n{fix_instructions}",
                        expected_output=f"{agent.role} files fixed",
                        agent=agent
                    )
                    crew = Crew(
                        agents=[agent], 
                        tasks=[task], 
                        verbose=True,
                        process=Process.sequential
                    )
                    crew.kickoff()

        # Verification phase
        print("🔍 Phase 5: Verification...")
        print(f"DEBUG: Verifier plan_file: {plan_file}")
        print(f"DEBUG: Verifier temp_dir: {outputs_dir}")
        
        # Ensure verifier has absolute paths
        verifier_task = Task(
            description=VERIFIER_PROMPT.format(
                plan_file=plan_file, 
                temp_dir=outputs_dir
            ),
            expected_output="Complete verification result",
            agent=verifier_agent
        )
        verifier_crew = Crew(
            agents=[verifier_agent], 
            tasks=[verifier_task], 
            verbose=True,
            process=Process.sequential
        )
        verifier_result = verifier_crew.kickoff()
        result = verifier_result.raw

        print(f"📋 Verification result: {result}")

        if "Verified" in result and "Issues" not in result:
            verified = True
            print("✅ All files verified successfully!")
            break
        else:
            print(f"❌ Issues found in iteration {iteration + 1}")
            with open(issues_file, 'w', encoding='utf-8') as f:
                f.write(f"Iteration {iteration + 1} Issues:\n{result}\n\n")

    if verified:
        print("🎉 MERN code generation completed successfully!")
        return collect_files(outputs_dir)
    else:
        print("❌ Generation failed after max iterations")
        print(f"📄 Check {issues_file} for detailed issues")
        
        # Still return the files even if not fully verified
        try:
            return collect_files(outputs_dir)
        except Exception as e:
            raise ValueError(f"Generation failed after max iterations and could not collect files: {e}")

# Test run
if __name__ == "__main__":
    sample_description = """Build a calculator web app using the MERN stack (MongoDB, Express.js, React, Node.js). The app should perform basic arithmetic operations (+, −, ×, ÷), support decimals, negation, clear, backspace, and equals functions. It should accept both button and keyboard inputs.

The frontend will be built using React with a clean, responsive UI. The backend will use Node.js and Express to handle API requests. Calculation history should be stored in MongoDB and displayed in the UI.

Include API endpoints to fetch, add, and delete history. Optionally, support light/dark mode and localStorage for session-based history if not using authentication."""
    
    try:
        files_dict = generate_mern_code(sample_description)
        print(f"\n📁 Generated {len(files_dict)} files:")
        for filename in files_dict.keys():
            print(f"  • {filename}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()