# Repository Configuration for Python Program Collection
# This file configures which Python repositories to collect programs from
# All repositories listed here should contain Python (.py) files

# PRIORITY REPOSITORIES FOR FORMAL SPECIFICATION RESEARCH
# These Python repositories are optimized for formal specification generation
# Each repository contains Python functions suitable for Dafny specification generation
FORMAL_SPEC_PRIORITY_REPOS = {
    # Priority 1: Core Python repositories with excellent formal specification properties
    "priority_1": [
        "pyca/cryptography",        # Python cryptographic primitives with security properties
        "sympy/sympy",              # Python symbolic mathematics with precise definitions
        "networkx/networkx",        # Python graph algorithms with mathematical properties
        "lark-parser/lark",         # Python parser combinators with formal semantics
    ],
    
    # Priority 2: Supporting Python repositories with good specification amenability
    "priority_2": [
        "more-itertools/more-itertools",  # Python functional programming utilities
        "pydantic/pydantic",              # Python type-based data validation
        "grantjenks/python-sortedcontainers", # Python data structures with formal invariants
        "pytoolz/toolz",                  # Python functional programming
        "marshmallow-code/marshmallow",   # Python schema-based validation
        "keleshev/schema",                # Python declarative data validation
        "pyparsing/pyparsing",            # Python parser generators
        "python-jsonschema/jsonschema",   # Python JSON Schema validation
        "pallets/click",                  # Python CLI with clear contracts
        "HypothesisWorks/hypothesis",     # Python property-based testing
        "python-attrs/attrs",             # Python class generation with validation
    ]
}

# Your custom Python repositories (highest priority)
CUSTOM_REPOS = [
    # Add your specific Python repositories here
    # Format: "owner/repository-name"
    # Examples of Python repositories:
    "microsoft/vscode",            # Note: Contains some Python, but mostly TypeScript
    "google/python-fire",          # Python CLI library
    "openai/openai-python",        # Python OpenAI SDK
    "anthropic/anthropic-sdk-python",  # Python Anthropic SDK
    # Add more Python repositories as needed
]

# Python Web Development Repositories
WEB_REPOS = [
    "django/django",
    "pallets/flask", 
    "tiangolo/fastapi",
    "encode/django-rest-framework",
    "tornadoweb/tornado",
    "bottlepy/bottle",
    "falconry/falcon",
    "starlette/starlette",
]

# Data Science and Machine Learning
DATA_SCIENCE_REPOS = [
    "scikit-learn/scikit-learn",
    "pandas-dev/pandas", 
    "pytorch/pytorch",
    "tensorflow/tensorflow",
    "numpy/numpy",
    "scipy/scipy",
    "matplotlib/matplotlib",
    "plotly/plotly.py",
    "bokeh/bokeh",
    "altair-viz/altair",
    "seaborn/seaborn",
]

# Algorithm and Competitive Programming
ALGORITHM_REPOS = [
    "TheAlgorithms/Python",
    "keon/algorithms",
    "Garvit244/Leetcode",
    "kamyu104/LeetCode-Solutions",
    "qiyuangong/leetcode",
    "neetcode-gh/leetcode",
    "azl397985856/leetcode",
    "haoel/leetcode",
    "donnemartin/interactive-coding-challenges",
]

# DevOps and Automation
DEVOPS_REPOS = [
    "ansible/ansible",
    "fabric/fabric",
    "celery/celery",
    "docker/docker-py",
    "paramiko/paramiko",
]

# Testing and Quality Tools
TESTING_REPOS = [
    "pytest-dev/pytest",
    "python/mypy",
    "PyCQA/pylint",
    "psf/black",
    "PyCQA/flake8",
    "PyCQA/isort",
    "pre-commit/pre-commit",
]

# CLI and Utilities
UTILITY_REPOS = [
    "pallets/click",
    "google/python-fire",
    "microsoft/playwright-python",
    "pypa/pip",
    "pypa/setuptools",
    "pypa/virtualenv",
    "pypa/pipenv",
]

# Database and Storage
DATABASE_REPOS = [
    "sqlalchemy/sqlalchemy",
    "mongodb/mongo-python-driver",
    "redis/redis-py",
    "elastic/elasticsearch-py",
    "coleifer/peewee",
    "encode/orm",
]

# Networking and Web Scraping
NETWORKING_REPOS = [
    "psf/requests",
    "scrapy/scrapy",
    "aio-libs/aiohttp",
    "urllib3/urllib3",
    "kennethreitz/requests-html",
    "MechanicalSoup/MechanicalSoup",
]

# Scientific Computing
SCIENTIFIC_REPOS = [
    "sympy/sympy",
    "statsmodels/statsmodels",
    "pymc-devs/pymc",
    "scikit-image/scikit-image",
    "networkx/networkx",
    "dask/dask",
]

# Game Development and Graphics
GAME_REPOS = [
    "pygame/pygame",
    "panda3d/panda3d",
    "kivy/kivy",
]

# Security and Cryptography
SECURITY_REPOS = [
    "pyca/cryptography",
    "requests/requests-oauthlib",
    "lepture/authlib",
]

