#!/usr/bin/env python3
# flake8: noqa
import argparse
import subprocess
import logging
import os
import collections
import time

logger = logging.getLogger(__name__)

ENVS = collections.OrderedDict(
    {
        "prod": {  # TODO: add prod support
            "OC_SERVER": "api.ul-pca-pr-ul01.ulaval.ca:6443",
            "OC_PROJECT": "ul-val-genovalia-pr",
            "OC_REGISTRY": "registre.apps.ul-pca-pr-ul01.ulaval.ca",
            "OC_DEPLOYMENT": "ontology-search-dev",
            "BUILD_TARGET": "docker-compose.yml",
            "IMAGES": [
                "registre.apps.ul-pca-pr-ul01.ulaval.ca/ul-val-genovalia-pr/ontology-search-dev:latest",
            ],
        },
        "dev": {
            "OC_SERVER": "api.ul-pca-pr-ul01.ulaval.ca:6443",
            "OC_PROJECT": "ul-val-genovalia-pr",
            "OC_REGISTRY": "registre.apps.ul-pca-pr-ul01.ulaval.ca",
            "OC_DEPLOYMENT": "ontology-search-dev",
            "BUILD_TARGET": "docker-compose.dev.yml",
            "IMAGES": [
                "registre.apps.ul-pca-pr-ul01.ulaval.ca/ul-val-genovalia-pr/ontology-search-dev:latest",
            ],
        },
    }
)


OC_SERVER = None
OC_PROJECT = None
OC_REGISTRY = None
OC_DEPLOYMENT = None
BUILD_TARGET = None
IMAGES = None


parser = argparse.ArgumentParser(description="Build and deploy image to Openshift")

parser.add_argument("-b", "--build", help="skip image building", action="store_false")
parser.add_argument(
    "-p",
    "--push",
    help="ignore image pushing to registry",
    action="store_false",
)
parser.add_argument(
    "-r",
    "--rollout",
    help="whether to skip rollout of the image",
    action="store_false",
)

parser.add_argument("-U", "--user", help="openshift user", default=None)
parser.add_argument("-P", "--password", help="openshift password", default=None)
parser.add_argument(
    "-f",
    "--force-login",
    help="whether to force (re)-login or attempt without it",
    action="store_true",
)
parser.add_argument("-v", "--verbose", help="verbose logging", action="store_true")


def select_env():
    print("Select environment:")
    for i, env in enumerate(ENVS.keys(), start=1):
        print(f"{i}. {env}")
    print("c. Cancel")
    while True:
        try:
            choice = input("Enter the number of the environment: ")
            if choice == "c":
                return None, None
            elif 1 <= int(choice) <= len(ENVS):
                return (
                    list(ENVS.values())[int(choice) - 1],
                    list(ENVS.keys())[int(choice) - 1],
                )
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number or c.")


def ask_to_abort():
    print("There were errors during the script. Do you want to abort? (y/n)")
    while True:
        answer = input().strip().lower()
        if answer in ["y", "yes"]:
            return True
        elif answer in ["n", "no"]:
            return False
        else:
            print("Please enter 'y' or 'n'.")


def is_docker_running(stdout=None):
    try:
        subprocess.run(["docker", "info"], check=True, stdout=stdout)
        return True
    except subprocess.CalledProcessError:
        logger.error("Docker is not running. Please start Docker.")
        return False
    except FileNotFoundError:
        logger.error("Docker is not installed or running. Please install Docker.")
        return False


def build_image(image, stdout=None):
    logger.info(f"Building image: {image}")
    try:
        subprocess.run(
            ["docker", "compose", "-f", BUILD_TARGET, "build"],  # type: ignore
            check=True,
            stdout=stdout,
        )  # type: ignore
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to build image: {e}")
        return False


def is_logged_in_to_oc(stdout=None):
    try:
        subprocess.run(["oc", "status"], check=True, stdout=stdout)
        return True
    except subprocess.CalledProcessError:
        logger.error("Not logged in to OpenShift.")
        return False


def login_to_oc(user, password, stdout=None):
    if password is None:
        try:
            subprocess.run(
                ["oc", "login", "-u", user, OC_SERVER],  # type: ignore
                check=True,
            )  # type: ignore
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to login: {e}")
            return False
    else:
        try:
            subprocess.run(
                ["oc", "login", "-u", user, OC_SERVER, "--password", password],  # type: ignore
                check=True,
                stdout=stdout,
            )  # type: ignore
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to login: {e}")
            return False


