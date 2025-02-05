# {{cookiecutter.project_name}}

{{cookiecutter.pattern_description}}

Template generated with `googleCloudPlatform/agent-starter-pack`

## Project Structure

This project is organized as follows:

```
{{cookiecutter.project_name}}/
├── app/                 # Core application code
│   ├── agent.py         # Main agent logic
│   ├── agent_engine_app.py # Agent Engine application logic
│   └── utils/           # Utility functions and helpers
├── deployment/          # Infrastructure and deployment scripts
├── notebooks/           # Jupyter notebooks for prototyping and evaluation
├── tests/               # Unit, integration, and load tests
├── Makefile             # Makefile for common commands
└── pyproject.toml       # Project dependencies and configuration
```


### Installation

Install required packages using uv:

```bash
uv sync --extra jupyter --extra streamlit 
```

### Setup

If not done during the initialization, set your default Google Cloud project and Location:

```bash
export PROJECT_ID="YOUR_PROJECT_ID"
export LOCATION="us-central1"
gcloud config set project $PROJECT_ID
gcloud auth application-default login
gcloud auth application-default set-quota-project $PROJECT_ID
```

## Commands

| Command              | Description                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------- |
| `make playground`    | Start Streamlit for local playground execution with automatic agent reloading.                                |
| `make backend`       | Deploy your Agent remotely in Agent Engine                                        |
| `make test`          | Run unit and integration tests                                                              |
| `make load_test`     | Execute load tests (see [tests/load_test/README.md](tests/load_test/README.md) for details) |
| `uv run jupyter lab` | Launch Jupyter notebook                                                                     |

For full command options and usage, refer to the [Makefile](Makefile).

## Usage
1. **Prototype:** Build your Generative AI Agent using the intro notebooks in `notebooks/` for guidance. Use Vertex AI Evaluation to assess performance.
2. **Integrate:** Import your chain into the app by editing `app/agent.py`.
3. **Test:** Explore your chain's functionality using the Streamlit playground with `make playground`. The playground offers features like chat history, user feedback, and various input types, and automatically reloads your agent on code changes.
4. **Deploy:** Configure and trigger the CI/CD pipelines, editing tests if needed. See the [deployment section](#deployment) for details.
5. **Monitor:** Track performance and gather insights using Cloud Logging, Tracing, and the Looker Studio dashboard to iterate on your application.

## Deployment

### Dev Environment

You can test deployment towards a Dev Environment using the following command:

```bash
gcloud config set project <your-dev-project-id>
make backend
```

The repository includes a Terraform configuration for the setup of the Dev Google Cloud project.
See [deployment/README.md](deployment/README.md) for instructions.

### Production Deployment

The repository includes a Terraform configuration for the setup of a production Google Cloud project. Refer to [deployment/README.md](deployment/README.md) for detailed instructions on how to deploy the infrastructure and application.

## Monitoring and Observability

>> You can use [this Looker Studio dashboard](https://lookerstudio.google.com/c/reporting/fa742264-4b4b-4c56-81e6-a667dd0f853f/page/tEnnC) template for visualizing events being logged in BigQuery. See the "Setup Instructions" tab to getting started.

The application uses OpenTelemetry for comprehensive observability with all events being sent to Google Cloud Trace and Logging for monitoring and to BigQuery for long term storage. 
