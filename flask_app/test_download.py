import kagglehub
import os

print("Testing kagglehub download...")

try:
    # Download latest version
    path = kagglehub.dataset_download("arindam235/startup-investments-crunchbase")
    print("Path to dataset files:", path)
    
    # List files in the path
    if os.path.exists(path):
        files = os.listdir(path)
        print("Files in download path:")
        for file in files:
            print(f"  - {file}")
    else:
        print("Download path doesn't exist!")
        
except Exception as e:
    print(f"Error downloading dataset: {e}")