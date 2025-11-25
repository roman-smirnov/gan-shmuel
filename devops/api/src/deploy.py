import os
import subprocess
import os
import subprocess

def test_deploy():
    all_tests_passed = True

    run_script = "run.sh"

    try:
        if os.path.isfile(run_script):
            print("run.sh found — starting TEST stack…")

            # Start test stack: build + test mode
            subprocess.run(["bash", "run.sh", "-b", "-t"], check=True)

            # --- BILLING TESTS ---
            print("Running billing tests…")
            try:
                subprocess.run(
                    ["docker", "exec","test-billing-app-1", "pytest", "tests/"],
                    check=True
                )
                print("✅ Tests passed!")
            except subprocess.CalledProcessError:
                print("❌ Tests FAILED")
                all_tests_passed = False

            # --- WEIGHT TESTS ---
            print("Running weight tests…")
            try:
                subprocess.run(
                    ["docker", "exec","test-weight-app-1", "pytest", "tests/"],
                    check=True
                )
                print("✅ Tests passed!")
            except subprocess.CalledProcessError:
                print("❌ Tests FAILED")
                all_tests_passed = False
            
            
            return all_tests_passed

        else:
            print("run.sh not found — skipping execution.")
            return False

    except Exception as e:
        print(f"Error during test deploy: {e}")
        return False

def deploy():
    run_script = "run.sh"

    if not os.path.isfile(run_script):
        print("run.sh not found — cannot deploy.")
        return False

    print("Deploying PRODUCTION stack…")

    try:
        subprocess.run(["bash", "run.sh", "-b", "-p"], check=True)
        print("Production deployment finished successfully!")
        return True
    except subprocess.CalledProcessError:
        print("Production deploy FAILED!")
        return False
