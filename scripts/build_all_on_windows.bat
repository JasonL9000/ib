@echo off
set sources[0]="cfgs\win_debug"
set sources[1]="cfgs\win_release"

for /L %%a in (0,1) do call ib --cfg %%sources[%%a]%% examples\win_hello.exe %*
