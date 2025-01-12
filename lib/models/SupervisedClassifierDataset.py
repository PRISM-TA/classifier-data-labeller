from sqlalchemy import Column, Date, String, Integer, schema
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class SupervisedClassifierDataset(Base):
    """
    SQLAlchemy model for supervised classifier dataset.
    This table stores labeled data for training/testing classification models.
    """
    __tablename__ = 'supervised_classifier_dataset'
    __table_args__ = {'schema': 'pg_default'}  # As shown in the image

    # Primary key columns (assuming composite key of start_date, end_date, ticker)
    start_date = Column(Date, primary_key=True)
    end_date = Column(Date, primary_key=True)
    ticker = Column(String, primary_key=True)
    label = Column(Integer)

    def __repr__(self):
        return (f"<SupervisedClassifierDataset("
                f"ticker={self.ticker}, "
                f"start_date={self.start_date}, "
                f"end_date={self.end_date}, "
                f"label={self.label})>")