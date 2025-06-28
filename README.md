# RPL-2.0-runner


## local PROD integration testing via docker compose

IMPORTANT: Make sure to follow these setup instructions first: [RPL-3.0 (Backend APIs): local PROD via docker compose](https://github.com/MiguelV5/RPL-3.0#local-prod-via-docker-compose)

ONLY AFTER the metaservices and the APIs from RPL-3.0 are running, you can run this to start both the receiver and the runner in a containerized environment:

```sh
docker compose -f docker-compose.local.yml up -d --build
```

To stop them:
```sh
docker compose -f docker-compose.local.yml down
```

You can spin up the frontend whenever you want, the only mandatory services are the backend ones (so that this compose file can find their networks and connect to them).

## local PROD integration testing via minikube

IMPORTANT: Make sure to follow these setup instructions first: [RPL-3.0 (Backend APIs): local PROD via minikube](https://github.com/MiguelV5/RPL-3.0#local-prod-via-minikube)

ONLY AFTER the backend's minikube setup, you can follow these steps to start the kubernetes deployment and service:

- Build the docker images:

```sh
docker build -t worker_rpl:local . # (this is the receiver)
docker build -t runner_rpl:local ./rpl_runner
```

- Temporarily edit the `kubernetes/deployments/runner.yaml` file to use the `worker_rpl:local` image for the receiver and the `runner_rpl:local` image for the runner. Also you should comment out the following contents:
```yaml
  nodeSelector:
    cloud.google.com/gke-preemptible: "true"
  tolerations:
  - effect: NoSchedule
    key: task
    operator: Equal
    value: preemptive
```

- Start the kubernetes deployment and service:

```sh
kubectl create -f kubernetes/deployments/runner.yaml
kubectl create -f kubernetes/services/runner.yaml
```

To stop the deployment or the service, you can run:

```shell script
kubectl delete -f ./kubernetes/deployments/runner.yaml
kubectl delete -f ./kubernetes/services/runner.yaml
```

If you want to stop everything at once, you can run this:
(WARNING: this will stop ALL deployments/services within the namespace, not just the runner related ones)

```shell script
kubectl delete --all deployments --namespace=default
kubectl delete --all services --namespace=default
```

---

## (Previous) USAGE

Build receiver docker image:

```sh
docker build -t rpl-2.0-runner ./rpl_runner
```

### With rabbitmq

1.- Start a rabbitmq server

```sh
docker run -p 9999:15672 -p 5672:5672 deadtrickster/rabbitmq_prometheus:latest
```

2.- Start receiving messages with 

```sh
python3 rabbitmq_receive.py
```

3.- Send messages with (or just POST a submission to the RPL-server)

```sh
python3 rabbitmq_send.py <submission_id> <lang>
```

WHERE LANG can be: `python_3.7` or `c_std11`


### Without rabbitmq
```sh
docker build -t rpl-2.0-runner ./rpl_runner && python3 receiver.py <submission_id> <lang>
```

## Description

### rabbitmq_send.py
ONLY FOR TESTING: Send a message to the queue


### rabbitmq_receive.py
Receive message from queue and invoque receiver.py

### receiver.py
Get submission from RPL-Server
Creates NEW DOCKER PROCESS with a custom runner for a specific language in a docker container
Post results to RPL

### init.py, runner.py and custom_runner.py (RUNNING INSIDE DOCKER CONTAINER)
1. Prepare
2. Build
3. Run

Every step is language-specific and redirecting `stdout` and `stderr` to a tempfile.

stdout result example:
	
```json
{
  "tests_execution_result_status":"OK",                                                                                                                                                                                    
  "tests_execution_stage":"COMPLETE",
  "tests_execution_exit_message": "Completed all stages",
  "unit_test_suite_result_summary": {
    "amount_passed": 2,
    "amount_failed": 0,
  "amount_errored": 0,
  "single_test_reports":[
    {
      "name": "test_1",
      "status": "PASSED",
      "messages": null
    }
    {
      "name": "test_2",
      "status": "PASSED",
      "messages": null
    }                                                                                                                                         
  ],
  "tests_execution_stdout": "2020-07-19 20:16:55,844 RPL-2.0      INFO     Build Started\n2020-07-19 20:16:55,845 RPL-2.0      INFO     Building\n2020-07-19 20:16:55,846 RPL-2.0      INFO     start_BUILD\n/usr/bin/python3.7 -m py_compile  unit_test.py unit_test_wrapper.py assignment_main.py\n2020-07-19 20:17:02,219 RPL-2.0      INFO     end_BUILD\n2020-07-19 20:17:02,219 RPL-2.0      INFO     Build Ended\n2020-07-19 20:17:02,219 RPL-2.0      INFO     Run Started\n2020-07-19 20:17:02,221 RPL-2.0      INFO     Running Unit Tests\n2020-07-19 20:17:02,221 RPL-2.0      INFO     start_RUN\n\n2020-07-19 20:17:02,287 RPL-2.0      INFO     end_RUN\n2020-07-19 20:17:02,288 RPL-2.0      INFO     RUN OK\n2020-07-19 20:17:02,288 RPL-2.0      INFO     Run Ended\n",
  "tests_execution_stderr":"",
} 
```


### How I tested it

In any case, you have to build the `runner` docker image that the receiver uses for testing assignments in a containerized environment.

```sh
docker build -t rpl-2.0-runner ./rpl_runner
```

Any changes made to any file inside the `rpl_runner` folder will need to rebuild the docker image.


### The whole circle
Start the rabbitmq server, the Java RPL Server and the rabbitmq_receive.py

Login, get your auth token.

Post a submission like  (replace `/home/alepox/Desktop/tp_prof/rpl/pruebita_runner/la_submission.tar.xz` and the Authorization header)

```sh
curl -X POST \
  {producer_base_api}/api/courses/1/activities/1/submissions \
  -H 'Accept: */*' \
  -H 'Accept-Encoding: gzip, deflate' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIxIiwiaWF0IjoxNTc4MTM5MjA0LCJleHAiOjE1NzgxNTM2MDR9.nSub-DaZq5bejmN_h31gymg4xay--mbSD0_ogpGOsDJzV1pP_gkSwCF_LnwfSm0UsLFYuuoCHruC2V8hCaaIqA' \
  -H 'Cache-Control: no-cache' \
  -H 'Connection: keep-alive' \
  -H 'Content-Length: 1025' \
  -H 'Content-Type: multipart/form-data; boundary=--------------------------193299411849957077408518' \
  -H 'Host: localhost:8080' \
  -H 'Postman-Token: 66b86c8a-1d39-44fc-b2e5-309da5282640,c1af91c7-6e68-40ce-b869-02fc81afa51e' \
  -H 'User-Agent: PostmanRuntime/7.20.1' \
  -H 'cache-control: no-cache' \
  -H 'content-type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW' \
  -F file=@/home/alepox/Desktop/tp_prof/rpl/pruebita_runner/la_submission.tar.xz \
  -F 'description=files for C'
```

### Just the consumer (without using rabbitmq)
If you already have submissions in the DB and the RPL-Server is up and running.

```sh
python3 receiver.py <submission_id> <lang>
```

### Just the consumer (using rabbitmq)
If you already have submissions in the DB and the RPL-Server is up and running and the rabbitmq server too.

Enqueue a submissionId and the magic will do the rest

```sh
python3 rabbitmq_receive.py
```

```sh
python3 rabbitmq_send.py <submission_id> <lang>
```

## Compiling and deleting source files

Check out `c_Makefile` and `python_Makefile`

### C

We are just compiling the code and deleting the source files before execution

### python

First we execute python -m py_compile so that, if it fails, we get a nice "user-only-code" error message
We are using (pyinstaller)[https://pyinstaller.readthedocs.io/en/stable/usage.html] to generate a binary file and then executing it in the "run" step.

