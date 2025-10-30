@echo off
title Darky - Your CMD AI
color 0a
setlocal enabledelayedexpansion

if not exist brain.txt (
  echo hello=Hey there! I'm Darky, your CMD AI.>>brain.txt
  echo how are you=I'm doing great! How about you?>>brain.txt
  echo who are you=I'm Darky, a simple AI made by you!>>brain.txt
)

echo =====================================
echo       WELCOME! I AM DARKY 🤖
echo =====================================
echo Type anything to chat with me.
echo Type "exit" to quit.
echo =====================================
echo.

:chat
set /p user=You: 
if /i "%user%"=="exit" goto bye

set found=false
for /f "tokens=1,* delims==" %%a in (brain.txt) do (
  if /i "%%a"=="%user%" (
    echo Darky: %%b
    set found=true
  )
)

if "%found%"=="false" (
  echo Darky: Hmm... I don’t know that yet.
  echo What should I reply when you say that?
  set /p ans=You teach Darky: 
  echo %user%=%ans%>>brain.txt
  echo Darky: Got it! I’ll remember that next time. 😄
)
goto chat

:bye
echo Darky: Bye! Have an awesome day! ⚡
pause
exit
