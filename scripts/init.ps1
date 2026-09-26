# Ensure the script stops immediately if any command fails
$ErrorActionPreference = "Stop"

# 1. Install dependencies
python -m pip install -r requirements.txt
npm install

# 2. Update submodules recursively
git submodule update --init --recursive

# 3. Bundle JavaScript assets (Using forward slashes for cross-OS compatibility)
npx esbuild src/bridge/js/entry.js --bundle --format=iife --global-name=CE --outfile=src/bridge/js/dist/ce-bundle.js --loader:.jsx=jsx     

# 4. Build .NET project (Unified to cross-platform forward-slash paths)
dotnet build ./src/bridge/net -c Release
