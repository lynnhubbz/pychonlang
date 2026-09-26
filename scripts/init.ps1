
python -m pip install -r requirements.txt
npm i


git submodule update --init --recursive

npx esbuild src/bridge/js/entry.js --bundle --format=iife --global-name=CE --outfile=src/bridge/js/dist/ce-bundle.js --loader:.jsx=jsx     
dotnet build .\src\bridge\net -c Release
