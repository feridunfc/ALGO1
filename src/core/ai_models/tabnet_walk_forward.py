# tabnet_walk_forward.py
# Walk-Forward Validation with TabNet for time-series classification
# NOTE: Update FILE_PATH, PRICE_COLUMN, TIME_COLUMN accordingly.

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, roc_auc_score
import torch
from pytorch_tabnet.tab_model import TabNetClassifier
import matplotlib.pyplot as plt
import seaborn as sns

def create_time_series_features(df, target_col, lags=[1, 2, 3, 5, 10], rolling_windows=[5, 10]):
    """
    Generates lag and rolling window features from a time-series DataFrame.
    Creates a binary target: 1 if next step increases vs current step, else 0.
    Returns (X, y).
    """
    df_feat = df.copy()
    for lag in lags:
        df_feat[f'lag_{lag}'] = df_feat[target_col].shift(lag)
    for window in rolling_windows:
        df_feat[f'rolling_mean_{window}'] = df_feat[target_col].shift(1).rolling(window=window).mean()
        df_feat[f'rolling_std_{window}'] = df_feat[target_col].shift(1).rolling(window=window).std()
    df_feat['target'] = (df_feat[target_col].shift(-1) > df_feat[target_col]).astype(int)
    df_feat = df_feat.dropna()
    return df_feat.drop(columns=[target_col]), df_feat['target']

def walk_forward_generator(data_length, train_size, test_size, step=1):
    """Yields (train_idx, test_idx) for walk-forward validation."""
    start = 0
    while start + train_size + test_size <= data_length:
        train_end = start + train_size
        test_end = train_end + test_size
        yield (np.arange(start, train_end), np.arange(train_end, test_end))
        start += step

if __name__ == '__main__':
    # --- Configuration ---
    FILE_PATH = 'path/to/your/time_series_data.csv'  # <<< CHANGE THIS
    PRICE_COLUMN = 'Close'                           # <<< CHANGE THIS
    TIME_COLUMN = 'Date'                             # <<< CHANGE THIS
    
    # Walk-Forward Parameters
    TRAIN_SIZE = 252  # ~ 1 trading year
    TEST_SIZE = 63    # ~ 1 trading quarter
    STEP_SIZE = 63    # slide by a quarter
    
    # --- Data Preparation ---
    try:
        df = pd.read_csv(FILE_PATH, parse_dates=[TIME_COLUMN])
        df = df.sort_values(TIME_COLUMN).reset_index(drop=True)
    except FileNotFoundError:
        print(f"Error: The file '{FILE_PATH}' was not found. Please update the path.")
        raise SystemExit(1)
        
    X, y = create_time_series_features(df, PRICE_COLUMN)
    
    # --- Walk-Forward Validation Loop ---
    test_scores = []
    final_model = None
    fold_number = 0
    
    wf_generator = walk_forward_generator(len(X), TRAIN_SIZE, TEST_SIZE, STEP_SIZE)
    
    print("Starting Walk-Forward Validation...")
    for train_indices, test_indices in wf_generator:
        fold_number += 1
        
        X_train, y_train = X.iloc[train_indices], y.iloc[train_indices]
        X_test, y_test = X.iloc[test_indices], y.iloc[test_indices]
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        clf = TabNetClassifier(
            optimizer_fn=torch.optim.Adam,
            optimizer_params=dict(lr=2e-2),
            scheduler_params={"step_size": 10, "gamma": 0.9},
            scheduler_fn=torch.optim.lr_scheduler.StepLR,
            mask_type='sparsemax',
            verbose=0
        )
        
        clf.fit(
            X_train=X_train_scaled, y_train=y_train.values,
            eval_set=[(X_test_scaled, y_test.values)],
            max_epochs=100,
            patience=15,
            batch_size=1024,
            eval_metric=['accuracy', 'auc']
        )
        
        preds = clf.predict(X_test_scaled)
        score = accuracy_score(y_test, preds)
        test_scores.append(score)
        
        print(f"Fold {fold_number}: Train {X_train.index.min()}-{X_train.index.max()}, "
              f"Test {X_test.index.min()}-{X_test.index.max()}, Accuracy: {score:.4f}")
        
        final_model = clf
    
    if not test_scores:
        print("\nWalk-forward validation produced no folds. Adjust TRAIN_SIZE/TEST_SIZE.")
    else:
        print("\n--- Walk-Forward Validation Summary ---")
        print(f"Number of folds: {len(test_scores)}")
        print(f"Mean Accuracy: {np.mean(test_scores):.4f}")
        print(f"Std Dev of Accuracy: {np.std(test_scores):.4f}")
        
        if final_model:
            print("\n--- Feature Importance of Final Model ---")
            importance_df = pd.DataFrame({
                'feature': X.columns,
                'importance': final_model.feature_importances_
            }).sort_values('importance', ascending=False)

            plt.figure(figsize=(12, 8))
            sns.barplot(x='importance', y='feature', data=importance_df)
            plt.title('Global Feature Importances from Final Model')
            plt.tight_layout()
            plt.show()
            print(importance_df.to_string(index=False))
