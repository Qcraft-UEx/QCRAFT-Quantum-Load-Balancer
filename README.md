<p align="center">
   <picture>
     <source media="(prefers-color-scheme: dark)" srcset="https://github.com/Qcraft-UEx/Qcraft/blob/main/docs/_images/qcraft_logo.png?raw=true" width="60%">
     <img src="https://github.com/Qcraft-UEx/Qcraft/blob/main/docs/_images/qcraft_logo.png?raw=true" width="60%" alt="Qcraft Logo">
   </picture>
  </a>
</p>

# QCRAFT Quantum Load Balancer
QCRAFT Quantum Load Balancer: A tool for quantum orchestration, integrating load balancing and resource allocation for efficient task execution.

### Description ###

This repository provides a Quantum Load Balancer. This tool is utilized to distribute workload across different quantum service providers and quantum resources, aiming to maximize the efficiency and quality of quantum task execution. Which results in better utilization of available resources.


### Requirements ###

The following is a list of the libraries needed to be able to execute the balancer

* Python 3
* pip3
* boto3
* flask
* flask_cors
* amazon-braket-sdk
* qiskit_ibm_provider
* qiskit_ibm_runtime

### Starting Quantum Load Balancer ###

Steps to start the Quantum Load Balancer: 

1. Replace the "IBM_TOKEN" in the "balancer_ibm.py" file with the IBM Quantum token

2. Replace the "AWS_KEY_ID" in the "main.py" file with the "aws_access_key_id" of AWS

3. Replace the "AWS_SECRET_KEY" in the "main.py" file with the "aws_secret_access_key" of AWS

4. Follow the steps below for the creation and deployment of the load balancer image:

    4.1  Execute the following command to create the Docker image: docker build -t load_balancer:1.0 .

    4.2  Execute the following command to deploy the container using the previously created image: 
    
    docker run --name load_balancer -p 5000:5000 -t load_balancer:1.0

### Executing Quantum Load Balancer ###

See the configuration of the experiments in the "ExperimentsConfiguration" file with some sample JSON


### Main endpoints ###

* /execute_aws/info
* /execute_aws/show/info
* /execute_aws/show
* /execute_aws
* /execute_ibm/info
* /execute_ibm/show/info
* /execute_ibm/show
* /execute_ibm
* /execute_aws_ibm/info
* /execute_aws_ibm





## License
QCRAFT Quantum Load Balancer is licensed under the [MIT License](https://github.com/Qcraft-UEx/QCRAFT/blob/main/LICENSE)
