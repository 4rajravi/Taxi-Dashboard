import warnings
import zipfile
import pandas as pd  # type: ignore
import glob
from pathlib import Path

from utils.logger import get_logger

warnings.filterwarnings("ignore")


class DataReader:
    """
    Reads, cleans, and processes taxi data from zipped .txt files.

    This class extracts all .txt files from ZIP archives in a given directory,
    cleans the data, merges it, and saves it to a serialized format (.pkl).
    """

    def __init__(
        self,
        dataset_size_limit: int,
        input_dir: str,
        output_dir: str,
        output_file: str = "merged_cleaned_data.pkl",
    ):
        """
        Initializes the DataReader with input/output paths and logging.

        Parameters:
            input_dir (str): Directory containing input ZIP files.
            output_dir (str): Directory to save the cleaned data.
            output_file (str): Filename for the output pickle file.
        """
        self.dataset_size_limit = dataset_size_limit
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_file = output_file
        self.logger = get_logger("DataReader", "datareader.log")
        self.columns = ["taxi_id", "timestamp", "longitude", "latitude"]

    def extract_and_clean(self) -> pd.DataFrame:
        """
        Extracts the first 'dataset_size_limit' .txt files from ZIP archives in the input directory,
        reads the content into DataFrames, cleans the data, adds trip_status,
        and combines them into one DataFrame.
        """
        all_dfs = []
        processed_files = 0  # Keep track of how many files have been processed

        for zip_path in glob.glob(str(self.input_dir / "*.zip")):
            self.logger.info(f"Processing {self.dataset_size_limit} files in: {zip_path}")
            try:
                with zipfile.ZipFile(zip_path, "r") as zip_ref:

                    for name in zip_ref.namelist():
                        if not name.endswith(".txt"):
                            continue

                        # Stop processing once we've reached the dataset_size_limit limit
                        if processed_files >= self.dataset_size_limit:
                            self.logger.info(
                                f"Dataset size limit of {self.dataset_size_limit} files reached. Stopping further processing."
                            )
                            break

                        try:
                            with zip_ref.open(name) as file:
                                df = pd.read_csv(file, header=None, names=self.columns)

                                if df.empty:
                                    self.logger.warning(f"Empty file: {name}")
                                    continue

                                # Fill taxi_id with the name of the .txt file if missing
                                df["taxi_id"].fillna(Path(name).stem, inplace=True)

                                # Replace null longitude and latitude with -1
                                df["longitude"].fillna(-1, inplace=True)
                                df["latitude"].fillna(-1, inplace=True)

                                # Replace values out of valid range with -1
                                df.loc[~df["longitude"].between(-180, 180), "longitude"] = -1
                                df.loc[~df["latitude"].between(-90, 90), "latitude"] = -1


                                # Convert timestamp to datetime and drop invalid timestamps
                                df["timestamp"] = pd.to_datetime(
                                    df["timestamp"], errors="coerce"
                                )
                                df.dropna(subset=["timestamp"], inplace=True)

                                # Add trip_status column and mark the last row
                                df["trip_status"] = "active"
                                if not df.empty:
                                    df.iloc[-1, df.columns.get_loc("trip_status")] = (
                                        "end"
                                    )

                                all_dfs.append(df)
                                processed_files += 1  # Increment file counter
                        except Exception as e:
                            self.logger.error(
                                f"Error reading file '{name}' from ZIP archive. Error: {e}"
                            )

                    if processed_files >= self.dataset_size_limit:
                        break  # Exit the loop once we hit the dataset size limit

            except Exception as e:
                self.logger.error(f"Failed to open zip {zip_path}: {e}")

            if processed_files >= self.dataset_size_limit:
                break  # Exit the outer loop if the dataset size limit is reached

        if not all_dfs:
            self.logger.error("No valid data found.")
            return pd.DataFrame(columns=self.columns + ["trip_status"])

        combined = pd.concat(all_dfs, ignore_index=True).drop_duplicates()
        combined.sort_values(by="timestamp", inplace=True)
        self.logger.info(f"Total merged rows: {len(combined)}")
        return combined

    def save(self, df: pd.DataFrame):
        """
        Saves the cleaned DataFrame to a pickle file in the output directory.

        Parameters:
            df (pd.DataFrame): The cleaned data to save.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / self.output_file
        df.to_pickle(path)
        self.logger.info(f"Data saved to: {path}")

    def process(self):
        """
        Main entry point to extract, clean, and save data.
        """
        df = self.extract_and_clean()
        if not df.empty:
            self.save(df)


if __name__ == "__main__":
    # Execute the data processing pipeline when run directly
    reader = DataReader("data/", "data/processed")
    reader.process()
