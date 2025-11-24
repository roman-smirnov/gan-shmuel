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
                subprocess.run(["pytest", "billing/tests", "-q"], check=True)
                print("Billing tests PASSED!")
            except subprocess.CalledProcessError:
                print("Billing tests FAILED!")
                all_tests_passed = False

            # --- WEIGHT TESTS ---
            print("Running weight tests…")
            try:
                subprocess.run(["pytest", "weight/tests", "-q"], check=True)
                print("Weight tests PASSED!")
            except subprocess.CalledProcessError:
                print("Weight tests FAILED!")
                all_tests_passed = False

        else:
            print("run.sh not found — skipping execution.")
            return False

    except Exception as e:
        print(f"Error during test deploy: {e}")
        return False

    return all_tests_passed

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
