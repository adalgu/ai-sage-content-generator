"""
Integration test script to verify the system is ready for MVP release
This script tests the core workflow without making actual API calls
"""

import os
import sys
from pathlib import Path


def check_file_exists(filepath, description):
    """Check if a required file exists"""
    if Path(filepath).exists():
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description} NOT FOUND: {filepath}")
        return False


def check_imports():
    """Check if all required modules can be imported"""
    required_modules = [
        ('streamlit', 'Streamlit'),
        ('langchain', 'LangChain'),
        ('langgraph', 'LangGraph'),
        ('langchain_anthropic', 'LangChain Anthropic'),
        ('anthropic', 'Anthropic SDK'),
        ('pydantic', 'Pydantic'),
        ('tiktoken', 'Tiktoken'),
        ('requests', 'Requests'),
        ('bs4', 'BeautifulSoup4'),
        ('dotenv', 'Python-dotenv'),
        ('notion_client', 'Notion Client'),
        ('pytest', 'Pytest'),
    ]

    all_imported = True
    print("\n=== Checking Python Modules ===")

    for module_name, description in required_modules:
        try:
            __import__(module_name)
            print(f"✓ {description} imported successfully")
        except ImportError as e:
            print(f"✗ {description} FAILED to import: {e}")
            all_imported = False

    return all_imported


def check_project_structure():
    """Check if all required project files exist"""
    print("\n=== Checking Project Structure ===")

    required_files = [
        ('README.md', 'README file'),
        ('TRD.md', 'Technical Requirements Document'),
        ('requirements.txt', 'Requirements file'),
        ('personas.json', 'Personas configuration'),
        ('main.py', 'Main CLI application'),
        ('app.py', 'Streamlit web application'),
        ('.env.example', 'Environment variables example'),
        ('.gitignore', 'Git ignore file'),
        ('test_unit.py', 'Unit tests'),
        ('test_integration.py', 'Integration tests'),
    ]

    all_exist = True
    for filepath, description in required_files:
        if not check_file_exists(filepath, description):
            all_exist = False

    return all_exist


def check_env_configuration():
    """Check environment configuration"""
    print("\n=== Checking Environment Configuration ===")

    # Check if .env exists
    env_exists = Path('.env').exists()

    if env_exists:
        print("✓ .env file exists")

        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()

        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        notion_token = os.getenv('NOTION_TOKEN')
        notion_db = os.getenv('NOTION_DATABASE_ID')

        if anthropic_key:
            print("✓ ANTHROPIC_API_KEY is set")
        else:
            print("⚠ ANTHROPIC_API_KEY is NOT set (required for API calls)")

        if notion_token and notion_db:
            print("✓ Notion credentials are set (optional)")
        else:
            print("ℹ Notion credentials are NOT set (optional feature)")

        return bool(anthropic_key)
    else:
        print("⚠ .env file does NOT exist")
        print("  Please copy .env.example to .env and configure your API keys")
        return False


def test_basic_functions():
    """Test basic functions without API calls"""
    print("\n=== Testing Basic Functions ===")

    try:
        from main import (
            count_tokens,
            calculate_cost,
            get_topic,
            load_personas,
        )

        # Test count_tokens
        tokens = count_tokens("Hello, world!")
        assert tokens > 0
        print(f"✓ count_tokens works (counted {tokens} tokens)")

        # Test calculate_cost
        cost = calculate_cost(1000, 1000, "claude-3-5-sonnet-20240620")
        assert cost > 0
        print(f"✓ calculate_cost works (calculated ${cost:.4f})")

        # Test get_topic
        topic = get_topic("AI Technology")
        assert topic == "AI Technology"
        print(f"✓ get_topic works (topic: {topic})")

        # Test load_personas
        personas = load_personas('personas.json')
        assert len(personas) > 0
        print(f"✓ load_personas works (loaded {len(personas)} personas)")

        return True

    except Exception as e:
        print(f"✗ Basic function tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_persona_validation():
    """Validate persona JSON structure"""
    print("\n=== Validating Personas ===")

    try:
        from main import load_personas

        personas = load_personas('personas.json')

        required_fields = ['name', 'instruction', 'color']

        for persona in personas:
            for field in required_fields:
                assert hasattr(persona, field), f"Persona missing field: {field}"

        print(f"✓ All {len(personas)} personas are valid")
        print(f"  Personas: {', '.join([p.name for p in personas])}")

        return True

    except Exception as e:
        print(f"✗ Persona validation FAILED: {e}")
        return False


def main():
    """Run all integration tests"""
    print("=" * 60)
    print("AI Sage Content Generator - Integration Test")
    print("=" * 60)

    results = []

    # Run all checks
    results.append(("Project Structure", check_project_structure()))
    results.append(("Python Modules", check_imports()))
    results.append(("Environment Config", check_env_configuration()))
    results.append(("Basic Functions", test_basic_functions()))
    results.append(("Persona Validation", test_persona_validation()))

    # Summary
    print("\n" + "=" * 60)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n🎉 ALL TESTS PASSED! System is ready for MVP release.")
        print("\nNext steps:")
        print("1. Configure your .env file with ANTHROPIC_API_KEY")
        print("2. Run 'streamlit run app.py' to start the web application")
        print("3. Or run 'python main.py' for CLI version")
        return 0
    else:
        print("\n⚠ SOME TESTS FAILED. Please fix the issues above.")
        print("\nCommon issues:")
        print("- Missing dependencies: Run 'pip install -r requirements.txt'")
        print("- Missing .env file: Copy .env.example to .env")
        print("- Missing API key: Add ANTHROPIC_API_KEY to .env file")
        return 1


if __name__ == "__main__":
    sys.exit(main())
