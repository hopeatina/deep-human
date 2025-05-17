#!/usr/bin/env python3
"""
Test script to verify configuration loading.
"""

import os
import sys
from config import HumanConfig


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_config.py <config_file_path>")
        sys.exit(1)

    config_path = sys.argv[1]
    abs_config_path = os.path.abspath(config_path)

    print(f"Testing config loading from: {abs_config_path}")

    # Check if the file exists
    if not os.path.exists(abs_config_path):
        print(f"Error: Config file not found at {abs_config_path}")
        sys.exit(1)

    # Try to load the config
    try:
        config = HumanConfig(abs_config_path)
        print("\nConfiguration loaded successfully!\n")

        # Print out key configuration values
        print(f"Persona Name: {config.get_persona_name()}")
        print(f"Persona Style: {config.get_persona_style()}")

        print("\nMatching Weights:")
        weights = config.get_matching_weights()
        for key, value in weights.items():
            print(f"  {key}: {value}")

        print("\nLLM Config:")
        llm_config = config.get_llm_config()
        for key, value in llm_config.items():
            print(f"  {key}: {value}")

        # Test if we can get a specific value
        bio = config.get("persona", "bio")
        print(f"\nBio: {bio}")

    except Exception as e:
        print(f"Error loading configuration: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
