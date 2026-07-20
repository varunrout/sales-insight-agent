from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent

RAW_CSV_PATH = ROOT_DIR / "data" / "sample_sales.csv"
DATA_PATH = ROOT_DIR / "data" / "sales.db"
DOCS_PATH = ROOT_DIR / "data" / "docs"
QUESTIONS_PATH = ROOT_DIR / "data" / "sample_questions.json"
VECTOR_STORE_PATH = ROOT_DIR / "rag" / "chroma_db"
CHART_OUTPUT_PATH = ROOT_DIR / "outputs" / "charts"
