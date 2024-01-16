# installation

1. npm install -g serverless
2. sls plugin install -n serverless-python-requirements
3. sls plugin install -n serverless-offline
4. python3.9 -m env venv
5. source env/bin/activate
6. bash ./install.sh

# login and connect to AWS

sls login: login to serverless dashboard. If you haven't done so, the dashboard must connect to your AWS provider.

# python requirements bundling

Make sure you have the following in the serverless.yml

```
functions:
  pre_process:
    handler: handler.pre_process
    events:
      - http:
          path: /pre-process
          method: post
    layers:
      - Ref: PythonRequirementsLambdaLayer

plugins:
  - serverless-python-requirements
  - serverless-offline
custom:
  pythonRequirements:
    dockerizePip: true
    layer: true
```

# using env variables

- install doppler cli
- `brew install jq`
- doppler login -> doppler setup -> select project and stage
- `import os` and then `os.environ['KEY']` to get the env variable
- AFTER DEPLOYMENT, sync env variables by `bash ./secrets.sh lambda_function_name` , the lambda function name is the name you see in the aws lambda functions console
  - bash ./secrets.sh api-jarvis-ai-dev-auth_google
  - bash ./secrets.sh api-jarvis-ai-dev-start_jarvis

# test and deployment

Docker must be open.

- Make sure to use `doppler setup` to set the correct environment (usually "prd")
- doppler run -- sls deploy: deploy to AWS. Should see in the log "installing requirements". To sync `bash ./secrets.sh lambda_function_name`
- doppler run -- sls invoke --function <function_name>: invoke locally after you deploy your function
- doppler run -- sls offline: use localhost to test api. Use `curl -X POST http://localhost:3000/dev/pre-process` to test response. When you make changes, you need to restart the local server.

# code base structure

-> lib: libary functions

-> storage: functions for interacting with storage

-> source:

    - core: main code

    - models: models for tools

    - services: providers for credentials, user context, api keys, etc

    - tools: tools to use for agents
