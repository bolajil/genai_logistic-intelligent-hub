from pathlib import Path
import pandas as pd

def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)

def save_parquet(df: pd.DataFrame, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
