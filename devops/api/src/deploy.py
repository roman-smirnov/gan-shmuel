import os
import subprocess

RUN_SCRIPT = "run.sh"

def test_shutdown():
    if not os.path.isfile(RUN_SCRIPT):
        print("Failed to shutdown test service group: run.sh not found")
        return 
    print("run.sh found — trying to shutdown test service group...")
    try:
        subprocess.run(["bash", RUN_SCRIPT, "down", "--test"], check=True)
    except Exception as e:
        print(f"Error when trying to shutdown test service group: {e}")
        return
    print("Successfuly shut down test service group.")
    return



def test_deploy():
    all_tests_passed = True

    try:
        if os.path.isfile(RUN_SCRIPT):
            print("run.sh found — starting TEST stack…")

            # Start test stack: build + test mode
            subprocess.run(["bash", "run.sh", "--build", "--test"], check=True)

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
        subprocess.run(["bash", "run.sh", "-b", "-p", "--master"], check=True)
        print("Production deployment finished successfully!")
        return True
    except subprocess.CalledProcessError:
        print("Production deploy FAILED!")
        return False