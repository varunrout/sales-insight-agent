from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent

MODEL_NAME = "claude-sonnet-4-5"
MODEL_TEMPERATURE = 0.0

DATA_PATH = ROOT_DIR / "data" / "sample_sales.csv"
DOCS_PATH = ROOT_DIR / "data" / "docs"
QUESTIONS_PATH = ROOT_DIR / "data" / "sample_questions.json"
VECTOR_STORE_PATH = ROOT_DIR / "rag" / "chroma_db"
CHART_OUTPUT_PATH = ROOT_DIR / "outputs" / "charts"
MODEL_OUTPUT_PATH = ROOT_DIR / "models"
