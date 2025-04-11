# actionTest
a repo to test my published action

    tries to stop a docker container with name 'CONTAINERNAME'
    tries to remove stopped container 'CONTAINERNAME'
    tries to build a docker image with the name 'IMAGENAME' (must contain version tag)
    starting a docker container with image: 'IMAGENAME' and the name: 'CONTAINERNAME'
    running 'docker system prune' because this action is meant to run on a self-hosted runner that replaces docker container on the same machine
