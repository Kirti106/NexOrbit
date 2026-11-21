param(
    [string]$DumpFile = ".\nexorbit.dump"
)
$ErrorActionPreference = "Stop"

if (-not (Test-Path $DumpFile)) {
    throw "Dump file not found: $DumpFile"
}
$resolved = (Resolve-Path $DumpFile).Path
docker cp $resolved nexorbit_db:/tmp/nexorbit.restore.dump
docker exec nexorbit_db pg_restore -U root -d nexorbit --clean --if-exists /tmp/nexorbit.restore.dump
