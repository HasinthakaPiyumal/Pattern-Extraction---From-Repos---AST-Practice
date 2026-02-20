# Cluster 15

def run_all_tests():
    """Run all test suites."""
    cmd = ['python', '-m', 'pytest', 'tests/', '-v', '--tb=short']
    return run_command(cmd, 'All Test Suites')

# Node: run_command
def run_room_matching_tests():
    """Run room matching tests."""
    cmd = ['python', '-m', 'pytest', 'tests/test_room_matching.py', '-v', '--tb=short']
    return run_command(cmd, 'Room Matching Tests')

def run_leaderboard_tests():
    """Run leaderboard tests."""
    cmd = ['python', '-m', 'pytest', 'tests/test_leaderboard.py', '-v', '--tb=short']
    return run_command(cmd, 'Leaderboard Tests')

def run_game_state_tests():
    """Run game state synchronization tests."""
    cmd = ['python', '-m', 'pytest', 'tests/test_game_state_sync.py', '-v', '--tb=short']
    return run_command(cmd, 'Game State Synchronization Tests')

def run_smoke_tests():
    """Run smoke tests (basic functionality)."""
    cmd = ['python', '-m', 'pytest', 'tests/', '-m', 'smoke', '-v', '--tb=short']
    return run_command(cmd, 'Smoke Tests')

def run_integration_tests():
    """Run integration tests."""
    cmd = ['python', '-m', 'pytest', 'tests/', '-m', 'integration', '-v', '--tb=short']
    return run_command(cmd, 'Integration Tests')

def run_unit_tests():
    """Run unit tests."""
    cmd = ['python', '-m', 'pytest', 'tests/', '-m', 'unit', '-v', '--tb=short']
    return run_command(cmd, 'Unit Tests')

def run_with_coverage():
    """Run tests with coverage report."""
    cmd = ['python', '-m', 'pytest', 'tests/', '--cov=app', '--cov-report=html', '--cov-report=term-missing', '-v']
    return run_command(cmd, 'Tests with Coverage')

def run_parallel_tests():
    """Run tests in parallel."""
    cmd = ['python', '-m', 'pytest', 'tests/', '-n', 'auto', '-v']
    return run_command(cmd, 'Parallel Tests')

def run_specific_test(test_path):
    """Run a specific test file or test function."""
    cmd = ['python', '-m', 'pytest', test_path, '-v', '--tb=short']
    return run_command(cmd, f'Specific Test: {test_path}')

def lint_code():
    """Run code linting."""
    cmd = ['flake8', 'tests/', '--max-line-length=100', '--ignore=E203,W503']
    return run_command(cmd, 'Code Linting')

def format_code():
    """Format code with black."""
    cmd = ['black', 'tests/', '--line-length=100']
    return run_command(cmd, 'Code Formatting')

