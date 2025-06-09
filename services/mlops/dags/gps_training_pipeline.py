"""
GPSRAG ML Training Pipeline
Airflow DAG for automatisk trening av ML-modeller på GPS-data
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import os
import logging

# Default arguments for DAG
default_args = {
    'owner': 'gpsrag-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create DAG
dag = DAG(
    'gps_training_pipeline',
    default_args=default_args,
    description='ML pipeline for GPS data analysis',
    schedule_interval=timedelta(days=7),  # Kjør ukentlig
    catchup=False,
    tags=['ml', 'gps', 'training'],
)

def extract_gps_data(**context):
    """Hent GPS-data fra database"""
    logging.info("Ekstraherer GPS-data fra database...")
    
    # TODO: Implementer faktisk database-tilkobling
    # Eksempel på hvordan data kan se ut:
    sample_data = pd.DataFrame({
        'latitude': np.random.uniform(59.9, 60.0, 1000),
        'longitude': np.random.uniform(10.7, 10.8, 1000),
        'altitude': np.random.uniform(0, 500, 1000),
        'speed': np.random.uniform(0, 30, 1000),
        'timestamp': pd.date_range('2024-01-01', periods=1000, freq='1min')
    })
    
    # Lagre til midlertidig fil
    data_path = '/opt/airflow/data/raw_gps_data.csv'
    sample_data.to_csv(data_path, index=False)
    logging.info(f"GPS-data lagret til {data_path}")
    
    return data_path

def preprocess_data(**context):
    """Preprosesser GPS-data for ML-modell"""
    logging.info("Preprosesserer GPS-data...")
    
    # Les inn rådata
    data_path = context['task_instance'].xcom_pull(task_ids='extract_data')
    df = pd.read_csv(data_path)
    
    # Feature engineering
    df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
    df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek
    df['distance'] = np.sqrt(df['latitude'].diff()**2 + df['longitude'].diff()**2)
    df['acceleration'] = df['speed'].diff()
    
    # Fjern missing values
    df = df.dropna()
    
    # Lag features og target
    features = ['latitude', 'longitude', 'altitude', 'hour', 'day_of_week', 'distance']
    target = 'speed'
    
    X = df[features]
    y = df[target]
    
    # Lagre preprosesserte data
    processed_path = '/opt/airflow/data/processed_gps_data.csv'
    processed_df = pd.concat([X, y], axis=1)
    processed_df.to_csv(processed_path, index=False)
    
    logging.info(f"Preprosesserte data lagret til {processed_path}")
    return processed_path

def train_model(**context):
    """Tren ML-modell for hastighetsforutsigelse"""
    logging.info("Trener ML-modell...")
    
    # Les inn preprosesserte data
    data_path = context['task_instance'].xcom_pull(task_ids='preprocess_data')
    df = pd.read_csv(data_path)
    
    # Split data
    features = ['latitude', 'longitude', 'altitude', 'hour', 'day_of_week', 'distance']
    X = df[features]
    y = df['speed']
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Tren modell
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    # Evaluer modell
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    logging.info(f"Modell MSE: {mse:.4f}")
    logging.info(f"Modell R²: {r2:.4f}")
    
    # Lagre modell
    model_path = '/opt/airflow/data/models/gps_speed_model.joblib'
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    joblib.dump(model, model_path)
    
    # Lagre metrics
    metrics = {
        'mse': mse,
        'r2': r2,
        'feature_importance': dict(zip(features, model.feature_importances_)),
        'training_date': datetime.now().isoformat()
    }
    
    import json
    metrics_path = '/opt/airflow/data/models/model_metrics.json'
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logging.info(f"Modell lagret til {model_path}")
    return model_path

def validate_model(**context):
    """Valider den trente modellen"""
    logging.info("Validerer modell...")
    
    model_path = context['task_instance'].xcom_pull(task_ids='train_model')
    
    # Last inn modell
    model = joblib.load(model_path)
    
    # Enkel validering med test-data
    test_features = np.array([[59.95, 10.75, 100, 12, 1, 0.001]])
    prediction = model.predict(test_features)
    
    logging.info(f"Test predikasjon: {prediction[0]:.2f} km/h")
    
    # Sjekk at predikasjon er rimelig
    if 0 <= prediction[0] <= 50:
        logging.info("Modell validering OK")
        return True
    else:
        logging.error("Modell validering feilet")
        raise ValueError("Modell produserer urealistiske prediksjoner")

def deploy_model(**context):
    """Deploy modell til produksjon"""
    logging.info("Deployer modell til produksjon...")
    
    # TODO: Implementer faktisk deployment
    # Dette kan inkludere:
    # - Kopiering til produksjonsmiljø
    # - Oppdatering av API-endepunkter
    # - A/B testing setup
    
    logging.info("Modell deployment fullført")

# Definer tasks
extract_task = PythonOperator(
    task_id='extract_data',
    python_callable=extract_gps_data,
    dag=dag,
)

preprocess_task = PythonOperator(
    task_id='preprocess_data',
    python_callable=preprocess_data,
    dag=dag,
)

train_task = PythonOperator(
    task_id='train_model',
    python_callable=train_model,
    dag=dag,
)

validate_task = PythonOperator(
    task_id='validate_model',
    python_callable=validate_model,
    dag=dag,
)

deploy_task = PythonOperator(
    task_id='deploy_model',
    python_callable=deploy_model,
    dag=dag,
)

# Cleanup task
cleanup_task = BashOperator(
    task_id='cleanup',
    bash_command='rm -f /opt/airflow/data/raw_gps_data.csv /opt/airflow/data/processed_gps_data.csv',
    dag=dag,
)

# Definer avhengigheter
extract_task >> preprocess_task >> train_task >> validate_task >> deploy_task >> cleanup_task 