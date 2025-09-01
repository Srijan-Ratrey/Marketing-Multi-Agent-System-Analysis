#!/usr/bin/env python3
"""
View Diagrams Script

Opens the interactive diagram viewer in the default web browser.
"""

import webbrowser
import os
from pathlib import Path

def open_diagram_viewer():
    """Open the interactive diagram viewer"""
    
    # Get the path to the HTML file
    project_root = Path(__file__).parent.parent
    html_file = project_root / "docs" / "graph-viewer.html"
    
    if not html_file.exists():
        print("❌ Error: graph-viewer.html not found!")
        print(f"Expected location: {html_file}")
        return
    
    # Convert to file URL
    file_url = f"file://{html_file.absolute()}"
    
    print("🖼️ Opening Interactive Diagram Viewer...")
    print(f"📁 Location: {html_file}")
    print(f"🌐 URL: {file_url}")
    
    try:
        # Open in default browser
        webbrowser.open(file_url)
        print("✅ Diagram viewer opened successfully!")
        print("\n📋 Available diagrams:")
        print("  • Lead Processing Workflow")
        print("  • Agent Communication Sequence")
        print("  • System Architecture")
        print("  • Scalability Design (10x Load)")
        
    except Exception as e:
        print(f"❌ Error opening browser: {e}")
        print(f"💡 Manual access: Open {file_url} in your browser")

def show_mermaid_alternatives():
    """Show alternative ways to view Mermaid diagrams"""
    print("\n🎯 Alternative ways to view diagrams:")
    print("=" * 50)
    
    print("1. 🌐 Online Mermaid Editor:")
    print("   • Visit: https://mermaid.live/")
    print("   • Copy Mermaid code from docs/*.md files")
    print("   • Paste and view rendered diagrams")
    
    print("\n2. 📝 VS Code Extension:")
    print("   • Install 'Mermaid Preview' extension")
    print("   • Open any .md file with diagrams")
    print("   • Press Ctrl+Shift+V for preview")
    
    print("\n3. 🐙 GitHub Automatic Rendering:")
    print("   • Push project to GitHub")
    print("   • All ```mermaid blocks render automatically")
    print("   • Perfect for sharing with assessors")
    
    print("\n4. 🖼️ Export as Images:")
    print("   • Use Mermaid CLI: npm install -g @mermaid-js/mermaid-cli")
    print("   • Export: mmdc -i input.md -o output.png")
    
    print("\n5. 📊 Notion/Obsidian:")
    print("   • Both support Mermaid rendering")
    print("   • Copy diagrams to these tools for viewing")

if __name__ == "__main__":
    print("🤖 Marketing Multi-Agent System - Diagram Viewer")
    print("=" * 55)
    
    # Try to open the interactive viewer
    open_diagram_viewer()
    
    # Show alternatives
    show_mermaid_alternatives()
    
    print("\n💡 For assessment presentation:")
    print("   Use the HTML viewer for interactive demos")
    print("   Or push to GitHub for automatic rendering")
