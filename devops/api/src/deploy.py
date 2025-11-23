import os
import yaml
import subprocess

def clean_deploy():
    BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    BILLING_COMPOSE = os.path.join(BASE, "billing/docker-compose.yml")
    WEIGHT_COMPOSE  = os.path.join(BASE, "weight/docker-compose.yml")
    subprocess.run([
        "docker", "compose",
        "-f", BILLING_COMPOSE,
        "-f", WEIGHT_COMPOSE,
        "up", "-d"
    ], check=True)




def update_compose_with_shared_network(
    compose_path,
    output_dir,
    output_filename="compose-test.yml",
    shared_network="shared-devops-network"
):
    """
    Loads ONE docker-compose file,
    attaches all services to an EXTERNAL shared network,
    fixes build paths,
    fixes env_file paths,
    and writes the new compose file into BASE/devops.
    """

    # Make sure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Load compose
    with open(compose_path, "r") as f:
        compose_data = yaml.safe_load(f)

    # Original compose location (billing/ or weight/)
    original_dir = os.path.dirname(compose_path)

    # Ensure networks section exists
    if "networks" not in compose_data:
        compose_data["networks"] = {}

    # Add EXTERNAL network (correct way for multi-compose interconnection)
    compose_data["networks"][shared_network] = {
        "external": True
    }

    # Update each service
    for _, service in compose_data.get("services", {}).items():

        # -------------------------------------------------------------
        # Attach service to shared network
        # -------------------------------------------------------------
        if "networks" not in service:
            service["networks"] = []
        if shared_network not in service["networks"]:
            service["networks"].append(shared_network)

        # -------------------------------------------------------------
        # Fix relative build paths
        # -------------------------------------------------------------
        if "build" in service:
            build_setting = service["build"]

            # Case: build: { context: "api" }
            if isinstance(build_setting, dict) and "context" in build_setting:
                new_context = os.path.relpath(
                    os.path.join(original_dir, build_setting["context"]),
                    output_dir
                )
                build_setting["context"] = new_context

            # Case: build: "api"
            elif isinstance(build_setting, str):
                new_context = os.path.relpath(
                    os.path.join(original_dir, build_setting),
                    output_dir
                )
                service["build"] = new_context

        # -------------------------------------------------------------
        # NEW: Fix env_file paths
        # -------------------------------------------------------------
        if "env_file" in service:
            fixed_env_paths = []

            for env_path in service["env_file"]:
                # Convert paths like ".env" to "../billing/.env" or "../weight/.env"
                new_env_path = os.path.relpath(
                    os.path.join(original_dir, env_path),
                    output_dir
                )
                fixed_env_paths.append(new_env_path)

            service["env_file"] = fixed_env_paths

    # Output path
    output_path = os.path.join(output_dir, output_filename)

    # Write updated compose
    with open(output_path, "w") as f:
        yaml.dump(compose_data, f, sort_keys=False)

    print(f"✔ Created: {output_path}")



def deploy():
    """
    1. Creates shared docker network
    2. Rewrites both compose files to use it
    3. Deploys both stacks
    """

    BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    BILLING_COMPOSE = os.path.join(BASE, "billing/docker-compose.yml")
    WEIGHT_COMPOSE  = os.path.join(BASE, "weight/docker-compose.yml")
    DEVOPS_DIR      = os.path.join(BASE, "devops")

    SHARED_NETWORK = "shared-devops-network"

    # -----------------------------------------------------
    # 1. Ensure shared external network exists
    # -----------------------------------------------------
    subprocess.run(
        ["docker", "network", "create", SHARED_NETWORK],
        check=False  # ignore error if network already exists
    )

    # -----------------------------------------------------
    # 2. Rewrite BOTH compose files into BASE/devops
    # -----------------------------------------------------
    update_compose_with_shared_network(
        compose_path=BILLING_COMPOSE,
        output_dir=DEVOPS_DIR,
        output_filename="compose-billing.yml",
        shared_network=SHARED_NETWORK
    )

    update_compose_with_shared_network(
        compose_path=WEIGHT_COMPOSE,
        output_dir=DEVOPS_DIR,
        output_filename="compose-weight.yml",
        shared_network=SHARED_NETWORK
    )

    # -----------------------------------------------------
    # 3. Deploy both stacks using ONE compose command each
    # -----------------------------------------------------

    billing_output = os.path.join(DEVOPS_DIR, "compose-billing.yml")
    weight_output  = os.path.join(DEVOPS_DIR, "compose-weight.yml")

    # ---- Billing ----
    subprocess.run(
        ["docker", "compose", "-f", billing_output, "up", "--build", "-d"],
        check=True
    )

    # ---- Weight ----
    subprocess.run(
        ["docker", "compose", "-f", weight_output, "up", "--build", "-d"],
        check=True
    )

    print("✔ Deployment completed successfully")


