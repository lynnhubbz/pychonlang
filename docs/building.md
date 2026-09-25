## Local

1. Run below
```
dotnet build src\bridge-net -c Release
```

2. Run the app
```
python src/app
```

### Build Local

1. standalone
```powershell
python -m nuitka `                
--standalone `
--enable-plugin=pyside6 `
--include-raw-dir=src\bridge-net\bin\Release\net8.0=src\bridge-net\bin\Release\net8.0 `
--include-data-dir=languages=languages `     
--include-data-dir=docs=docs `
--include-data-files=src\app\md-dark.css=src\app\md-dark.css
--include-data-files=src\app\md-light.css=src\app\md-light.css                                         
--output-dir=build `                    
src\app\__main__.py            
```

2. onefile
```powershell            
python -m nuitka `               
--standalone `  
--onefile `                   
--windows-console-mode=force `
--enable-plugin=pyside6 `                                                              
--include-raw-dir=src\bridge-net\bin\Release\net8.0=src\bridge-net\bin\Release\net8.0 `
--include-data-dir=languages=languages `  
--include-data-dir=docs=docs
--include-data-files=src\app\md-dark.css=src\app\md-dark.css
--include-data-files=src\app\md-light.css=src\app\md-light.css`                                             
--onefile-tempdir-spec="{TEMP}/pychonlang_{PID}" `
--output-dir=build `                              
src\app\__main__.py 
```