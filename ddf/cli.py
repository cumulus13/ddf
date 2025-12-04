#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Command-line interface for DDF.
"""

def main():
    """Main entry point for the DDF CLI."""
    from .ddf import Usage
    
    try:
        Usage.usage()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        import sys
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}")
        import sys
        import os
        if os.getenv('DDF_DEBUG'):
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()