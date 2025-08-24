# Installation

To install QKDpy, you can use pip or uv:

## Using uv (recommended)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/yourusername/qkdpy.git
cd qkdpy

# Create a virtual environment
uv venv

# Install in development mode
uv pip install -e .
```

## Using pip

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .
```
