#!/bin/bash

# OpenEnv Submission Validation Script

set -e
echo "═══════════════════════════════════════"
echo "  OpenEnv Pre-Submission Validation"
echo "═══════════════════════════════════════"
echo ""

# 1. Check for required root files
echo "── 1. Required Files ──"
FILES=("openenv.yaml" "inference.py" "README.md" "Dockerfile" "requirements.txt")
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ Missing $file"
        exit 1
    fi
done
echo ""

# 2. Check server/ module structure
echo "── 2. Server Module Structure ──"
SERVER_FILES=("server/__init__.py" "server/app.py" "server/models.py" "server/environment.py" "server/tasks.py" "server/grader.py")
for file in "${SERVER_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ Missing $file"
        exit 1
    fi
done
echo ""

# 3. Activate venv & validate Python imports
echo "── 3. Python Import Validation ──"
source venv/bin/activate
python3 -c "
from server.tasks import TASKS
from server.grader import grade_action
from server.environment import CodeSecurityEnv
from server.models import CodeReviewAction, CodeObservation, StepResult, StateResponse, ResetResponse, TaskInfo

assert len(TASKS) >= 3, f'Expected 3+ tasks, got {len(TASKS)}'
print('  ✅ All imports resolve correctly')
print(f'     Tasks: {list(TASKS.keys())}')
" || { echo "  ❌ Python import validation failed"; exit 1; }
echo ""

# 4. Quick grader smoke test
echo "── 4. Grader Smoke Test ──"
python3 -c "
from server.environment import CodeSecurityEnv
from server.models import Action

env = CodeSecurityEnv()
obs = env.reset('python-off-by-one')
result = env.step(Action(**{
    'bug_identified': True,
    'bug_location': 'range(len(transactions) + 1)',
    'bug_type': 'logic-error',
    'bug_description': 'Off-by-one index error — the range goes one past the end causing an out of bounds IndexError',
    'severity': 'medium',
    'suggested_fix': 'Use range(len(transactions)) to fix the boundary',
}))
assert 0.0 <= result.reward <= 1.0, f'Reward out of range: {result.reward}'
assert result.done is True
print(f'  ✅ Grader returned reward={result.reward:.4f}, done={result.done}')

# Verify zero-reward path
env2 = CodeSecurityEnv()
env2.reset('python-off-by-one')
r2 = env2.step(Action(**{
    'bug_identified': False,
    'bug_location': '',
    'bug_type': 'none',
    'bug_description': 'No bug found',
    'severity': 'none',
    'suggested_fix': '',
}))
assert r2.reward == 0.0, f'Expected 0.0 for no-bug, got {r2.reward}'
print(f'  ✅ No-bug path returns reward=0.0')
" || { echo "  ❌ Grader smoke test failed"; exit 1; }
echo ""

# 5. Validate openenv.yaml
echo "── 5. openenv.yaml Validation ──"
python3 -c "
import yaml
with open('openenv.yaml', 'r') as f:
    data = yaml.safe_load(f)
assert 'name' in data, 'Missing name field'
assert 'tasks' in data, 'Missing tasks field'
assert len(data['tasks']) >= 3, f'Need 3+ tasks, got {len(data[\"tasks\"])}'
print(f'  ✅ Valid YAML with {len(data[\"tasks\"])} tasks')
" || { echo "  ❌ openenv.yaml validation failed"; exit 1; }
echo ""

echo "═══════════════════════════════════════"
echo "  ✅ All checks passed!"
echo "═══════════════════════════════════════"
