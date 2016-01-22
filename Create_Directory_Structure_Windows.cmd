set str=%~f0
echo.%str%
set str=%str:Create_Directory_Structure_Windows.cmd=%
md "%str%\events"
md "%str%\fifos"
md "%str%\ground_errors"
md "%str%\housekeeping"
md "%str%\housekeeping\logs"
md "%str%\image_data"
md "%str%\memory"
md "%str%\memory\dumps"
md "%str%\memory\load"
md "%str%\memory\checks"
md "%str%\payload_data"
md "%str%\scheduling"
md "%str%\scheduling\new"
md "%str%\telemetry"