def login_to_registry(stdout):
    try:
        subprocess.run(
            [
                "docker",
                "login",
                "-u",
                subprocess.check_output(["oc", "whoami"]).strip(),
                "-p",
                subprocess.check_output(["oc", "whoami", "--show-token"]).strip(),
                OC_REGISTRY,  # type: ignore
            ],
            check=True,
            stdout=stdout,
        )  # type: ignore
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to login to registry: {e}")
        return False


def push_image(image, stdout=None):
    logger.info(f"Pushing image: {image}")
    try:
        subprocess.run(["docker", "push", image], check=True, stdout=stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to push image: {e}")
        return False


def rollout_deployment(stdout=None):
    try:
        subprocess.run(
            ["oc", "rollout", "latest", OC_DEPLOYMENT],  # type: ignore
            check=True,
            stdout=stdout,
        )  # type: ignore
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to rollout deployment: {e}")
        return False


def main(verbose, build, push, rollout, user, password, force_login):
    stdout = None

    envs, env_name = select_env()
    if envs is None:
        logger.info("No environment selected. Exiting.")
        return

    global OC_SERVER, OC_PROJECT, OC_REGISTRY, OC_DEPLOYMENT, IMAGES, BUILD_TARGET
    OC_DEPLOYMENT = envs["OC_DEPLOYMENT"]
    OC_SERVER = envs["OC_SERVER"]
    OC_PROJECT = envs["OC_PROJECT"]
    OC_REGISTRY = envs["OC_REGISTRY"]
    IMAGES = envs["IMAGES"]
    BUILD_TARGET = envs["BUILD_TARGET"]

    # what will be done
    print(f"target: {env_name}")
    print(f"docker-compose target: {BUILD_TARGET}")
    if build:
        print(f"will build {len(IMAGES)} images")
    if push:
        print(f"will push {len(IMAGES)} images")
    if rollout:
        print(f"will rollout {OC_DEPLOYMENT}")

    time.sleep(2)

    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        stdout = open(os.devnull, "wb")
        logging.basicConfig(level=logging.INFO)

    if build:
        result = is_docker_running(stdout)
        if not result:
            return

        logger.info("Building images...")
        for image in IMAGES:
            result = build_image(image, stdout=stdout)
            if not result:
                logger.error("Failed to build image.")
                if ask_to_abort():
                    return

    if push:
        must_login = False
        if not force_login:
            logger.info("Checking if logged in to OpenShift...")
            result = is_logged_in_to_oc(stdout=stdout)
            if result:
                must_login = False
            else:
                logger.warning("Not logged in to OpenShift.")
                must_login = True
        else:
            must_login = True

        if must_login:
            if not user:
                user = input("Enter OpenShift username: ")

            logger.info("Logging in to OpenShift...")
            result = login_to_oc(user, password, stdout=stdout)
            if not result:
                logger.error("Failed to login to OpenShift.")
                return

        logger.info("Logging in to Docker registry...")
        result = login_to_registry(stdout=stdout)
        if not result:
            logger.error("Failed to login to Docker registry.")
            return

        logger.info("Pushing images...")
        for image in IMAGES:
            result = push_image(image, stdout=stdout)
            if not result:
                logger.error("Failed to push image.")
                if ask_to_abort():
                    return

    if rollout:
        must_login = False
        if not force_login:
            logger.info("Checking if logged in to OpenShift...")
            result = is_logged_in_to_oc(stdout=stdout)
            if result:
                must_login = False
            else:
                logger.warning("Not logged in to OpenShift.")
                must_login = True
        else:
            must_login = True
        if must_login:
            if not user:
                user = input("Enter OpenShift username: ")

            logger.info("Logging in to OpenShift...")
            result = login_to_oc(user, password, stdout=stdout)
            if not result:
                logger.error("Failed to login to OpenShift.")
                return
        logger.info("Rolling out deploymentconfig...")
        result = rollout_deployment(stdout=stdout)
        if not result:
            logger.error("Failed to rollout deploymentconfig.")
            return

    if not build and not push and not rollout:
        logger.info(
            "No action specified. Do not use all of -b, -r and -p options at the same time."
        )
        return

    logger.info("Run completed successfully.")


if __name__ == "__main__":
    args = parser.parse_args()
    main(**vars(args))
