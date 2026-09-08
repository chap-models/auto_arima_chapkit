"""ML service for auto_arima_chapkit."""

import os
from pathlib import Path

from chapkit import BaseConfig
from chapkit.api import AssessedStatus, MLServiceBuilder, MLServiceInfo, ModelMetadata, PeriodType
from chapkit.artifact import ArtifactHierarchy
from chapkit.ml import ShellModelRunner


class AutoArimaChapkitConfig(BaseConfig):
    """Configuration for auto_arima_chapkit."""

    # Required: number of prediction periods
    prediction_periods: int = 3

    # Add your model-specific parameters here
    # Config fields can be accessed by external scripts via config.yml
    # For example:
    # min_samples: int = 5
    # model_type: str = "linear_regression"


# Create shell-based runner with command templates
# The runner copies the entire project directory to an isolated workspace
# and executes commands with the workspace as the current directory.
# This allows scripts to use relative paths and imports.
#
# Variables will be substituted with actual file paths at runtime:
#   {data_file} - Training data CSV
#   {historic_file} - Historic data CSV
#   {future_file} - Future data CSV
#   {output_file} - Predictions CSV
#   {geo_file} - Optional GeoJSON file (if provided)
#
# Files available in workspace (scripts can access directly):
#   config.yml - YAML config (always available)
#   model.pickle - Model file (create/use as needed)

# The runner with train and predict commands
runner: ShellModelRunner[AutoArimaChapkitConfig] = ShellModelRunner(
    train_command="Rscript scripts/train.R --data {data_file}",
    predict_command=(
        "Rscript scripts/predict.R  --historic {historic_file} --future {future_file} --output {output_file}"
    ),
)

# Create ML service info with metadata
info = MLServiceInfo(
    id="auto-arima-chapkit",
    display_name="Auto_ARIMA (chapkit)",
    version="1.0.0",
    description="An ARIMA model which automatically chooses the hyperparameters using the function ARIMA() from the fable package.",
    model_metadata=ModelMetadata(
        author="Harsha (adapted to chapkit by Halvard)",
        author_assessed_status=AssessedStatus.red,
        contact_email="halvares@uio.no",
        organization="Cardiff University",
        organization_logo_url="https://wp.logos-download.com/wp-content/uploads/2016/11/Cardiff_University_logo_logotype.png",
    ),
    period_type=PeriodType.monthly,
    allow_free_additional_continuous_covariates=False,
    min_prediction_periods=0,
    max_prediction_periods=12,
)

# Create artifact hierarchy for ML artifacts
HIERARCHY = ArtifactHierarchy(
    name="auto_arima_chapkit",
    level_labels={0: "ml_training_workspace", 1: "ml_prediction"},
)

# Database configuration
# Uses environment variable or defaults to data/chapkit.db
# Creates data directory if it doesn't exist
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///data/chapkit.db")
if DATABASE_URL.startswith("sqlite") and ":///" in DATABASE_URL:
    db_path = Path(DATABASE_URL.split("///")[1])
    db_path.parent.mkdir(parents=True, exist_ok=True)

# Build the FastAPI application
app = (
    MLServiceBuilder(
        info=info,
        config_schema=AutoArimaChapkitConfig,
        hierarchy=HIERARCHY,
        runner=runner,
        database_url=DATABASE_URL,
    )
    # ====================================================================================
    # CHAP Core Registration (Optional)
    # ====================================================================================
    # Uncomment to automatically register this service with CHAP Core on startup.
    # Replace the URL with your CHAP Core instance.
    #
    # For Docker deployments, you can set these environment variables instead:
    #   SERVICEKIT_ORCHESTRATOR_URL - the registration endpoint URL
    #   SERVICEKIT_REGISTRATION_KEY - the secret key (only if enabled on CHAP Core)
    #
    # The service will:
    # - Auto-detect hostname (works with Docker container names)
    # - Retry registration on failure (default: 5 retries, 2s delay)
    # - Send keepalive pings to stay registered (default: 10s interval, 30s TTL)
    # - Gracefully deregister on shutdown
    #
    # .with_registration(
    #     orchestrator_url="https://chap.example.org/v2/services/$register",
    #     registration_key="your-secret-key",  # or use SERVICEKIT_REGISTRATION_KEY env var
    # )
    .with_registration()
    .build()
)


if __name__ == "__main__":
    from chapkit.api import run_app

    # Set reload=True to enable hot reloading during development
    run_app("main:app", reload=False)