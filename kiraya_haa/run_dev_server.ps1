Set-Location $PSScriptRoot
python -m flask --app app:create_app run --host 127.0.0.1 --port 5000
