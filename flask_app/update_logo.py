#!/usr/bin/env python3
"""
Deal Scout Logo Integration Script

This script will help you integrate the Deal Scout logo image.

Instructions:
1. Save the attached Deal Scout logo image as 'deal-scout-logo.png' in the static/images/ directory
2. Run this script to update the HTML template to use the image instead of the CSS placeholder
3. The logo will appear in the header with proper styling

The logo should be:
- PNG format for transparency
- High resolution for crisp display  
- The script will automatically scale it to 50px height
"""

import os
import sys

def update_logo_in_template():
    """Update the HTML template to use the actual logo image"""
    
    template_path = 'templates/index.html'
    logo_path = 'static/images/deal-scout-logo.png'
    
    # Check if logo file exists
    if not os.path.exists(logo_path):
        print(f"❌ Logo file not found: {logo_path}")
        print("Please save the Deal Scout logo as 'deal-scout-logo.png' in the static/images/ directory")
        return False
    
    # Read the template file
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ Template file not found: {template_path}")
        return False
    
    # Replace the CSS placeholder with the actual logo
    old_logo = '''<span class="logo-placeholder" style="display: inline-block; width: 50px; height: 50px; background: linear-gradient(45deg, #1e3a8a, #3b82f6); border-radius: 50%; margin-right: 15px; vertical-align: middle; position: relative;">
                        <i class="fas fa-search" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: white; font-size: 20px;"></i>
                    </span>'''
    
    new_logo = '<img src="/static/images/deal-scout-logo.png" alt="Deal Scout" style="height: 50px; margin-right: 15px; vertical-align: middle;">'
    
    if old_logo in content:
        content = content.replace(old_logo, new_logo)
        
        # Write the updated content back
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Successfully updated template to use Deal Scout logo image")
        print("The logo will now appear in the header when you refresh the page")
        return True
    else:
        print("⚠️ Logo placeholder not found in template - may already be updated")
        return False

if __name__ == '__main__':
    print("Deal Scout Logo Integration")
    print("=" * 30)
    
    # Change to the flask_app directory
    if os.path.basename(os.getcwd()) != 'flask_app':
        if os.path.exists('flask_app'):
            os.chdir('flask_app')
            print(f"📁 Changed to flask_app directory: {os.getcwd()}")
        else:
            print("❌ Please run this script from the project root or flask_app directory")
            sys.exit(1)
    
    # Update the logo
    if update_logo_in_template():
        print("\n🎉 Logo integration complete!")
        print("💡 Refresh your browser to see the new Deal Scout logo")
    else:
        print("\n⚠️ Logo integration incomplete")
        print("Please ensure the logo file is saved as 'static/images/deal-scout-logo.png'")