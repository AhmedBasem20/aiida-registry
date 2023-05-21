# -*- coding: utf-8 -*-
"""Test installing registered plugins.

This uses the aiida-core Docker container to test the installation of the plugins.
"""
# pylint: disable=missing-function-docstring,consider-using-f-string,too-few-public-methods

import json
import os
import sys
from dataclasses import asdict, dataclass

from . import PLUGINS_METADATA, PLUGINS_TEST_RESULTS

# Where to mount the workdir inside the Docker container
_DOCKER_WORKDIR = "/tmp/scripts"


@dataclass
class TestResult:
    """Test result."""

    is_installable: bool
    is_importable: bool
    process_metadata: dict
    error_message: str


def has_python_version_classifier(plugin_info):
    """Return True, if package specifies python version compatibility."""
    meta = plugin_info["metadata"]

    if meta is None or "classifiers" not in meta:
        return False

    for classifier in meta["classifiers"]:
        if classifier.startswith("Programming Language :: Python ::"):
            return True

    return False


def supports_python_version(plugin_info):
    """Return True, if package supports current python version."""

    # If developers don't specify version compatibility, we assume all versions are supported
    if not has_python_version_classifier(plugin_info):
        return True

    python_version = sys.version_info
    classifier = "Programming Language :: Python :: {}.{}".format(
        python_version[0], python_version[1]
    )

    if classifier in plugin_info["metadata"]["classifiers"]:
        return True

    print(
        "   >> SKIPPING - python version {}.{} not supported".format(
            python_version[0], python_version[1]
        )
    )
    return False


def handle_error(process_result, message):
    error_message = ""

    if process_result.exit_code != 0:
        error_message = process_result.output.decode("utf8")
        raise ValueError(f"{message}\n{error_message}")

    return error_message


def test_install_one_docker(container_image, plugin):
    """Test installing one plugin in a Docker container."""
    import docker  # pylint: disable=import-outside-toplevel

    client = docker.from_env(timeout=180)

    is_package_installed = False
    is_package_importable = False
    process_metadata = {}
    error_message = ""

    print("   - Starting container for {}".format(plugin["name"]))
    container = client.containers.run(
        container_image,
        detach=True,
        volumes={os.getcwd(): {"bind": _DOCKER_WORKDIR, "mode": "rw"}},
    )

    try:
        print("   - Installing plugin {}".format(plugin["name"]))
        install_package = container.exec_run(f'pip install --pre {plugin["pip_url"]}')

        error_message = handle_error(
            install_package, f"Failed to install plugin {plugin['name']}"
        )

        # Should make this depend on the AiiDA version inside the container,
        # at least after 2.0 is out that removes reentry
        _reentry_scan = container.exec_run("reentry scan -r aiida")

        is_package_installed = True

        if "package_name" not in list(plugin.keys()):
            plugin["package_name"] = plugin["name"].replace("-", "_")

        print("   - Importing {}".format(plugin["package_name"]))
        import_package = container.exec_run(
            "python -c 'import {}'".format(plugin["package_name"])
        )

        error_message = handle_error(
            import_package, f"Failed to import package {plugin['package_name']}"
        )
        is_package_importable = True

        print(
            "   - Extracting entry point metadata for {}".format(plugin["package_name"])
        )
        extract_metadata = container.exec_run(
            workdir=_DOCKER_WORKDIR,
            cmd="python ./bin/analyze_entrypoints.py -o result.json",
        )
        error_message = handle_error(
            extract_metadata,
            f"Failed to fetch entry point metadata for package {plugin['package_name']}",
        )

        with open("result.json", "r", encoding="utf8") as handle:
            process_metadata = json.load(handle)

    except ValueError as exc:
        print(f"   >> ERROR: {str(exc)}")

    finally:
        container.remove(force=True)

    return asdict(
        TestResult(
            is_installable=is_package_installed,
            is_importable=is_package_importable,
            process_metadata=process_metadata,
            error_message=error_message,
        )
    )


def test_install_all(container_image):
    with open(PLUGINS_METADATA, "r", encoding="utf8") as handle:
        data = json.load(handle)

    test_results = []

    print("[test installing plugins]")
    for _k, plugin in data.items():
        print(" - {}".format(plugin["name"]))

        # this currently checks for the wrong python version
        # if not supports_python_version(plugin):
        #    continue

        # 'planning' plugins aren't installed/tested
        if plugin["development_status"] in ["planning"]:
            print("    >> SKIPPING: plugin at planning state")
            continue

        if "pip_url" not in list(plugin.keys()):
            if plugin["development_status"] not in ["planning", "pre-alpha", "alpha"]:
                print(
                    f"    >> WARNING: pip_url key missing, despite required for {plugin['development_status']} stage !"
                )
            else:
                print("    >> SKIPPING: No pip_url key provided")
            continue

        test_results.append(test_install_one_docker(container_image, plugin))

    print(f"Dumping {PLUGINS_TEST_RESULTS}")
    with open(PLUGINS_TEST_RESULTS, "w", encoding="utf8") as handle:
        json.dump(test_results, handle, indent=2)

def get_all_data(container_image):
    with open(PLUGINS_METADATA, "r", encoding="utf8") as handle:
        data = json.load(handle)

    test_results = []

    print("[test installing plugins]")
    i = 0
    for _k, plugin in data.items():
        print(" - {}".format(plugin["name"]))
        i+=1
        if i > 8:
            break

        # this currently checks for the wrong python version
        # if not supports_python_version(plugin):
        #    continue

        # 'planning' plugins aren't installed/tested
        if plugin["development_status"] in ["planning"]:
            print("    >> SKIPPING: plugin at planning state")
            continue

        if "pip_url" not in list(plugin.keys()):
            if plugin["development_status"] not in ["planning", "pre-alpha", "alpha"]:
                print(
                    f"    >> WARNING: pip_url key missing, despite required for {plugin['development_status']} stage !"
                )
            else:
                print("    >> SKIPPING: No pip_url key provided")
            continue

        result_dict = test_install_one_docker(container_image, plugin)
        process_metadata = result_dict["process_metadata"]
        print(json.dumps(process_metadata, indent=4))
        if process_metadata is not None:
                try:                
                    for k, calculation in process_metadata["aiida.calculations"].items():
                        data[plugin["name"]]["entry_points"]["aiida.calculations"][k] = calculation
                except KeyError:
                    continue

            


    print(f"Dumping {PLUGINS_TEST_RESULTS}")
    with open(PLUGINS_TEST_RESULTS, "w", encoding="utf8") as handle:
        json.dump(test_results, handle, indent=2)
    
    json_str = json.dumps(data, indent=2)
    print(json_str)