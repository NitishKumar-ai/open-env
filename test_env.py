import os
import sys
# Add the current directory to sys.path so we can import 'server'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server.environment import CodeReviewEnvironment
from server.models import CodeReviewAction

def run_test():
    print("Initializing CodeReviewEnvironment...")
    env = CodeReviewEnvironment()
    
    print("\n--- 1. Testing 'easy' task (reset) ---")
    obs = env.reset(difficulty="easy")
    print(f"Task ID: {obs.task_id}")
    print(f"Difficulty: {obs.difficulty}")
    print(f"Task Description: {obs.task_description}")
    print(f"Code Snippet:\n{obs.code_snippet}")
    print("-" * 40)
    
    print("\n--- 2. Submitting an accurate CodeReviewAction ---")
    action = CodeReviewAction(
        bug_identified=True,
        bug_type="off-by-one error",
        bug_location="range(1, len(arr) + 1)",
        bug_description="The loop contains an off-by-one IndexError because it tries to access arr[i] which goes out of bounds.",
        suggested_fix="Change to range(len(arr))",
        severity="high"
    )
    
    obs, reward, done, info = env.step(action)
    print(f"Step Reward: {reward}")
    print(f"Is Done: {done}")
    print(f"Info Breakdown:")
    for k, v in info['breakdown'].items():
        print(f"  {k}: {v}")
    print(f"Total Score: {info['total_score']}")
    print(f"Feedback: {info['feedback']}")

if __name__ == "__main__":
    run_test()
