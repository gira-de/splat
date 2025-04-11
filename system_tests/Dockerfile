# Use the base image of splat (which is already pushed)
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

WORKDIR /splat

COPY ./system_tests /splat/system_tests

CMD ["python3", "-m", "unittest", "discover", "-v", "-s", "system_tests", "-p", "test_*.py"]
