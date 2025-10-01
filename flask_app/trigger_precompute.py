#!/usr/bin/env python3
"""
Simple script to trigger precomputation for Deal Scout
Run this after starting the Flask server
"""
import requests
import json
import sys
import time

SERVER_URL = "http://localhost:5000"

def check_server():
    """Check if server is running"""
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def check_precompute_status():
    """Check current precomputation status"""
    try:
        response = requests.get(f"{SERVER_URL}/api/admin/precompute/status")
        return response.json()
    except Exception as e:
        print(f"Error checking status: {e}")
        return None

def trigger_precompute(max_rows=400, save_to_disk=True):
    """Trigger precomputation"""
    print(f"\n🚀 Triggering precomputation for {max_rows} companies...")
    print("⏳ This may take 30 seconds to 2 minutes depending on dataset size...\n")
    
    try:
        response = requests.post(
            f"{SERVER_URL}/api/admin/precompute",
            json={
                'max_rows': max_rows,
                'save_to_disk': save_to_disk
            },
            timeout=600  # 10 minute timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Precomputation completed successfully!\n")
            print(f"📊 Results:")
            print(f"   Total scored: {result.get('counts', {}).get('total_scored', 0)}")
            print(f"   🟢 Invest:    {result.get('counts', {}).get('invest', 0)}")
            print(f"   🟡 Monitor:   {result.get('counts', {}).get('monitor', 0)}")
            print(f"   🔴 Avoid:     {result.get('counts', {}).get('avoid', 0)}")
            print(f"   💾 Saved to cache: {result.get('saved_to_cache', False)}")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return False
            
    except requests.Timeout:
        print("❌ Request timed out. Precomputation may still be running.")
        print("   Check server logs or try checking status in a few minutes.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("Deal Scout - Precomputation Trigger")
    print("=" * 60)
    
    # Check if server is running
    print("\n🔍 Checking if server is running...")
    if not check_server():
        print("❌ Server is not running at", SERVER_URL)
        print("\n📝 Start the server first:")
        print('   cd "c:\\Users\\jamie\\OneDrive\\Documents\\Deal Scout\\flask_app"')
        print('   $env:AUTO_TRAIN_ON_IMPORT="false"')
        print('   & "C:/Users/jamie/OneDrive/Documents/Deal Scout/.venv/Scripts/python.exe" app.py')
        sys.exit(1)
    
    print("✅ Server is running!")
    
    # Check current status
    print("\n🔍 Checking current precomputation status...")
    status = check_precompute_status()
    if status:
        if status.get('available'):
            print(f"✅ Precomputed data already available!")
            print(f"   {status.get('precomputed_count', 0)} / {status.get('total_companies', 0)} companies ({status.get('coverage_percentage', 0):.1f}%)")
            
            response = input("\n❓ Recompute anyway? (y/N): ").strip().lower()
            if response != 'y':
                print("\n👋 Exiting. No changes made.")
                sys.exit(0)
        else:
            print(f"⚠️  Precomputed data not available")
            print(f"   Only {status.get('precomputed_count', 0)} / {status.get('total_companies', 0)} companies precomputed")
    
    # Get parameters
    print("\n⚙️  Configuration:")
    max_rows_input = input(f"   Max rows to compute (default: 400, press Enter to use default): ").strip()
    max_rows = int(max_rows_input) if max_rows_input else 400
    
    save_input = input(f"   Save to disk cache? (Y/n): ").strip().lower()
    save_to_disk = save_input != 'n'
    
    # Trigger precomputation
    success = trigger_precompute(max_rows, save_to_disk)
    
    if success:
        # Verify it worked
        print("\n🔍 Verifying results...")
        time.sleep(1)
        status = check_precompute_status()
        if status and status.get('available'):
            print(f"✅ Verification successful!")
            print(f"   Coverage: {status.get('coverage_percentage', 0):.1f}%")
            print(f"\n🎉 All done! You can now:")
            print(f"   1. Refresh your browser at {SERVER_URL}")
            print(f"   2. Navigate to 'Evaluate Companies' tab")
            print(f"   3. You should see varied scores (not all 50%)")
        else:
            print("⚠️  Warning: Status still shows data not available")
            print("   Check server logs for errors")
    else:
        print("\n❌ Precomputation failed. Check server logs for details.")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ Process complete!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Exiting...")
        sys.exit(130)
