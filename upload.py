import pandas as pd
import argparse
import os
from dotenv import load_dotenv
from lib.models.SupervisedClassifierDataset import SupervisedClassifierDataset
from lib.db.session import create_db_session

def pattern_to_label(pattern: str) -> int:
    """Convert pattern string to numeric label."""
    pattern_map = {
        'downtrend': 0,
        'sideways': 1,
        'uptrend': 2
    }
    return pattern_map.get(pattern.lower(), -1)

def load_and_process_csv(file_path: str) -> pd.DataFrame:
    """Load and process the CSV file."""
    # Read CSV
    df = pd.read_csv(file_path)
    
    # Convert dates from string to datetime
    df['start_date'] = pd.to_datetime(df['start_date'])
    df['end_date'] = pd.to_datetime(df['end_date'])
    
    # Convert pattern to numeric label
    df['label'] = df['pattern'].apply(pattern_to_label)
    
    return df[['ticker', 'start_date', 'end_date', 'label']]

def upload_to_database(df: pd.DataFrame, session_maker) -> None:
    """Upload data to database."""
    with session_maker() as session:
        try:
            # Delete existing records
            session.query(SupervisedClassifierDataset).delete()
            
            # Create new records
            for _, row in df.iterrows():
                record = SupervisedClassifierDataset(
                    ticker=row['ticker'],
                    start_date=row['start_date'].date(),
                    end_date=row['end_date'].date(),
                    label=row['label']
                )
                session.add(record)
            
            # Commit the transaction
            session.commit()
            print(f"Successfully uploaded {len(df)} records to database")
            
        except Exception as e:
            session.rollback()
            print(f"Error uploading to database: {str(e)}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Upload labeled data to database')
    parser.add_argument('--file', type=str, required=True, help='Path to CSV file')
    
    args = parser.parse_args()
    
    try:
        # Load environment variables
        load_dotenv()
        
        # Load and process CSV
        print("Loading and processing CSV file...")
        df = load_and_process_csv(args.file)
        
        # Create database session using environment variables
        print("Creating database session...")
        session_maker = create_db_session(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "postgres")
        )
        
        # Upload to database
        print("Uploading to database...")
        upload_to_database(df, session_maker)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()