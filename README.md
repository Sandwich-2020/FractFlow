# FractFlow

FractFlow is a fractal intelligence architecture that decomposes intelligence into nestable Agent-Tool units, building dynamically evolving distributed cognitive systems through recursive combinations.

## Design Philosophy

FractFlow is a fractal intelligence architecture that decomposes intelligence into nestable Agent-Tool units, building dynamically evolving distributed cognitive systems through recursive combinations.

Each agent not only has cognitive capabilities but also the ability to call other agents, forming a self-referential, self-organizing, and self-adaptive intelligence flow.

Similar to an octopus where each tentacle has its own brain in a collaborative structure, FractFlow achieves a structurally malleable and behaviorally evolving form of distributed intelligence through the combination and coordination of modular intelligence.

## Installation

Please install "uv" first with https://docs.astral.sh/uv/#installation

### Method 1: Local Installation

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### Method 2: Build and Install Package

```bash
python -m build 
```

Then you will get a dist folder, which can be installed with the following command:

```bash
uv pip install dist/FractFlow-0.1.0-py3-none-any.whl
```

### Method 3: Development Mode Installation

For development purposes, you can install the package in development mode. This allows you to modify the code without reinstalling the package:

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
pip install -e .
```

After installation, you can run the example scripts from the `scripts` directory:

```bash
python scripts/run_simple_example.py
python scripts/run_code_gen.py
python scripts/run_fractal_example.py
python scripts/run_simple_example_ui.py
```

Note: Make sure you are in the project root directory when running these commands.
