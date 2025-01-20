# Robust Load Testing for Generative AI Applications

This directory provides a comprehensive load testing framework for your Generative AI application, leveraging the power of [Locust](http://locust.io), a leading open-source load testing tool.

##  Load Testing

Follow these steps to execute load tests on your local machine:


**2. (In another tab) Create virtual environment with Locust**
Using another terminal tab, This is suggested to avoid conflicts with the existing application python environment.

```commandline
python3 -m venv locust_env && source locust_env/bin/activate && pip install locust==2.31.1 "google-cloud-aiplatform[evaluation,langchain,reasoningengine]>=1.77.0"
```

**3. Execute the Load Test:**
Trigger the Locust load test with the following command:

```bash
locust -f tests/load_test/load_test.py \
--headless \
-t 30s -u 10 -r 2 \
--csv=tests/load_test/.results/results \
--html=tests/load_test/.results/report.html
```

This command initiates a 30-second load test, simulating 2 users spawning per second, reaching a maximum of 10 concurrent users.

