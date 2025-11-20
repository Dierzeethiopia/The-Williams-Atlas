#!/bin/bash

# Campus Navigator - Quick Start Script
# This script demonstrates the key features of the Campus Navigator system

echo "🚀 Campus Navigator - Quick Start Guide"
echo "=================================="

echo "1. 📊 Viewing Campus Statistics:"
python main.py --load data/campus.json --stats

echo -e "\n2. 🗺️  Finding a Route:"
python main.py --load data/campus.json --from "Main Entrance" --to "Engineering Hall"

echo -e "\n3. ♿ Accessible Route Finding:"
python main.py --load data/campus.json --from "Library" --to "Student Center" --preference accessible

echo -e "\n4. 🏃 Fastest Route Finding:"
python main.py --load data/campus.json --from "Dormitory A" --to "Athletic Center" --preference time

echo -e "\n5. 🌳 Scenic Route Finding:"
python main.py --load data/campus.json --from "Central Quad" --to "Science Building" --preference scenic

echo -e "\n6. 📍 Listing All Locations:"
python main.py --load data/campus.json --list

echo -e "\n✅ Quick Start Complete!"
echo "To explore more features, run: python main.py --interactive"
echo "To run tests, use: python tests/basic_tests.py"
echo "For a full demonstration: python demo.py"