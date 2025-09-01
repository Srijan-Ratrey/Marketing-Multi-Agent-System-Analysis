"""
Setup verification script for Marketing Multi-Agent System Analysis
"""
import sys
import os
import pandas as pd

def verify_environment():
    """Verify that the environment is set up correctly"""
    print("🔍 Verifying Project Setup")
    print("=" * 50)
    
    # Check Python version
    python_version = sys.version_info
    print(f"✓ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check key libraries
    try:
        import pandas as pd
        import numpy as np
        import matplotlib.pyplot as plt
        import seaborn as sns
        import plotly.express as px
        import sklearn
        import jupyter
        print("✓ All required libraries installed")
    except ImportError as e:
        print(f"✗ Missing library: {e}")
        return False
    
    # Check dataset availability
    data_dir = "marketing_multi_agent_dataset_v1_final/"
    if os.path.exists(data_dir):
        print(f"✓ Dataset directory found: {data_dir}")
        
        # Count available CSV files
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        print(f"✓ Found {len(csv_files)} CSV files")
        
        # Test loading a sample file
        try:
            sample_file = os.path.join(data_dir, 'campaigns.csv')
            if os.path.exists(sample_file):
                df = pd.read_csv(sample_file)
                print(f"✓ Successfully loaded sample dataset: {df.shape}")
            else:
                print("✗ Sample dataset not found")
        except Exception as e:
            print(f"✗ Error loading sample dataset: {e}")
    else:
        print(f"✗ Dataset directory not found: {data_dir}")
        return False
    
    # Check project structure
    required_dirs = ['analysis', 'notebooks', 'scripts', 'data', 'results', 'docs']
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"✓ Directory exists: {dir_name}")
        else:
            print(f"✗ Directory missing: {dir_name}")
    
    # Check key files
    required_files = ['requirements.txt', 'README.md', '.gitignore']
    for file_name in required_files:
        if os.path.exists(file_name):
            print(f"✓ File exists: {file_name}")
        else:
            print(f"✗ File missing: {file_name}")
    
    print("\n🎉 Setup verification completed!")
    print("\n🚀 Next steps:")
    print("1. Run: jupyter lab")
    print("2. Open: notebooks/marketing_analysis.ipynb")
    print("3. Start exploring the dataset!")
    
    return True

if __name__ == "__main__":
    verify_environment()
