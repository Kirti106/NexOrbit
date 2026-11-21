$ErrorActionPreference = "Stop"

$DumpFile = Join-Path (Get-Location) "nexorbit.dump"
docker exec nexorbit_db pg_dump -U root -d nexorbit --format=custom --file=/tmp/nexorbit.dump
docker cp nexorbit_db:/tmp/nexorbit.dump $DumpFile
Write-Host "Dump written to $DumpFile"
