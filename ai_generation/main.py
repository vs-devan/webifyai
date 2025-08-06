import os
import sys
import logging
import traceback
from pathlib import Path
from typing import Dict, Optional, List
from crewai import Agent, Task, Crew, Process, LLM
from configs.prompts import PLANNER_PROMPT, FRONTEND_PROMPT, BACKEND_PROMPT, INTEGRATOR_PROMPT, VERIFIER_PROMPT, FIXER_PROMPT
from agents.planner import get_planner_agent
from agents.verifier import get_verifier_agent
from tools.file_tools import read_file, write_file, list_files
from utils.file_utils import collect_files
from utils.validation import validate_description, validate_generated_files
from utils.logger import setup_logger

class MERNCodeGenerator:
    """Enhanced MERN code generation system with robust error handling and validation."""
    
    def __init__(self, reasoning_model: str = "ollama/granite3.3:2b", 
                 coding_model: str = "ollama/qwen2.5-coder:7b",
                 outputs_dir: Optional[str] = None):
        """
        Initialize the MERN code generator.
        
        Args:
            reasoning_model: Model for planning and reasoning tasks
            coding_model: Model for code generation tasks
            outputs_dir: Custom output directory (defaults to ./outputs)
        """
        self.logger = setup_logger(__name__)
        self.reasoning_model = reasoning_model
        self.coding_model = coding_model
        
        # Setup directories with proper path handling
        self.outputs_dir = Path(outputs_dir or "outputs").resolve().as_posix()  # .as_posix() forces /
        self.plan_file = (Path(self.outputs_dir) / "plan.txt").as_posix()
        self.issues_file = (Path(self.outputs_dir) / "issues.txt").as_posix()
        self.generation_log = (Path(self.outputs_dir) / "generation.log").as_posix()
        
        # Configuration
        self.max_iterations = 3
        self.max_retries = 3
        
        # Initialize LLMs with enhanced error handling
        self.reasoning_llm = self._create_llm(reasoning_model, temperature=0.0, max_tokens=4000)
        self.coding_llm = self._create_llm(coding_model, temperature=0.1, max_tokens=8000)
        
        # Initialize agents
        self._initialize_agents()
        
    def _create_llm(self, model: str, temperature: float, max_tokens: int) -> LLM:
        """Create LLM instance with error handling."""
        try:
            return LLM(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=600
            )
        except Exception as e:
            self.logger.error(f"Failed to create LLM {model}: {e}")
            raise
    
    def _initialize_agents(self):
        """Initialize all agents with enhanced configuration."""
        try:
            # Coding agents with enhanced tool integration
            self.frontend_agent = Agent(
                role="Frontend Developer",
                goal="Generate complete React frontend with responsive design and proper error handling",
                backstory="Senior React developer with expertise in modern hooks, responsive design, and accessibility.",
                llm=self.coding_llm,
                tools=[read_file, write_file, list_files],
                verbose=True,
                allow_delegation=False,
                max_iter=25,
                max_execution_time=1200
            )
            
            self.backend_agent = Agent(
                role="Backend Developer", 
                goal="Generate robust Express.js backend with proper validation, error handling, and security",
                backstory="Senior Node.js developer with expertise in Express, MongoDB, authentication, and API security.",
                llm=self.coding_llm,
                tools=[read_file, write_file, list_files],
                verbose=True,
                allow_delegation=False,
                max_iter=25,
                max_execution_time=1200
            )
            
            self.integrator_agent = Agent(
                role="Integration Specialist",
                goal="Generate comprehensive configuration and deployment files",
                backstory="DevOps expert specializing in MERN stack deployment, Docker, and CI/CD pipelines.",
                llm=self.coding_llm,
                tools=[read_file, write_file, list_files],
                verbose=True,
                allow_delegation=False,
                max_iter=20,
                max_execution_time=900
            )
            
            self.reasoning_agent = Agent(
                role="Technical Architect",
                goal="Analyze requirements and provide precise technical guidance",
                backstory="Senior technical architect with deep expertise in full-stack development and system design.",
                llm=self.reasoning_llm,
                tools=[read_file, list_files],
                verbose=True,
                allow_delegation=False,
                max_iter=15,
                max_execution_time=600
            )
            
            # Get specialized agents
            self.verifier_agent = get_verifier_agent(self.reasoning_llm)
            self.planner_agent = get_planner_agent(self.reasoning_llm)
            
        except Exception as e:
            self.logger.error(f"Failed to initialize agents: {e}")
            raise
    
    def generate_mern_code(self, description: str) -> Dict[str, str]:
        """
        Generate MERN stack code from description with comprehensive error handling.
        
        Args:
            description: Application description
            
        Returns:
            Dictionary of generated files {filename: content}
        """
        try:
            # Validate input
            validation_result = validate_description(description)
            if not validation_result["valid"]:
                raise ValueError(f"Invalid description: {validation_result['errors']}")
            
            self.logger.info("🚀 Starting MERN Code Generation...")
            self.logger.info(f"Output directory: {self.outputs_dir}")
            
            # Phase 1: Planning
            self._execute_planning_phase(description)
            
            # Phase 2-5: Generation and Verification Loop
            files_dict = self._execute_generation_loop()
            
            # Final validation
            validation_result = validate_generated_files(files_dict)
            if not validation_result["valid"]:
                self.logger.warning(f"Generated files validation warnings: {validation_result['warnings']}")
            
            self.logger.info("🎉 MERN code generation completed successfully!")
            return files_dict
            
        except Exception as e:
            self.logger.error(f"Code generation failed: {e}")
            self.logger.error(traceback.format_exc())
            raise
    
    def _execute_planning_phase(self, description: str):
        """Execute the planning phase with retry logic."""
        self.logger.info("📝 Phase 1: Planning...")
        
        plan_task = Task(
            description=PLANNER_PROMPT.format(description=description).replace("\\", "/"),
            expected_output="Comprehensive MERN application architecture plan",
            agent=self.planner_agent
        )
        
        for attempt in range(self.max_retries):
            try:
                planner_crew = Crew(
                    agents=[self.planner_agent], 
                    tasks=[plan_task], 
                    verbose=True,
                    process=Process.sequential
                )
                
                result = planner_crew.kickoff()
                plan_content = result.raw.strip() if hasattr(result, 'raw') else str(result).strip()
                
                if not plan_content or len(plan_content) < 100:
                    raise ValueError("Generated plan is too short or empty")
                
                # Write plan with proper encoding
                with open(self.plan_file, 'w', encoding='utf-8') as f:
                    f.write(plan_content)
                
                self.logger.info("✅ Planning completed successfully")
                return
                
            except Exception as e:
                self.logger.warning(f"Planning attempt {attempt+1}/{self.max_retries} failed: {e}")
                if attempt == self.max_retries - 1:
                    raise ValueError(f"Planning failed after {self.max_retries} attempts: {e}")
    
    def _execute_generation_loop(self) -> Dict[str, str]:
        """Execute the main generation and verification loop."""
        verified = False
        files_generated = False
        
        for iteration in range(self.max_iterations):
            self.logger.info(f"🔄 Starting Iteration {iteration + 1}/{self.max_iterations}")
            
            try:
                if not files_generated:
                    self._generate_initial_files()
                    files_generated = True
                else:
                    self._apply_fixes()
                
                # Verification phase
                verified = self._execute_verification_phase(iteration)
                
                if verified:
                    break
                    
            except Exception as e:
                self.logger.error(f"Iteration {iteration + 1} failed: {e}")
                if iteration == self.max_iterations - 1:
                    raise
        
        if not verified:
            raise ValueError(f"Generation failed after {self.max_iterations} iterations. Check {self.issues_file}")
        
        return collect_files(str(self.outputs_dir))
    
    def _generate_initial_files(self):
        """Generate initial files for all components."""
        phases = [
            ("⚛️ Frontend Generation", self.frontend_agent, FRONTEND_PROMPT.replace("\\", "/")),
            ("🖥️ Backend Generation", self.backend_agent, BACKEND_PROMPT.replace("\\", "/")), 
            ("🔧 Integration Files", self.integrator_agent, INTEGRATOR_PROMPT.replace("\\", "/"))
        ]
        
        for phase_name, agent, prompt_template in phases:
            self.logger.info(f"{phase_name}...")
            
            task = Task(
                description=prompt_template.format(
                    plan_file=str(self.plan_file),
                    issues_file=str(self.issues_file),
                    temp_dir=str(self.outputs_dir)
                ),
                expected_output=f"{agent.role} files generated successfully",
                agent=agent
            )
            
            crew = Crew(
                agents=[agent], 
                tasks=[task], 
                verbose=True,
                process=Process.sequential
            )
            
            try:
                crew.kickoff()
                self.logger.info(f"✅ {phase_name} completed")
            except Exception as e:
                self.logger.error(f"{phase_name} failed: {e}")
                raise
    
    def _apply_fixes(self):
        """Apply fixes based on verification issues."""
        self.logger.info("🔧 Applying fixes based on verification issues...")
        
        if not self.issues_file.exists():
            self.logger.warning("No issues file found, skipping fixes")
            return
        
        try:
            with open(self.issues_file, 'r', encoding='utf-8') as f:
                issues_content = f.read()
            
            if not issues_content.strip():
                self.logger.warning("Issues file is empty, skipping fixes")
                return
            
            # Get fix instructions from reasoning agent
            fix_task = Task(
                description=FIXER_PROMPT.format(
                    issues_file=str(self.issues_file),
                    issues_content=issues_content,
                    temp_dir=str(self.outputs_dir),
                    plan_file=str(self.plan_file)
                ),
                expected_output="Detailed fix instructions for code generation agents",
                agent=self.reasoning_agent
            )
            
            fix_crew = Crew(
                agents=[self.reasoning_agent], 
                tasks=[fix_task], 
                verbose=True
            )
            
            result = fix_crew.kickoff()
            fix_instructions = result.raw if hasattr(result, 'raw') else str(result)
            
            # Apply fixes through all agents
            agents_and_prompts = [
                (self.frontend_agent, FRONTEND_PROMPT.replace("\\", "/")),
                (self.backend_agent, BACKEND_PROMPT.replace("\\", "/")),
                (self.integrator_agent, INTEGRATOR_PROMPT.replace("\\", "/"))
            ]
            
            for agent, prompt_template in agents_and_prompts:
                task_description = prompt_template.format(
                    plan_file=str(self.plan_file),
                    issues_file=str(self.issues_file),
                    temp_dir=str(self.outputs_dir)
                )
                task_description += f"\n\n🔧 CRITICAL FIX INSTRUCTIONS:\n{fix_instructions}"
                
                task = Task(
                    description=task_description,
                    expected_output=f"{agent.role} fixes applied",
                    agent=agent
                )
                
                crew = Crew(agents=[agent], tasks=[task], verbose=True)
                crew.kickoff()
                
        except Exception as e:
            self.logger.error(f"Fix application failed: {e}")
            raise
    
    def _execute_verification_phase(self, iteration: int) -> bool:
        """Execute verification and return whether all files are verified."""
        self.logger.info("🔍 Verification Phase...")
        
        try:
            verifier_task = Task(
                description=VERIFIER_PROMPT.format(
                    plan_file=str(self.plan_file),
                    temp_dir=str(self.outputs_dir)
                ).replace("\\", "/"),
                expected_output="Complete verification report",
                agent=self.verifier_agent
            )
            
            verifier_crew = Crew(
                agents=[self.verifier_agent], 
                tasks=[verifier_task], 
                verbose=True
            )
            
            result = verifier_crew.kickoff()
            verification_result = result.raw if hasattr(result, 'raw') else str(result)
            
            # Enhanced verification logic
            if self._is_verification_successful(verification_result):
                self.logger.info("✅ All files verified successfully!")
                return True
            else:
                self.logger.warning(f"❌ Issues found in iteration {iteration + 1}")
                
                # Save issues for next iteration
                with open(self.issues_file, 'w', encoding='utf-8') as f:
                    f.write(f"Iteration {iteration + 1} Issues:\n{verification_result}\n\n")
                
                return False
                
        except Exception as e:
            self.logger.error(f"Verification failed: {e}")
            return False
    
    def _is_verification_successful(self, result: str) -> bool:
        """Enhanced verification result analysis."""
        result_lower = result.lower()
        success_indicators = ["verified", "success", "complete", "all files"]
        failure_indicators = ["issues", "error", "missing", "failed", "problem"]
        
        has_success = any(indicator in result_lower for indicator in success_indicators)
        has_failure = any(indicator in result_lower for indicator in failure_indicators)
        
        return has_success and not has_failure
