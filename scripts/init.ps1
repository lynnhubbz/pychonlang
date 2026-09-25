
python -m pip install -r requirements.txt


git submodule update --init --recursive

npx esbuild src/js/entry.js --bundle --format=iife --global-name=CE --outfile=src/js/dist/ce-bundle.js --loader:.jsx=jsx     
dotnet build src\csharp -c Release