# Configuration options for different collection strategies
COLLECTION_STRATEGIES = {
    # Focus on formal specification research (NEW)
    "formal_spec_focused": {
        "categories": [
            ("formal_spec_priority_1", FORMAL_SPEC_PRIORITY_REPOS["priority_1"]),
            ("formal_spec_priority_2", FORMAL_SPEC_PRIORITY_REPOS["priority_2"]),
            ("scientific", SCIENTIFIC_REPOS),
            ("algorithms", ALGORITHM_REPOS[:3]),  # Limit algorithms to best 3
        ],
        "max_per_category": 10,
    },
    
    # Balanced collection across all categories
    "balanced": {
        "categories": [
            ("custom", CUSTOM_REPOS),
            ("web", WEB_REPOS),
            ("data_science", DATA_SCIENCE_REPOS),
            ("algorithms", ALGORITHM_REPOS),
            ("devops", DEVOPS_REPOS),
            ("testing", TESTING_REPOS),
            ("utilities", UTILITY_REPOS),
            ("database", DATABASE_REPOS),
            ("networking", NETWORKING_REPOS),
            ("scientific", SCIENTIFIC_REPOS),
        ],
        "max_per_category": 5,  # Max repos per category per batch
    },
    
    # Focus on algorithms and competitive programming
    "algorithms_focused": {
        "categories": [
            ("algorithms", ALGORITHM_REPOS),
            ("data_science", DATA_SCIENCE_REPOS),
            ("utilities", UTILITY_REPOS),
        ],
        "max_per_category": 8,
    },
    
    # Focus on web development
    "web_focused": {
        "categories": [
            ("web", WEB_REPOS),
            ("utilities", UTILITY_REPOS),
            ("database", DATABASE_REPOS),
            ("testing", TESTING_REPOS),
        ],
        "max_per_category": 6,
    },
    
    # Focus on data science and ML
    "data_science_focused": {
        "categories": [
            ("data_science", DATA_SCIENCE_REPOS),
            ("scientific", SCIENTIFIC_REPOS),
            ("algorithms", ALGORITHM_REPOS),
        ],
        "max_per_category": 8,
    },
    
    # Focus on AI and language models
    "ai_focused": {
        "categories": [
            ("custom", CUSTOM_REPOS),  # Includes OpenAI, Anthropic
            ("data_science", DATA_SCIENCE_REPOS),
            ("algorithms", ALGORITHM_REPOS),
        ],
        "max_per_category": 6,
    }
}

# Default strategy to use when none specified (Updated for formal spec research)
DEFAULT_STRATEGY = "formal_spec_focused"

def get_formal_spec_repos() -> list:
    """Get all priority repositories for formal specification research."""
    repos = []
    repos.extend(FORMAL_SPEC_PRIORITY_REPOS["priority_1"])
    repos.extend(FORMAL_SPEC_PRIORITY_REPOS["priority_2"])
    return repos

def get_repos_for_strategy(strategy_name: str = None) -> list:
    """Get repository list for a specific collection strategy."""
    if strategy_name is None:
        strategy_name = DEFAULT_STRATEGY
    
    if strategy_name not in COLLECTION_STRATEGIES:
        raise ValueError(f"Unknown strategy: {strategy_name}. Available: {list(COLLECTION_STRATEGIES.keys())}")
    
    strategy = COLLECTION_STRATEGIES[strategy_name]
    repos = []
    
    for category_name, category_repos in strategy["categories"]:
        max_repos = strategy["max_per_category"]
        repos.extend(category_repos[:max_repos])
    
    return repos

def get_all_repos() -> list:
    """Get all available repositories."""
    all_repos = []
    all_repos.extend(FORMAL_SPEC_PRIORITY_REPOS["priority_1"])
    all_repos.extend(FORMAL_SPEC_PRIORITY_REPOS["priority_2"])
    all_repos.extend(CUSTOM_REPOS)
    all_repos.extend(WEB_REPOS)
    all_repos.extend(DATA_SCIENCE_REPOS)
    all_repos.extend(ALGORITHM_REPOS)
    all_repos.extend(DEVOPS_REPOS)
    all_repos.extend(TESTING_REPOS)
    all_repos.extend(UTILITY_REPOS)
    all_repos.extend(DATABASE_REPOS)
    all_repos.extend(NETWORKING_REPOS)
    all_repos.extend(SCIENTIFIC_REPOS)
    all_repos.extend(GAME_REPOS)
    all_repos.extend(SECURITY_REPOS)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_repos = []
    for repo in all_repos:
        if repo and repo not in seen:
            seen.add(repo)
            unique_repos.append(repo)
    
    return unique_repos

def get_repo_categories() -> dict:
    """Get all repository categories for analysis."""
    return {
        "formal_spec_priority_1": FORMAL_SPEC_PRIORITY_REPOS["priority_1"],
        "formal_spec_priority_2": FORMAL_SPEC_PRIORITY_REPOS["priority_2"],
        "custom": CUSTOM_REPOS,
        "web": WEB_REPOS,
        "data_science": DATA_SCIENCE_REPOS,
        "algorithms": ALGORITHM_REPOS,
        "devops": DEVOPS_REPOS,
        "testing": TESTING_REPOS,
        "utilities": UTILITY_REPOS,
        "database": DATABASE_REPOS,
        "networking": NETWORKING_REPOS,
        "scientific": SCIENTIFIC_REPOS,
        "game": GAME_REPOS,
        "security": SECURITY_REPOS,
    }

def print_repository_summary():
    """Print a summary of all available repositories."""
    categories = get_repo_categories()
    
    print("Repository Configuration Summary")
    print("=" * 50)
    
    total_repos = 0
    for category, repos in categories.items():
        count = len(repos)
        total_repos += count
        print(f"{category:25}: {count:3} repositories")
    
    print("=" * 50)
    print(f"{'Total':25}: {total_repos:3} repositories")
    
    print(f"\nFormal Specification Priority Repositories:")
    print(f"  Priority 1: {len(FORMAL_SPEC_PRIORITY_REPOS['priority_1'])} repositories")
    print(f"  Priority 2: {len(FORMAL_SPEC_PRIORITY_REPOS['priority_2'])} repositories")
    print(f"  Total Priority: {len(get_formal_spec_repos())} repositories")