def main():
    """Enhanced main function with better error handling and examples."""
    try:
        # Initialize generator
        generator = MERNCodeGenerator()
        
        # Sample descriptions for testing
        sample_descriptions = {
            "calculator": """Build a calculator web app using the MERN stack (MongoDB, Express.js, React, Node.js). 
            The app should perform basic arithmetic operations (+, −, ×, ÷), support decimals, negation, clear,
            backspace, and equals functions. It should accept both button and keyboard inputs.

            The frontend will be built using React with a clean, responsive UI that works on mobile and desktop.
            The backend will use Node.js and Express to handle API requests with proper validation and error handling.
            Calculation history should be stored in MongoDB and displayed in the UI with options to clear history.

            Include API endpoints to fetch, add, and delete calculation history. Implement proper error boundaries,
            loading states, and user feedback. Support light/dark mode toggle and ensure accessibility compliance.
            Include comprehensive testing setup and deployment configuration.""",
            
            "todo": """Create a Todo List application using the MERN stack with user authentication.
            Users should be able to register, login, create todos, mark as complete, edit, delete, and organize
            by categories. Include priority levels, due dates, and search functionality.
            
            Frontend: React with modern hooks, responsive design, drag-and-drop reordering, real-time updates.
            Backend: Express.js with JWT authentication, input validation, rate limiting, and RESTful APIs.
            Database: MongoDB with user and todo models, proper indexing for performance.
            
            Include features like task filtering, bulk operations, data export, and offline capability.
            Implement comprehensive error handling, security measures, and deployment configuration.""",
            
            "blog": """Build a full-featured blog platform using the MERN stack with rich text editing.
            Support multiple authors, categories, tags, comments, and social sharing.
            
            Features: User authentication, role-based permissions, rich text editor, image uploads,
            comment system with moderation, search and filtering, SEO optimization, analytics dashboard.
            
            Frontend: React with modern UI components, responsive design, infinite scrolling, syntax highlighting.
            Backend: Express.js with file upload handling, email notifications, caching, and API rate limiting.
            Database: MongoDB with optimized schemas for posts, users, comments, and analytics.
            
            Include admin panel, content management, automated backups, and comprehensive deployment setup."""
        }
        
        # Interactive mode
        print("🚀 Enhanced MERN Stack Code Generator")
        print("=" * 50)
        
        print("\nAvailable sample projects:")
        for key, desc in sample_descriptions.items():
            preview = desc.split('.')[0] + "..."
            print(f"  {key}: {preview}")
        
        print("\nOptions:")
        print("1. Use a sample project (enter: calculator, todo, or blog)")
        print("2. Enter custom description")
        print("3. Exit")
        
        choice = input("\nYour choice: ").strip().lower()
        
        if choice in sample_descriptions:
            description = sample_descriptions[choice]
            print(f"\n📝 Using {choice} sample project")
        elif choice == "exit" or choice == "3":
            print("👋 Goodbye!")
            return
        elif choice == "2" or choice == "custom":
            print("\n📝 Enter your project description (minimum 20 characters):")
            description = input().strip()
            if len(description) < 20:
                print("❌ Description too short. Please provide more details.")
                return
        else:
            print("❌ Invalid choice. Using calculator sample.")
            description = sample_descriptions["calculator"]
        
        # Generate code
        print("\n" + "="*60)
        print("🔨 Starting code generation...")
        print("="*60)
        
        files_dict = generator.generate_mern_code(description)
        
        # Display results
        print("\n" + "="*60)
        print("✅ CODE GENERATION COMPLETED!")
        print("="*60)
        
        print(f"\n📊 Generated {len(files_dict)} files:")
        
        # Categorize files
        categories = {
            "Frontend": [],
            "Backend": [], 
            "Configuration": [],
            "Documentation": [],
            "Other": []
        }
        
        for filename in sorted(files_dict.keys()):
            if any(x in filename.lower() for x in ['src/', 'public/', 'components/', 'pages/']):
                categories["Frontend"].append(filename)
            elif any(x in filename.lower() for x in ['server', 'models/', 'routes/', 'middleware/']):
                categories["Backend"].append(filename)
            elif any(x in filename.lower() for x in ['package.json', '.env', 'vercel', 'docker']):
                categories["Configuration"].append(filename)
            elif any(x in filename.lower() for x in ['readme', '.md', 'docs/']):
                categories["Documentation"].append(filename)
            else:
                categories["Other"].append(filename)
        
        for category, files in categories.items():
            if files:
                print(f"\n🗂️  {category}:")
                for filename in files:
                    file_size = len(files_dict[filename])
                    print(f"   📄 {filename} ({file_size:,} characters)")
        
        # Show key insights
        total_lines = sum(content.count('\n') + 1 for content in files_dict.values())
        total_chars = sum(len(content) for content in files_dict.values())
        
        print(f"\n📈 Statistics:")
        print(f"   📝 Total lines of code: {total_lines:,}")
        print(f"   💾 Total characters: {total_chars:,}")
        print(f"   📁 Output directory: {generator.outputs_dir}")
        
        # Validation summary
        validation = validate_generated_files(files_dict)
        if validation["valid"]:
            print("✅ All validations passed!")
        else:
            print("⚠️  Validation issues found:")
            for error in validation["errors"]:
                print(f"   ❌ {error}")
        
        if validation["warnings"]:
            print("⚠️  Warnings:")
            for warning in validation["warnings"]:
                print(f"   ⚠️  {warning}")
        
        print(f"\n🚀 Next steps:")
        print(f"   1. Navigate to: {generator.outputs_dir}")
        print(f"   2. Install dependencies: npm install")
        print(f"   3. Set up environment variables (check .env.example)")
        print(f"   4. Start development: npm run dev")
        
        return files_dict
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Generation cancelled by user")
        return None
    except Exception as e:
        print(f"\n❌ Generation failed: {e}")
        logging.exception("Generation failed")
        return None

