@ECHO off

call .venv\Scripts\activate.bat
function processing {
    python src\method_processing\main.py @args
}

Set-Alias proc processing -Scope Global
Write-Host "Alias 'proc' created for processing function. Type 'proc --help' for usage."
