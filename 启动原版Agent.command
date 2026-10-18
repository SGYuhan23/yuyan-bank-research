#!/bin/bash
cd "$(dirname "$0")"
exec agent-platform/backend/.venv/bin/python scripts/start_general_agent.py