# Additional utility functions
def analyze_project_complexity(description: str) :
    """Analyze project complexity to adjust generation parameters."""
    complexity_indicators = {
        "authentication": 2,
        "real-time": 3,
        "payment": 4,
        "admin": 2,
        "dashboard": 3,
        "analytics": 3,
        "notifications": 2,
        "file upload": 2,
        "search": 2,
        "social": 3,
        "chat": 4,
        "video": 4,
        "ai": 5,
        "machine learning": 5
    }
    
    desc_lower = description.lower()
    complexity_score = 1
    features = []
    
    for feature, score in complexity_indicators.items():
        if feature in desc_lower:
            complexity_score += score
            features.append(feature)
    
    complexity_level = "Simple"
    if complexity_score > 10:
        complexity_level = "Complex"
    elif complexity_score > 5:
        complexity_level = "Moderate"
    
    return {
        "score": complexity_score,
        "level": complexity_level,
        "detected_features": features,
        "estimated_files": min(50, 10 + complexity_score * 2),
        "estimated_time": f"{5 + complexity_score}+ minutes"
    }

def create_project_summary(files_dict: Dict[str, str], description: str) -> str:
    """Create a comprehensive project summary."""
    complexity = analyze_project_complexity(description)
    
    summary = f"""
# Project Generation Summary

## Overview
- **Complexity Level**: {complexity['level']} ({complexity['score']} points)
- **Detected Features**: {', '.join(complexity['detected_features']) or 'Basic MERN stack'}
- **Files Generated**: {len(files_dict)}
- **Total Lines**: {sum(content.count('\\n') + 1 for content in files_dict.values()):,}

## Architecture

### Frontend (React)
- Modern functional components with hooks
- Responsive design with CSS Grid/Flexbox
- Component-based architecture
- State management and error boundaries

### Backend (Express.js)
- RESTful API design
- Middleware stack for security
- Input validation and error handling
- MongoDB integration with Mongoose

### Database (MongoDB)
- Optimized schemas and indexing
- Data validation at model level
- Relationship management

## Key Features
{chr(10).join(f'- {feature.title()}' for feature in complexity['detected_features'])}

## Security Implementations
- CORS configuration
- Input sanitization
- Rate limiting
- Environment variable management
- Secure headers

## Development Setup
1. Install dependencies: `npm install`
2. Configure environment variables
3. Start MongoDB service
4. Run development server: `npm run dev`

## Deployment Ready
- Production build scripts
- Environment configuration
- Deployment manifests included
"""
    return summary.strip()

# Export enhanced classes and functions
__all__ = [
    'MERNCodeGenerator',
    'validate_description', 
    'validate_generated_files',
    'analyze_project_complexity',
    'create_project_summary',
    'setup_logger',
    'main'
]

if __name__ == "__main__":
    try:
        result = main()
        if result:
            print("\n🎉 Generation completed successfully!")
        else:
            print("\n❌ Generation was cancelled or failed")
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        import traceback
        traceback.print_exc() 