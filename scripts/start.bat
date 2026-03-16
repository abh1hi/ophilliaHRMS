@echo off
setlocal
REM Usage: start.bat [profiles...]
REM Default: core hr
REM Examples:
REM   start.bat              -> starts gateway + auth + db + redis + rabbitmq + hr services
REM   start.bat core         -> starts gateway + auth + db + redis + rabbitmq only
REM   start.bat core payroll -> core + payroll module

SET PROFILES=%*
IF "%PROFILES%"=="" SET PROFILES=core hr

SET PROFILE_ARGS=
FOR %%p IN (%PROFILES%) DO SET PROFILE_ARGS=%PROFILE_ARGS% --profile %%p

echo Starting HRMS with profiles: %PROFILES%
docker compose %PROFILE_ARGS% up --build -d
echo.
echo Gateway: http://localhost/health
