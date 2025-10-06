# Claude Code Configuration

## Project Overview
This is a Python project for Nextflow workflow management.

## Git usage

Before implementing any feature, switch to a new branch and implement changes there. 

Commit often (after every implemented change)

## Project management

Project is done using uv; if you want to add new dependencies; do:
uv add {your dependencies}

and if you want to run any script do,

uv run {your script}

To test imports after editable installation:
1. source .venv/bin/activate
2. uv pip install -e .
3. python -c "import pynf; print('✓ pynf import successful')"

## project philosophy

This is a prototype project, performance is not important, instead code should be concise, we also do not run automated tests yet, to do tests, simply write scripts that will call nf modules and logg outputs. 

